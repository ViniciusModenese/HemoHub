import random
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from doadores.models import Doador
from usuarios.models import Usuario

SENHA_PADRAO = 'HemoHub2026!'

NOMES_M = [
    'João', 'Pedro', 'Lucas', 'Gabriel', 'Matheus', 'Rafael', 'Bruno', 'Carlos', 'Felipe', 'Gustavo',
    'Rodrigo', 'Marcelo', 'André', 'Diego', 'Eduardo', 'Fábio', 'Ricardo', 'Thiago', 'Vinícius', 'Leandro',
    'Alexandre', 'Daniel', 'Fernando', 'Henrique', 'Igor', 'José', 'Luiz', 'Marcos', 'Paulo', 'Renato',
]
NOMES_F = [
    'Maria', 'Ana', 'Juliana', 'Fernanda', 'Patrícia', 'Camila', 'Beatriz', 'Larissa', 'Amanda', 'Bruna',
    'Carla', 'Débora', 'Elaine', 'Gabriela', 'Isabela', 'Jéssica', 'Karina', 'Luciana', 'Mariana', 'Natália',
    'Priscila', 'Renata', 'Sandra', 'Tatiane', 'Vanessa', 'Aline', 'Cristina', 'Daniela', 'Eduarda', 'Flávia',
]
SOBRENOMES = [
    'Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves', 'Pereira', 'Lima', 'Gomes',
    'Costa', 'Ribeiro', 'Martins', 'Carvalho', 'Almeida', 'Lopes', 'Soares', 'Fernandes', 'Vieira', 'Barbosa',
    'Rocha', 'Dias', 'Monteiro', 'Cardoso', 'Reis', 'Araújo', 'Castro', 'Andrade', 'Nascimento', 'Moreira',
]
NOMES_RUA = [
    'Rua das Flores', 'Rua XV de Novembro', 'Avenida Brasil', 'Rua Sete de Setembro', 'Rua José Bonifácio',
    'Avenida Paulista', 'Rua Rio Branco', 'Rua Tiradentes', 'Avenida Getúlio Vargas', 'Rua São Paulo',
    'Rua das Palmeiras', 'Rua Barão do Rio Branco', 'Avenida Independência', 'Rua Marechal Deodoro',
    'Rua Duque de Caxias', 'Avenida das Nações', 'Rua Santos Dumont', 'Rua Doutor Eduardo', 'Rua Piratininga',
    'Avenida dos Bandeirantes',
]

TIPOS_SANGUINEOS_PESOS = [
    ('O+', 36), ('A+', 34), ('B+', 8), ('AB+', 2.5),
    ('O-', 9), ('A-', 8), ('B-', 2), ('AB-', 0.5),
]

HUBS = [
    {'cidade': 'São Paulo', 'bairro': 'Sé', 'ddd': '11', 'lat': -23.5505, 'lon': -46.6333},
    {'cidade': 'São Paulo', 'bairro': 'Pinheiros', 'ddd': '11', 'lat': -23.5629, 'lon': -46.6821},
    {'cidade': 'São Paulo', 'bairro': 'Moema', 'ddd': '11', 'lat': -23.5975, 'lon': -46.6660},
    {'cidade': 'São Paulo', 'bairro': 'Santo Amaro', 'ddd': '11', 'lat': -23.6560, 'lon': -46.7100},
    {'cidade': 'São Paulo', 'bairro': 'Tatuapé', 'ddd': '11', 'lat': -23.5400, 'lon': -46.5766},
    {'cidade': 'São Paulo', 'bairro': 'Itaquera', 'ddd': '11', 'lat': -23.5340, 'lon': -46.4550},
    {'cidade': 'São Paulo', 'bairro': 'Santana', 'ddd': '11', 'lat': -23.5010, 'lon': -46.6250},
    {'cidade': 'São Paulo', 'bairro': 'Vila Mariana', 'ddd': '11', 'lat': -23.5890, 'lon': -46.6350},
    {'cidade': 'São Paulo', 'bairro': 'Butantã', 'ddd': '11', 'lat': -23.5710, 'lon': -46.7080},
    {'cidade': 'São Paulo', 'bairro': 'Campo Limpo', 'ddd': '11', 'lat': -23.6440, 'lon': -46.7590},
    {'cidade': 'Guarulhos', 'bairro': 'Centro', 'ddd': '11', 'lat': -23.4633, 'lon': -46.5333},
    {'cidade': 'Osasco', 'bairro': 'Centro', 'ddd': '11', 'lat': -23.5320, 'lon': -46.7920},
    {'cidade': 'Barueri', 'bairro': 'Centro', 'ddd': '11', 'lat': -23.5106, 'lon': -46.8761},
    {'cidade': 'Santo André', 'bairro': 'Centro', 'ddd': '11', 'lat': -23.6639, 'lon': -46.5383},
    {'cidade': 'São Bernardo do Campo', 'bairro': 'Centro', 'ddd': '11', 'lat': -23.6944, 'lon': -46.5654},
    {'cidade': 'São Caetano do Sul', 'bairro': 'Centro', 'ddd': '11', 'lat': -23.6229, 'lon': -46.5546},
    {'cidade': 'Mogi das Cruzes', 'bairro': 'Centro', 'ddd': '11', 'lat': -23.5225, 'lon': -46.1883},
    {'cidade': 'Campinas', 'bairro': 'Centro', 'ddd': '19', 'lat': -22.9056, 'lon': -47.0608},
    {'cidade': 'Jundiaí', 'bairro': 'Centro', 'ddd': '11', 'lat': -23.1857, 'lon': -46.8978},
    {'cidade': 'Piracicaba', 'bairro': 'Centro', 'ddd': '19', 'lat': -22.7253, 'lon': -47.6492},
    {'cidade': 'Sorocaba', 'bairro': 'Centro', 'ddd': '15', 'lat': -23.5015, 'lon': -47.4526},
    {'cidade': 'Santos', 'bairro': 'Centro', 'ddd': '13', 'lat': -23.9608, 'lon': -46.3336},
    {'cidade': 'São José dos Campos', 'bairro': 'Centro', 'ddd': '12', 'lat': -23.1791, 'lon': -45.8872},
    {'cidade': 'Taubaté', 'bairro': 'Centro', 'ddd': '12', 'lat': -23.0264, 'lon': -45.5553},
    {'cidade': 'Ribeirão Preto', 'bairro': 'Centro', 'ddd': '16', 'lat': -21.1775, 'lon': -47.8103},
    {'cidade': 'São José do Rio Preto', 'bairro': 'Centro', 'ddd': '17', 'lat': -20.8197, 'lon': -49.3794},
    {'cidade': 'Bauru', 'bairro': 'Centro', 'ddd': '14', 'lat': -22.3147, 'lon': -49.0606},
    {'cidade': 'Botucatu', 'bairro': 'Centro', 'ddd': '14', 'lat': -22.8858, 'lon': -48.4450},
    {'cidade': 'Marília', 'bairro': 'Centro', 'ddd': '14', 'lat': -22.2139, 'lon': -49.9458},
    {'cidade': 'Presidente Prudente', 'bairro': 'Centro', 'ddd': '18', 'lat': -22.1256, 'lon': -51.3889},
    {'cidade': 'Araraquara', 'bairro': 'Centro', 'ddd': '16', 'lat': -21.7944, 'lon': -48.1756},
    {'cidade': 'Franca', 'bairro': 'Centro', 'ddd': '16', 'lat': -20.5386, 'lon': -47.4008},
]


