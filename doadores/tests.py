from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import Usuario
from hemocentros.models import Hemocentro
from doadores.models import Doador, Agendamento

class DoadorModelTests(TestCase):
    def setUp(self):
        self.user_doador = Usuario.objects.create_user(
            username='joao_teste',
            email='joao_teste@email.com',
            password='senha123',
            tipo_usuario=Usuario.TipoUsuario.DOADOR
        )
        self.doador = Doador.objects.create(
            usuario=self.user_doador,
            nome_completo='João Teste Silva',
            cpf='111.222.333-44',
            data_nascimento=date(1995, 5, 10),
            sexo='M',
            peso=Decimal('72.5'),
            tipo_sanguineo='O+',
            logradouro='Rua Teste',
            numero='100',
            bairro='Centro',
            cidade='São Paulo',
            estado='SP',
            cep='01001-000',
            latitude=Decimal('-23.550520'),
            longitude=Decimal('-46.633308')
        )
        self.user_hemo = Usuario.objects.create_user(
            username='hemo_teste',
            email='hemo@email.com',
            password='senha123',
            tipo_usuario=Usuario.TipoUsuario.HEMOCENTRO
        )
        self.hemocentro = Hemocentro.objects.create(
            usuario=self.user_hemo,
            nome='Hemocentro Teste',
            cnpj='11.222.333/0001-44',
            logradouro='Av Teste',
            numero='200',
            bairro='Bela Vista',
            cidade='São Paulo',
            estado='SP',
            cep='01310-000',
            latitude=Decimal('-23.560520'),
            longitude=Decimal('-46.643308')
        )

    def test_doador_criado_esta_apto(self):
        apto, motivos = self.doador.apto_para_doar()
        self.assertTrue(apto)
        self.assertEqual(len(motivos), 0)
        self.assertEqual(self.doador.sexo, 'M')

    def test_agendamento_criacao(self):
        agendamento = Agendamento.objects.create(
            doador=self.doador,
            hemocentro=self.hemocentro,
            data=date.today() + timedelta(days=2),
            horario='10:30'
        )
        self.assertEqual(agendamento.status, Agendamento.Status.CONFIRMADO)
        self.assertEqual(self.doador.agendamentos.count(), 1)

    def test_painel_doador_autenticado(self):
        client = Client()
        client.force_login(self.user_doador)
        resp = client.get(reverse('doadores:painel'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'João Teste Silva')

