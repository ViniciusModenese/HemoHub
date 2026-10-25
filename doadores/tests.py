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

    def _agendar(self, data):
        client = Client()
        client.force_login(self.user_doador)
        resp = client.post(
            reverse('doadores:criar_agendamento', args=[self.hemocentro.id]),
            {'data': data.isoformat(), 'horario': '09:00', 'aceite_requisitos': 'on'},
        )
        return resp

    def test_agendamento_apto_e_criado(self):
        self._agendar(date.today() + timedelta(days=5))
        self.assertEqual(self.doador.agendamentos.count(), 1)

    def test_agendamento_bloqueado_dentro_do_intervalo(self):
        from doadores.models import HistoricoDoacao
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=10))
        self._agendar(date.today() + timedelta(days=5))
        self.assertEqual(self.doador.agendamentos.count(), 0)

    def test_agendamento_permitido_apos_o_intervalo(self):
        from doadores.models import HistoricoDoacao
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=10))
        self._agendar(date.today() + timedelta(days=60))
        self.assertEqual(self.doador.agendamentos.count(), 1)

    def test_agendamento_bloqueado_para_doador_inapto_sem_data_prevista(self):
        self.doador.peso = Decimal('45.0')
        self.doador.save()
        self._agendar(date.today() + timedelta(days=5))
        self.assertEqual(self.doador.agendamentos.count(), 0)

    def _doador_com_idade(self, anos):
        hoje = date.today()
        self.doador.data_nascimento = date(hoje.year - anos, 1, 1)
        self.doador.save()

    def test_api_do_mapa_informa_agendamento_ativo(self):
        client = Client()
        client.force_login(self.user_doador)
        url = reverse('doadores:dados_agendamento_hemocentro', args=[self.hemocentro.id])
        self.assertNotIn('agendamento_ativo', client.get(url).json())
        self._agendar(date.today() + timedelta(days=5))
        self.assertEqual(client.get(url).json()['agendamento_ativo']['hemocentro'], 'Hemocentro Teste')

    def test_fluxo_do_mapa_aplica_a_regra_de_aptidao(self):
        from doadores.models import HistoricoDoacao
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=10))
        client = Client()
        client.force_login(self.user_doador)
        resp = client.post(
            reverse('doadores:criar_agendamento', args=[self.hemocentro.id]),
            {'data': (date.today() + timedelta(days=5)).isoformat(), 'horario': '09:00', 'ajax': 'true', 'aceite_requisitos': 'on'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(resp.status_code, 400)
        self.assertFalse(resp.json()['sucesso'])
        self.assertEqual(self.doador.agendamentos.count(), 0)

    def test_agendamento_sem_aceite_dos_requisitos_e_bloqueado(self):
        client = Client()
        client.force_login(self.user_doador)
        client.post(
            reverse('doadores:criar_agendamento', args=[self.hemocentro.id]),
            {'data': (date.today() + timedelta(days=5)).isoformat(), 'horario': '09:00'},
        )
        self.assertEqual(self.doador.agendamentos.count(), 0)

    def test_nao_cancela_agendamento_ja_concluido(self):
        self._agendar(date.today() + timedelta(days=5))
        agendamento = self.doador.agendamentos.get()
        agendamento.status = Agendamento.Status.CONCLUIDO
        agendamento.save()
        client = Client()
        client.force_login(self.user_doador)
        client.post(reverse('doadores:cancelar_agendamento', args=[agendamento.pk]))
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.CONCLUIDO)

    def test_horario_fora_da_grade_ou_mal_formatado_e_recusado(self):
        client = Client()
        client.force_login(self.user_doador)
        url = reverse('doadores:criar_agendamento', args=[self.hemocentro.id])
        dia = (date.today() + timedelta(days=5)).isoformat()
        for horario in ['9:00', 'abc', '03:00', '25:99', '12:00:00', '09:00 ']:
            client.post(url, {'data': dia, 'horario': horario, 'aceite_requisitos': 'on'})
            self.assertEqual(self.doador.agendamentos.count(), 0, horario)
        client.post(url, {'data': dia, 'horario': '09:00', 'aceite_requisitos': 'on'})
        self.assertEqual(self.doador.agendamentos.count(), 1)

    def test_horario_sem_zero_nao_burla_a_regra_de_horario_passado(self):
        client = Client()
        client.force_login(self.user_doador)
        client.post(
            reverse('doadores:criar_agendamento', args=[self.hemocentro.id]),
            {'data': date.today().isoformat(), 'horario': '9:00', 'aceite_requisitos': 'on'},
        )
        self.assertEqual(self.doador.agendamentos.count(), 0)

    def test_idade_minima_16_anos(self):
        self._doador_com_idade(15)
        self.assertFalse(self.doador.apto_para_doar()[0])
        self._doador_com_idade(16)
        self.assertTrue(self.doador.apto_para_doar()[0])

    def test_entre_60_e_69_so_quem_ja_doou_antes_dos_60(self):
        from doadores.models import HistoricoDoacao
        self._doador_com_idade(65)
        self.assertFalse(self.doador.apto_para_doar()[0])
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=200))
        self.assertFalse(self.doador.apto_para_doar()[0])
        HistoricoDoacao.objects.create(
            doador=self.doador, data_doacao=date(date.today().year - 6, 6, 1),
        )
        self.assertTrue(self.doador.apto_para_doar()[0])

    def test_acima_de_70_so_doador_regular(self):
        from doadores.models import HistoricoDoacao
        self._doador_com_idade(72)
        apto, motivos = self.doador.apto_para_doar()
        self.assertFalse(apto)
        self.assertIn('regulares', motivos[0])
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=200))
        self.assertFalse(self.doador.apto_para_doar()[0])
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=400))
        self.assertTrue(self.doador.apto_para_doar()[0])

    def test_doacoes_antigas_nao_tornam_regular_o_doador_acima_de_70(self):
        from doadores.models import HistoricoDoacao
        self._doador_com_idade(72)
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=900))
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=1000))
        self.assertFalse(self.doador.apto_para_doar()[0])

    def test_banco_impede_dois_agendamentos_confirmados_do_mesmo_doador(self):
        from django.db import IntegrityError, transaction
        Agendamento.objects.create(
            doador=self.doador, hemocentro=self.hemocentro,
            data=date.today() + timedelta(days=3), horario='09:00',
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            Agendamento.objects.create(
                doador=self.doador, hemocentro=self.hemocentro,
                data=date.today() + timedelta(days=9), horario='10:00',
            )
        Agendamento.objects.create(
            doador=self.doador, hemocentro=self.hemocentro,
            data=date.today() + timedelta(days=9), horario='10:00',
            status=Agendamento.Status.CANCELADO,
        )
        self.assertEqual(self.doador.agendamentos.count(), 2)

    def test_segundo_agendamento_ativo_e_bloqueado(self):
        self._agendar(date.today() + timedelta(days=5))
        self._agendar(date.today() + timedelta(days=200))
        self.assertEqual(self.doador.agendamentos.count(), 1)

    def test_novo_agendamento_permitido_apos_cancelar(self):
        self._agendar(date.today() + timedelta(days=5))
        primeiro = self.doador.agendamentos.get()
        primeiro.status = Agendamento.Status.CANCELADO
        primeiro.save()
        self._agendar(date.today() + timedelta(days=6))
        self.assertEqual(self.doador.agendamentos.filter(status=Agendamento.Status.CONFIRMADO).count(), 1)
        self.assertEqual(self.doador.agendamentos.count(), 2)

    def test_agendamento_hoje_em_horario_passado_e_bloqueado(self):
        client = Client()
        client.force_login(self.user_doador)
        client.post(
            reverse('doadores:criar_agendamento', args=[self.hemocentro.id]),
            {'data': date.today().isoformat(), 'horario': '00:00'},
        )
        self.assertEqual(self.doador.agendamentos.count(), 0)

    def test_painel_doador_autenticado(self):
        client = Client()
        client.force_login(self.user_doador)
        resp = client.get(reverse('doadores:painel'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'João Teste Silva')



class CpfCadastroTests(TestCase):
    def _dados(self, cpf):
        return {
            'username': 'novo_doador', 'email': 'novo@email.com',
            'password1': 'SenhaForte!2026', 'password2': 'SenhaForte!2026',
            'nome_completo': 'Novo Doador', 'cpf': cpf,
            'data_nascimento': '1990-01-01', 'sexo': 'M', 'peso': '70.0',
            'tipo_sanguineo': 'O+', 'telefone': '',
            'logradouro': 'Rua A', 'numero': '1', 'bairro': 'Centro',
            'cidade': 'São Paulo', 'estado': 'SP', 'cep': '01001-000',
        }

    def test_cpf_invalido_e_recusado(self):
        from doadores.forms import FormularioCadastroDoador
        for cpf in ['123.456.789-00', '111.111.111-11', '123', 'abc']:
            formulario = FormularioCadastroDoador(self._dados(cpf))
            self.assertFalse(formulario.is_valid(), cpf)
            self.assertIn('cpf', formulario.errors)

    def test_cpf_valido_e_aceito_e_formatado(self):
        from doadores.forms import FormularioCadastroDoador
        formulario = FormularioCadastroDoador(self._dados('52998224725'))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.cleaned_data['cpf'], '529.982.247-25')

    def test_cpf_duplicado_com_formatacao_diferente_e_recusado(self):
        from doadores.forms import FormularioCadastroDoador
        usuario = Usuario.objects.create_user(
            username='existente', email='existente@email.com', password='x',
            tipo_usuario=Usuario.TipoUsuario.DOADOR,
        )
        Doador.objects.create(
            usuario=usuario, nome_completo='Existente', cpf='529.982.247-25',
            data_nascimento=date(1990, 1, 1), sexo='M', peso=Decimal('70.0'),
            tipo_sanguineo='O+', logradouro='Rua A', numero='1', bairro='Centro',
            cidade='São Paulo', estado='SP', cep='01001-000',
            latitude=Decimal('-23.55'), longitude=Decimal('-46.63'),
        )
        formulario = FormularioCadastroDoador(self._dados('52998224725'))
        self.assertFalse(formulario.is_valid())
        self.assertIn('cpf', formulario.errors)

    def test_cpf_ja_cadastrado_sem_pontuacao_e_detectado(self):
        from doadores.forms import FormularioCadastroDoador
        usuario = Usuario.objects.create_user(
            username='legado', email='legado@email.com', password='x',
            tipo_usuario=Usuario.TipoUsuario.DOADOR,
        )
        Doador.objects.create(
            usuario=usuario, nome_completo='Legado', cpf='52998224725',
            data_nascimento=date(1990, 1, 1), sexo='M', peso=Decimal('70.0'),
            tipo_sanguineo='O+', logradouro='Rua A', numero='1', bairro='Centro',
            cidade='São Paulo', estado='SP', cep='01001-000',
            latitude=Decimal('-23.55'), longitude=Decimal('-46.63'),
        )
        formulario = FormularioCadastroDoador(self._dados('529.982.247-25'))
        self.assertFalse(formulario.is_valid())
        self.assertIn('cpf', formulario.errors)
