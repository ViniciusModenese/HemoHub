from decimal import Decimal
from django.test import TestCase
from usuarios.models import Usuario
from hemocentros.models import Hemocentro
from necessidades.models import NecessidadeSanguinea

class NecessidadeSanguineaTests(TestCase):
    def setUp(self):
        self.user_hemo = Usuario.objects.create_user(
            username='hemo_nec',
            email='hemo_nec@email.com',
            password='senha',
            tipo_usuario=Usuario.TipoUsuario.HEMOCENTRO
        )
        self.hemocentro = Hemocentro.objects.create(
            usuario=self.user_hemo,
            nome='Hemocentro Urgencia',
            cnpj='11.222.333/0001-99',
            logradouro='Rua A',
            numero='1',
            bairro='Centro',
            cidade='São Paulo',
            estado='SP',
            cep='01001-000',
            latitude=Decimal('-23.550520'),
            longitude=Decimal('-46.633308')
        )

    def test_criacao_necessidade_critica(self):
        nec = NecessidadeSanguinea.objects.create(
            hemocentro=self.hemocentro,
            tipo_sanguineo='O-',
            nivel_urgencia=NecessidadeSanguinea.NivelUrgencia.CRITICA
        )
        self.assertTrue(nec.ativa)
        self.assertIn('O-', str(nec))

