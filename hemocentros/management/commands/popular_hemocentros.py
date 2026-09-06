import json
import re
import time
import unicodedata

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from hemocentros.models import FotoHemocentro, Hemocentro
from usuarios.models import Usuario

CAMINHO_PADRAO = settings.BASE_DIR / 'hemocentros' / 'dados_semente' / 'hemocentros_sp.json'
SENHA_PADRAO = 'HemoHub2026!'
INTERVALO_ENTRE_GEOCODIFICACOES_SEGUNDOS = 1.1


def gerar_slug(texto):
    texto_normalizado = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    texto_normalizado = texto_normalizado.lower()
    texto_normalizado = re.sub(r'[^a-z0-9]+', '_', texto_normalizado).strip('_')
    return texto_normalizado[:30] or 'hemocentro'


def gerar_username_unico(nome):
    base = gerar_slug(nome)
    username = base
    contador = 2
    while Usuario.objects.filter(username=username).exists():
        username = f'{base}_{contador}'
        contador += 1
    return username


class Command(BaseCommand):
    help = 'Popula o banco com hemocentros reais de São Paulo a partir de um arquivo JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--arquivo', type=str, default=str(CAMINHO_PADRAO))
        parser.add_argument('--sem-fotos', action='store_true', help='Não baixa/anexa fotos mesmo se a URL estiver presente.')

    def handle(self, *args, **opcoes):
        caminho = opcoes['arquivo']
        baixar_fotos = not opcoes['sem_fotos']

        with open(caminho, encoding='utf-8') as arquivo:
            registros = json.load(arquivo)

        criados = 0
        ignorados = 0

        for registro in registros:
            nome = registro.get('nome', '').strip()
            if not nome:
                continue

            if Hemocentro.objects.filter(nome=nome).exists():
                ignorados += 1
                self.stdout.write(f'Já existe, pulando: {nome}')
                continue

            with transaction.atomic():
                username = gerar_username_unico(nome)
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=f'{username}@hemocentros.hemohub.local',
                    password=SENHA_PADRAO,
                    tipo_usuario=Usuario.TipoUsuario.HEMOCENTRO,
                )
                hemocentro = Hemocentro.objects.create(
                    usuario=usuario,
                    nome=nome,
                    descricao=registro.get('descricao', ''),
                    telefone=registro.get('telefone', ''),
                    horario_funcionamento=registro.get('horario_funcionamento') or 'Consulte o hemocentro para o horário de funcionamento atualizado.',
                    logradouro=registro.get('logradouro', ''),
                    numero=registro.get('numero', 'S/N'),
                    bairro=registro.get('bairro', ''),
                    cidade=registro.get('cidade', ''),
                    estado='SP',
                    cep=registro.get('cep', ''),
                )

            if hemocentro.latitude is None:
                self.stdout.write(self.style.WARNING(f'Não geocodificado: {nome}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'Criado: {nome} ({hemocentro.latitude}, {hemocentro.longitude})'))

            url_imagem = registro.get('imagem_wikimedia_url')
            if baixar_fotos and url_imagem:
                self._anexar_foto(hemocentro, url_imagem)

            criados += 1
            time.sleep(INTERVALO_ENTRE_GEOCODIFICACOES_SEGUNDOS)

        self.stdout.write(self.style.SUCCESS(f'\nConcluído. Criados: {criados}. Ignorados (já existiam): {ignorados}.'))

    def _anexar_foto(self, hemocentro, url_imagem):
        try:
            resposta = requests.get(url_imagem, timeout=15, headers={'User-Agent': 'HemoHub/1.0 (uso local)'})
            resposta.raise_for_status()
            extensao = url_imagem.split('.')[-1].split('?')[0].lower()
            if extensao not in ('jpg', 'jpeg', 'png', 'webp'):
                extensao = 'jpg'
            nome_arquivo = f'{gerar_slug(hemocentro.nome)}.{extensao}'
            FotoHemocentro.objects.create(
                hemocentro=hemocentro,
                imagem=ContentFile(resposta.content, name=nome_arquivo),
                legenda='Foto real (Wikimedia Commons)',
            )
            return True
        except (requests.RequestException, OSError) as erro:
            self.stdout.write(self.style.WARNING(f'Falha ao baixar foto de {hemocentro.nome}: {erro}'))
            return False