def sortear_tipo_sanguineo():
    tipos, pesos = zip(*TIPOS_SANGUINEOS_PESOS)
    return random.choices(tipos, weights=pesos, k=1)[0]


def gerar_username_unico(indice):
    base = f'doador_{indice:04d}'
    username = base
    contador = 2
    while Usuario.objects.filter(username=username).exists():
        username = f'{base}_{contador}'
        contador += 1
    return username


def gerar_cpf_unico():
    while True:
        digitos = [str(random.randint(0, 9)) for _ in range(11)]
        cpf = f'{"".join(digitos[0:3])}.{"".join(digitos[3:6])}.{"".join(digitos[6:9])}-{"".join(digitos[9:11])}'
        if not Doador.objects.filter(cpf=cpf).exists():
            return cpf


def gerar_data_nascimento():
    hoje = timezone.now().date()
    idade_dias = random.randint(16 * 365, 74 * 365)
    return hoje - timedelta(days=idade_dias)


class Command(BaseCommand):
    help = 'Cria doadores fictícios espalhados pelo estado de São Paulo, sem geocodificar via API (rápido).'

    def add_arguments(self, parser):
        parser.add_argument('--quantidade', type=int, default=300)

    def handle(self, *args, **opcoes):
        quantidade = opcoes['quantidade']
        criados = 0

        with transaction.atomic():
            for indice in range(1, quantidade + 1):
                sexo = random.choice(['M', 'F'])
                primeiro_nome = random.choice(NOMES_M if sexo == 'M' else NOMES_F)
                nome_completo = f'{primeiro_nome} {random.choice(SOBRENOMES)} {random.choice(SOBRENOMES)}'

                hub = random.choice(HUBS)
                latitude = hub['lat'] + random.uniform(-0.035, 0.035)
                longitude = hub['lon'] + random.uniform(-0.035, 0.035)

                username = gerar_username_unico(indice)
                usuario = Usuario.objects.create_user(
                    username=username,
                    email=f'{username}@doadores.hemohub.local',
                    password=SENHA_PADRAO,
                    tipo_usuario=Usuario.TipoUsuario.DOADOR,
                )

                esta_gestante = sexo == 'F' and random.random() < 0.05

                Doador.objects.create(
                    usuario=usuario,
                    nome_completo=nome_completo,
                    cpf=gerar_cpf_unico(),
                    data_nascimento=gerar_data_nascimento(),
                    sexo=sexo,
                    peso=round(random.uniform(48, 105), 1),
                    tipo_sanguineo=sortear_tipo_sanguineo(),
                    telefone=f"({hub['ddd']}) 9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}",
                    esta_gestante=esta_gestante,
                    logradouro=random.choice(NOMES_RUA),
                    numero=str(random.randint(10, 2500)),
                    bairro=hub['bairro'],
                    cidade=hub['cidade'],
                    estado='SP',
                    cep=f'{random.randint(1000, 19999):05d}-{random.randint(0, 999):03d}',
                    latitude=latitude,
                    longitude=longitude,
                )
                criados += 1

        self.stdout.write(self.style.SUCCESS(f'Concluído. {criados} doadores criados.'))
