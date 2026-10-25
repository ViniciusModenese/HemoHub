import math

import requests

CABECALHOS_NOMINATIM = {'User-Agent': 'HemoHub/1.0 (uso local, sem fins comerciais)'}

TIPOS_SANGUINEOS = [
    ('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'),
    ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'),
]

DOADORES_COMPATIVEIS = {
    'A+': ['A+', 'A-', 'O+', 'O-'],
    'A-': ['A-', 'O-'],
    'B+': ['B+', 'B-', 'O+', 'O-'],
    'B-': ['B-', 'O-'],
    'AB+': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
    'AB-': ['A-', 'B-', 'AB-', 'O-'],
    'O+': ['O+', 'O-'],
    'O-': ['O-'],
}


def obter_coordenadas(endereco):
    try:
        resposta = requests.get(
            'https://nominatim.openstreetmap.org/search',
            params={'q': endereco, 'format': 'json', 'limit': 1},
            headers=CABECALHOS_NOMINATIM,
            timeout=10,
        )
        resposta.raise_for_status()
        dados = resposta.json()
        if dados:
            return float(dados[0]['lat']), float(dados[0]['lon'])
    except (requests.RequestException, ValueError, KeyError, IndexError):
        pass
    return None, None


def obter_coordenadas_endereco(logradouro, numero, bairro, cidade, estado):
    tentativas = [
        f'{logradouro}, {numero}, {bairro}, {cidade}, {estado}, Brasil',
        f'{logradouro}, {numero}, {cidade}, {estado}, Brasil',
        f'{logradouro}, {cidade}, {estado}, Brasil',
        f'{cidade}, {estado}, Brasil',
    ]
    for tentativa in tentativas:
        latitude, longitude = obter_coordenadas(tentativa)
        if latitude is not None:
            return latitude, longitude
    return None, None


def calcular_distancia_km(latitude1, longitude1, latitude2, longitude2):
    raio_terra_km = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [latitude1, longitude1, latitude2, longitude2])
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    return raio_terra_km * c


def _so_digitos(valor):
    return ''.join(caractere for caractere in (valor or '') if caractere.isdigit())


def _digito_verificador(digitos, pesos):
    soma = sum(int(digito) * peso for digito, peso in zip(digitos, pesos))
    resto = soma % 11
    return '0' if resto < 2 else str(11 - resto)


def normalizar_cpf(valor):
    digitos = _so_digitos(valor)
    if len(digitos) != 11 or digitos == digitos[0] * 11:
        return None
    primeiro = _digito_verificador(digitos[:9], range(10, 1, -1))
    segundo = _digito_verificador(digitos[:10], range(11, 1, -1))
    if digitos[9:] != primeiro + segundo:
        return None
    return f'{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}'


def normalizar_cnpj(valor):
    digitos = _so_digitos(valor)
    if len(digitos) != 14 or digitos == digitos[0] * 14:
        return None
    primeiro = _digito_verificador(digitos[:12], [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    segundo = _digito_verificador(digitos[:13], [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    if digitos[12:] != primeiro + segundo:
        return None
    return f'{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}'
