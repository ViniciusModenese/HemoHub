from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import Usuario
from hemocentros.models import Hemocentro

class HemocentroModelTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_hemo = Usuario.objects.create_user(
            username='hemo_teste',
            email='hemo@email.com',
            password='senha123',
            tipo_usuario=Usuario.TipoUsuario.HEMOCENTRO
        )
        self.hemocentro = Hemocentro.objects.create(
            usuario=self.user_hemo,
            nome='Hemocentro Central',
            cnpj='12.345.678/0001-90',
            horario_funcionamento='Segunda a sexta das 08h às 17h',
            logradouro='Rua das Flores',
            numero='123',
            bairro='Centro',
            cidade='São Paulo',
            estado='SP',
            cep='01001-000',
            latitude=Decimal('-23.550520'),
            longitude=Decimal('-46.633308')
        )

    def test_criacao_hemocentro(self):
        self.assertEqual(str(self.hemocentro), 'Hemocentro Central')
        self.assertIn('Rua das Flores', self.hemocentro.endereco_completo)

    def test_painel_hemocentro_autenticado(self):
        self.client.force_login(self.user_hemo)
        resp = self.client.get(reverse('hemocentros:painel'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Hemocentro Central')

