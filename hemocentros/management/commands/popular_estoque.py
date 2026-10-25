import random

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from hemocentros.models import EstoqueSanguineo, Hemocentro
from hemoconecta.utilitarios import TIPOS_SANGUINEOS


class Command(BaseCommand):
    help = 'Preenche o estoque de sangue com quantidades aleatórias (dados de demonstração).'

    def add_arguments(self, parser):
        parser.add_argument('--hemocentro', default='colsan_jundiai', help='Usuário do hemocentro (padrão: colsan_jundiai).')
        parser.add_argument('--todos', action='store_true', help='Preenche o estoque de todos os hemocentros.')
        parser.add_argument('--forcar', action='store_true', help='Permite rodar com DEBUG desligado (substitui o estoque real).')

    def handle(self, *args, **opcoes):
        if not settings.DEBUG and not opcoes['forcar']:
            raise CommandError(
                'Este comando substitui o estoque por números aleatórios e só roda com DEBUG ligado. '
                'Use --forcar se tiver certeza.'
            )
        if opcoes['todos']:
            hemocentros = Hemocentro.objects.all()
        else:
            hemocentros = Hemocentro.objects.filter(usuario__username=opcoes['hemocentro'])
            if not hemocentros.exists():
                raise CommandError(f'Hemocentro "{opcoes["hemocentro"]}" não encontrado.')

        for hemocentro in hemocentros:
            resumo = []
            for tipo, _ in TIPOS_SANGUINEOS:
                quantidade = random.randint(0, 80)
                EstoqueSanguineo.objects.update_or_create(
                    hemocentro=hemocentro,
                    tipo_sanguineo=tipo,
                    defaults={'quantidade_bolsas': quantidade},
                )
                resumo.append(f'{tipo}={quantidade}')
            self.stdout.write(f'{hemocentro.nome}: ' + ', '.join(resumo))
