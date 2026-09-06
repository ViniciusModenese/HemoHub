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
