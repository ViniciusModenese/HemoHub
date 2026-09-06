from django.test import TestCase, Client
from django.urls import reverse
from hemoconecta.utilitarios import DOADORES_COMPATIVEIS
from paginas.views import PODE_DOAR_PARA

class PaginasViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_pagina_inicio_status_200(self):
        resp = self.client.get(reverse('paginas:inicio'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'HemoHub')

    def test_api_mapa_status_200_json(self):
        resp = self.client.get(reverse('paginas:dados_mapa'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/json')

    def test_compatibilidade_sanguinea(self):
        self.assertIn('O-', DOADORES_COMPATIVEIS['A+'])
        self.assertIn('O-', DOADORES_COMPATIVEIS['O-'])
        self.assertIn('AB+', PODE_DOAR_PARA['O-'])
        self.assertIn('A+', PODE_DOAR_PARA['O-'])

