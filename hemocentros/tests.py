from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import Usuario
from hemocentros.models import Hemocentro
from doadores.models import Agendamento, Doador, HistoricoDoacao

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



class BaseAgenda(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_hemo = Usuario.objects.create_user(
            username='hemo_agenda',
            email='hemo_agenda@email.com',
            password='senha123',
            tipo_usuario=Usuario.TipoUsuario.HEMOCENTRO
        )
        self.hemocentro = Hemocentro.objects.create(
            usuario=self.user_hemo,
            nome='Hemocentro Agenda',
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
        user_doador = Usuario.objects.create_user(
            username='doador_agenda',
            email='doador_agenda@email.com',
            password='senha123',
            tipo_usuario=Usuario.TipoUsuario.DOADOR
        )
        self.doador = Doador.objects.create(
            usuario=user_doador,
            nome_completo='Doador Agenda',
            cpf='999.888.777-66',
            data_nascimento=date(1990, 1, 1),
            sexo='M',
            peso=Decimal('75.0'),
            tipo_sanguineo='O+',
            logradouro='Rua Teste',
            numero='1',
            bairro='Centro',
            cidade='São Paulo',
            estado='SP',
            cep='01001-000',
            latitude=Decimal('-23.550520'),
            longitude=Decimal('-46.633308')
        )
        self.client.force_login(self.user_hemo)

    def _agendamento(self, dias, status=Agendamento.Status.CONFIRMADO):
        return Agendamento.objects.create(
            doador=self.doador,
            hemocentro=self.hemocentro,
            data=date.today() + timedelta(days=dias),
            horario='09:00',
            status=status,
        )

    def _acao(self, agendamento, acao):
        return self.client.post(
            reverse('hemocentros:atualizar_agendamento', args=[agendamento.pk]),
            {'acao': acao},
        )


class ConcluirAgendamentoTests(BaseAgenda):
    def test_concluir_agendamento_de_hoje_registra_historico(self):
        agendamento = self._agendamento(0)
        self._acao(agendamento, 'concluir')
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.CONCLUIDO)
        self.assertEqual(self.doador.historico.count(), 1)

    def test_concluir_agendamento_futuro_e_bloqueado(self):
        agendamento = self._agendamento(5)
        self._acao(agendamento, 'concluir')
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.CONFIRMADO)
        self.assertEqual(self.doador.historico.count(), 0)

    def test_concluir_duas_vezes_nao_duplica_historico(self):
        agendamento = self._agendamento(0)
        self._acao(agendamento, 'concluir')
        self._acao(agendamento, 'concluir')
        self.assertEqual(self.doador.historico.count(), 1)

    def test_agendamento_cancelado_nao_pode_ser_concluido(self):
        agendamento = self._agendamento(0)
        self._acao(agendamento, 'cancelar')
        self._acao(agendamento, 'concluir')
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.CANCELADO)
        self.assertEqual(self.doador.historico.count(), 0)

    def test_painel_mostra_pendentes_antes_dos_cancelados(self):
        cancelado = self._agendamento(-3)
        cancelado.status = Agendamento.Status.CANCELADO
        cancelado.save()
        pendente = self._agendamento(2)
        resp = self.client.get(reverse('hemocentros:painel'))
        lista = list(resp.context['agendamentos'])
        self.assertEqual(lista, [pendente, cancelado])

    def test_painel_agrupa_pendentes_concluidos_e_cancelados(self):
        cancelado = self._agendamento(3)
        cancelado.status = Agendamento.Status.CANCELADO
        cancelado.save()
        concluido = self._agendamento(0)
        concluido.status = Agendamento.Status.CONCLUIDO
        concluido.save()
        pendente = self._agendamento(5)
        resp = self.client.get(reverse('hemocentros:painel'))
        self.assertEqual(list(resp.context['agendamentos']), [pendente, concluido, cancelado])

    def _lista(self, **filtros):
        resp = self.client.get(reverse('hemocentros:painel'), filtros)
        self.assertEqual(resp.status_code, 200)
        return list(resp.context['agendamentos'])

    def _tres_agendamentos(self):
        concluido = self._agendamento(0, Agendamento.Status.CONCLUIDO)
        cancelado = self._agendamento(10, Agendamento.Status.CANCELADO)
        pendente = self._agendamento(5)
        return pendente, concluido, cancelado

    def test_filtro_por_status(self):
        pendente, concluido, cancelado = self._tres_agendamentos()
        self.assertEqual(self._lista(status='confirmado'), [pendente])
        self.assertEqual(self._lista(status='concluido'), [concluido])
        self.assertEqual(self._lista(status='cancelado'), [cancelado])

    def test_filtro_por_periodo(self):
        pendente, concluido, cancelado = self._tres_agendamentos()
        de = (date.today() + timedelta(days=3)).isoformat()
        ate = (date.today() + timedelta(days=7)).isoformat()
        self.assertEqual(self._lista(de=de, ate=ate), [pendente])
        self.assertEqual(self._lista(de=de), [pendente, cancelado])

    def test_filtro_combina_status_e_periodo(self):
        pendente, concluido, cancelado = self._tres_agendamentos()
        de = (date.today() + timedelta(days=3)).isoformat()
        self.assertEqual(self._lista(status='cancelado', de=de), [cancelado])
        self.assertEqual(self._lista(status='concluido', de=de), [])

    def test_filtro_com_valores_invalidos_e_ignorado(self):
        pendente, concluido, cancelado = self._tres_agendamentos()
        self.assertEqual(
            self._lista(status='qualquer', de='lixo', ate='31/02/2026'),
            [pendente, concluido, cancelado],
        )


class CnpjTests(TestCase):
    def _dados(self, cnpj):
        return {
            'username': 'novo_hemo', 'email': 'novo_hemo@email.com',
            'password1': 'SenhaForte!2026', 'password2': 'SenhaForte!2026',
            'nome': 'Novo Hemocentro', 'cnpj': cnpj,
            'horario_funcionamento': 'Segunda a sexta, 08h às 17h',
            'logradouro': 'Rua A', 'numero': '1', 'bairro': 'Centro',
            'cidade': 'São Paulo', 'estado': 'SP', 'cep': '01001-000',
        }

    def test_cnpj_invalido_e_recusado(self):
        from hemocentros.forms import FormularioCadastroHemocentro
        for cnpj in ['11.222.333/0001-99', '00.000.000/0000-00', '123']:
            formulario = FormularioCadastroHemocentro(self._dados(cnpj))
            self.assertFalse(formulario.is_valid(), cnpj)
            self.assertIn('cnpj', formulario.errors)

    def test_cnpj_valido_e_aceito_e_formatado(self):
        from hemocentros.forms import FormularioCadastroHemocentro
        formulario = FormularioCadastroHemocentro(self._dados('11222333000181'))
        self.assertTrue(formulario.is_valid(), formulario.errors)
        self.assertEqual(formulario.cleaned_data['cnpj'], '11.222.333/0001-81')

    def test_cnpj_em_branco_continua_permitido(self):
        from hemocentros.forms import FormularioCadastroHemocentro
        formulario = FormularioCadastroHemocentro(self._dados(''))
        self.assertTrue(formulario.is_valid(), formulario.errors)


class RegistrarDoacaoTests(BaseAgenda):
    def setUp(self):
        super().setUp()
        outro_usuario = Usuario.objects.create_user(
            username='outro_doador', email='outro@email.com', password='senha123',
            tipo_usuario=Usuario.TipoUsuario.DOADOR,
        )
        outro_hemo_usuario = Usuario.objects.create_user(
            username='outro_hemo', email='outro_hemo@email.com', password='senha123',
            tipo_usuario=Usuario.TipoUsuario.HEMOCENTRO,
        )
        self.outro_hemocentro = Hemocentro.objects.create(
            usuario=outro_hemo_usuario, nome='Outro Hemocentro',
            horario_funcionamento='08h às 17h', logradouro='Rua B', numero='2',
            bairro='Centro', cidade='São Paulo', estado='SP', cep='01001-000',
            latitude=Decimal('-23.55'), longitude=Decimal('-46.63'),
        )
        self.outro_doador = Doador.objects.create(
            usuario=outro_usuario, nome_completo='Doador De Outro Lugar', cpf='111.444.777-35',
            data_nascimento=date(1990, 1, 1), sexo='M', peso=Decimal('75.0'),
            tipo_sanguineo='A+', logradouro='Rua C', numero='3', bairro='Centro',
            cidade='São Paulo', estado='SP', cep='01001-000',
            latitude=Decimal('-23.55'), longitude=Decimal('-46.63'),
        )
        Agendamento.objects.create(
            doador=self.outro_doador, hemocentro=self.outro_hemocentro,
            data=date.today(), horario='10:00',
        )

    def _registrar(self, doador, data):
        return self.client.post(
            reverse('hemocentros:registrar_doacao'),
            {'doador_id': doador.pk, 'data_doacao': data.isoformat(), 'local': ''},
        )

    def test_busca_encontra_doadores_de_toda_a_rede_pelo_nome(self):
        resp = self.client.get(reverse('hemocentros:registrar_doacao'), {'q': 'Doador'})
        nomes = [d.nome_completo for d in resp.context['doadores_encontrados']]
        self.assertEqual(nomes, ['Doador Agenda', 'Doador De Outro Lugar'])

    def test_busca_pelo_nome_exige_ao_menos_3_letras(self):
        resp = self.client.get(reverse('hemocentros:registrar_doacao'), {'q': 'Do'})
        self.assertEqual(list(resp.context['doadores_encontrados']), [])

    def test_busca_pelo_cpf_com_ou_sem_pontuacao(self):
        for termo in ['111.444.777-35', '11144477735']:
            resp = self.client.get(reverse('hemocentros:registrar_doacao'), {'q': termo})
            self.assertEqual([d.pk for d in resp.context['doadores_encontrados']], [self.outro_doador.pk])

    def test_busca_nao_mostra_o_endereco_completo_do_doador(self):
        resp = self.client.get(reverse('hemocentros:registrar_doacao'), {'doador': self.outro_doador.pk})
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, 'Rua C, 3')

    def test_registra_doacao_de_doador_de_outro_hemocentro_e_cancela_o_agendamento_dele_la(self):
        agendamento_la = self.outro_doador.agendamentos.get()
        self._registrar(self.outro_doador, date.today())
        self.assertEqual(self.outro_doador.historico.count(), 1)
        agendamento_la.refresh_from_db()
        self.assertEqual(agendamento_la.status, Agendamento.Status.CANCELADO)
        self.assertEqual(
            self.outro_doador.agendamentos.filter(hemocentro=self.hemocentro, status=Agendamento.Status.CONCLUIDO).count(), 1,
        )

    def test_intervalo_vale_para_doacao_feita_em_outro_hemocentro(self):
        HistoricoDoacao.objects.create(
            doador=self.outro_doador, data_doacao=date.today() - timedelta(days=5), local='Outro Hemocentro',
        )
        self._registrar(self.outro_doador, date.today())
        self.assertEqual(self.outro_doador.historico.count(), 1)

    def test_registro_com_data_futura_e_recusado(self):
        self._agendamento(0)
        self._registrar(self.doador, date.today() + timedelta(days=3))
        self.assertEqual(self.doador.historico.count(), 0)

    def test_registro_dentro_do_intervalo_e_recusado(self):
        self._agendamento(0)
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=10))
        self._registrar(self.doador, date.today())
        self.assertEqual(self.doador.historico.count(), 1)

    def test_registro_fecha_o_agendamento_e_nao_duplica(self):
        agendamento = self._agendamento(0)
        self._registrar(self.doador, date.today())
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.CONCLUIDO)
        self.assertEqual(self.doador.historico.count(), 1)
        self._acao(agendamento, 'concluir')
        self.assertEqual(self.doador.historico.count(), 1)

    def test_concluir_volta_para_o_painel_com_o_filtro(self):
        agendamento = self._agendamento(0)
        resp = self.client.post(
            reverse('hemocentros:atualizar_agendamento', args=[agendamento.pk]),
            {'acao': 'concluir', 'voltar': 'status=confirmado&de=2026-01-01&x=lixo'},
        )
        self.assertEqual(resp.status_code, 302)
        self.assertIn('status=confirmado', resp.url)
        self.assertIn('de=2026-01-01', resp.url)
        self.assertNotIn('lixo', resp.url)

    def test_registro_um_dia_antes_do_agendamento_conclui_o_agendamento(self):
        agendamento = self._agendamento(1)
        self._registrar(self.doador, date.today())
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.CONCLUIDO)
        self.assertEqual(agendamento.data, date.today())
        self.assertEqual(self.doador.historico.count(), 1)
        self.assertEqual(self.doador.agendamentos.filter(status=Agendamento.Status.CONFIRMADO).count(), 0)

    def test_registro_sem_agendamento_pendente_aparece_na_agenda(self):
        concluido = self._agendamento(-90)
        concluido.status = Agendamento.Status.CONCLUIDO
        concluido.save()
        self._registrar(self.doador, date.today())
        novos = self.doador.agendamentos.filter(data=date.today(), status=Agendamento.Status.CONCLUIDO)
        self.assertEqual(novos.count(), 1)
        resp = self.client.get(reverse('hemocentros:painel'))
        self.assertIn(novos.get(), list(resp.context['agendamentos']))

    def test_registro_cancela_agendamento_em_outro_hemocentro_dentro_do_intervalo(self):
        self._agendamento(-90, Agendamento.Status.CONCLUIDO)
        em_outro_lugar = Agendamento.objects.create(
            doador=self.doador, hemocentro=self.outro_hemocentro,
            data=date.today() + timedelta(days=10), horario='09:00',
        )
        self._registrar(self.doador, date.today())
        em_outro_lugar.refresh_from_db()
        self.assertEqual(em_outro_lugar.status, Agendamento.Status.CANCELADO)

    def test_registro_mantem_agendamento_em_outro_hemocentro_depois_do_intervalo(self):
        self._agendamento(-90, Agendamento.Status.CONCLUIDO)
        mantido = Agendamento.objects.create(
            doador=self.doador, hemocentro=self.outro_hemocentro,
            data=date.today() + timedelta(days=120), horario='09:00',
        )
        self._registrar(self.doador, date.today())
        mantido.refresh_from_db()
        self.assertEqual(mantido.status, Agendamento.Status.CONFIRMADO)

    def test_concluir_e_recusado_se_ja_ha_doacao_no_intervalo(self):
        agendamento = self._agendamento(0)
        HistoricoDoacao.objects.create(doador=self.doador, data_doacao=date.today() - timedelta(days=1))
        self._acao(agendamento, 'concluir')
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.CONFIRMADO)
        self.assertEqual(self.doador.historico.count(), 1)


class EstoqueTests(BaseAgenda):
    def _dados(self, **alteracoes):
        dados = {f'tipo_{t}': 20 for t in ['Apos', 'Aneg', 'Bpos', 'Bneg', 'ABpos', 'ABneg', 'Opos', 'Oneg']}
        dados.update(alteracoes)
        return dados

    def test_niveis_do_estoque(self):
        from hemocentros.models import nivel_do_estoque
        self.assertEqual(nivel_do_estoque(0), 'critico')
        self.assertEqual(nivel_do_estoque(9), 'critico')
        self.assertEqual(nivel_do_estoque(10), 'baixo')
        self.assertEqual(nivel_do_estoque(24), 'baixo')
        self.assertEqual(nivel_do_estoque(25), 'normal')

    def test_painel_mostra_os_8_tipos_zerados_quando_nao_ha_registro(self):
        resp = self.client.get(reverse('hemocentros:painel'))
        estoque = resp.context['estoque']
        self.assertEqual([i['tipo'] for i in estoque], ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'])
        self.assertTrue(all(i['quantidade'] == 0 and i['nivel'] == 'critico' for i in estoque))
        self.assertNotContains(resp, 'Não informado')

    def test_atualizar_estoque_cria_e_depois_altera_os_registros(self):
        from hemocentros.models import EstoqueSanguineo
        url = reverse('hemocentros:atualizar_estoque')
        self.client.post(url, self._dados(tipo_Oneg=3))
        self.assertEqual(self.hemocentro.estoque.count(), 8)
        self.assertEqual(self.hemocentro.estoque.get(tipo_sanguineo='O-').quantidade_bolsas, 3)
        self.client.post(url, self._dados(tipo_Oneg=40))
        self.assertEqual(self.hemocentro.estoque.count(), 8)
        self.assertEqual(self.hemocentro.estoque.get(tipo_sanguineo='O-').quantidade_bolsas, 40)
        painel = self.client.get(reverse('hemocentros:painel')).context['estoque']
        self.assertEqual(next(i for i in painel if i['tipo'] == 'O-')['nivel'], 'normal')

    def test_quantidade_negativa_e_recusada(self):
        resp = self.client.post(reverse('hemocentros:atualizar_estoque'), self._dados(tipo_Apos=-5))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(self.hemocentro.estoque.count(), 0)

    def test_hemocentro_so_altera_o_proprio_estoque(self):
        outro = Hemocentro.objects.create(
            usuario=Usuario.objects.create_user(
                username='outro_estoque', email='oe@email.com', password='x',
                tipo_usuario=Usuario.TipoUsuario.HEMOCENTRO,
            ),
            nome='Outro', horario_funcionamento='08h às 17h', logradouro='Rua B', numero='2',
            bairro='Centro', cidade='São Paulo', estado='SP', cep='01001-000',
            latitude=Decimal('-23.55'), longitude=Decimal('-46.63'),
        )
        self.client.post(reverse('hemocentros:atualizar_estoque'), self._dados())
        self.assertEqual(self.hemocentro.estoque.count(), 8)
        self.assertEqual(outro.estoque.count(), 0)

    def test_doador_nao_acessa_a_tela_de_estoque(self):
        cliente = Client()
        cliente.force_login(self.doador.usuario)
        self.assertEqual(cliente.get(reverse('hemocentros:atualizar_estoque')).status_code, 404)

    def test_comando_popular_estoque(self):
        from django.core.management import call_command
        from io import StringIO
        call_command('popular_estoque', hemocentro='hemo_agenda', forcar=True, stdout=StringIO())
        self.assertEqual(self.hemocentro.estoque.count(), 8)
        self.assertTrue(all(0 <= e.quantidade_bolsas <= 80 for e in self.hemocentro.estoque.all()))

    def _estoque_o_pos(self, quantidade):
        from hemocentros.models import EstoqueSanguineo
        return EstoqueSanguineo.objects.create(
            hemocentro=self.hemocentro, tipo_sanguineo='O+', quantidade_bolsas=quantidade,
        )

    def _quantidade_o_pos(self):
        return self.hemocentro.estoque.get(tipo_sanguineo='O+').quantidade_bolsas

    def test_concluir_soma_uma_bolsa_do_tipo_do_doador(self):
        self._estoque_o_pos(20)
        self._acao(self._agendamento(0), 'concluir')
        self.assertEqual(self._quantidade_o_pos(), 21)

    def test_concluir_cria_o_tipo_com_uma_bolsa_quando_nao_havia_registro(self):
        self._acao(self._agendamento(0), 'concluir')
        self.assertEqual(self.hemocentro.estoque.count(), 1)
        self.assertEqual(self._quantidade_o_pos(), 1)

    def test_concluir_recusado_nao_altera_o_estoque(self):
        self._estoque_o_pos(20)
        self._acao(self._agendamento(5), 'concluir')
        self.assertEqual(self._quantidade_o_pos(), 20)

    def test_registrar_doacao_soma_uma_bolsa_e_nao_soma_de_novo_ao_concluir(self):
        self._estoque_o_pos(20)
        agendamento = self._agendamento(0)
        self.client.post(
            reverse('hemocentros:registrar_doacao'),
            {'doador_id': self.doador.pk, 'data_doacao': date.today().isoformat(), 'local': ''},
        )
        self.assertEqual(self._quantidade_o_pos(), 21)
        self._acao(agendamento, 'concluir')
        self.assertEqual(self._quantidade_o_pos(), 21)

    def test_estoque_de_outro_tipo_nao_muda(self):
        from hemocentros.models import EstoqueSanguineo
        self._estoque_o_pos(20)
        EstoqueSanguineo.objects.create(hemocentro=self.hemocentro, tipo_sanguineo='A+', quantidade_bolsas=30)
        self._acao(self._agendamento(0), 'concluir')
        self.assertEqual(self.hemocentro.estoque.get(tipo_sanguineo='A+').quantidade_bolsas, 30)


class AlertaDeEstoqueTests(BaseAgenda):
    def _estoque(self, tipo, quantidade):
        from hemocentros.models import EstoqueSanguineo
        return EstoqueSanguineo.objects.create(
            hemocentro=self.hemocentro, tipo_sanguineo=tipo, quantidade_bolsas=quantidade,
        )

    def _emitir(self, tipo):
        return self.client.post(reverse('hemocentros:emitir_alerta_estoque'), {'tipo': tipo})

    def _card(self, tipo):
        estoque = self.client.get(reverse('hemocentros:painel')).context['estoque']
        return next(i for i in estoque if i['tipo'] == tipo)

    def test_botao_aparece_so_nos_tipos_criticos(self):
        self._estoque('O+', 5)
        self._estoque('A+', 50)
        resp = self.client.get(reverse('hemocentros:painel'))
        html = resp.content.decode()
        self.assertIn('name="tipo" value="O+"', html)
        self.assertNotIn('name="tipo" value="A+"', html)
        self.assertContains(resp, 'Nenhum alerta emitido')

    def test_emitir_alerta_cria_necessidade_critica_e_notifica_doador_proximo(self):
        from django.core import mail
        from necessidades.models import NecessidadeSanguinea, NotificacaoDoador
        self._estoque('O+', 5)
        self._emitir('O+')
        necessidade = NecessidadeSanguinea.objects.get(hemocentro=self.hemocentro, tipo_sanguineo='O+')
        self.assertEqual(necessidade.nivel_urgencia, 'critica')
        self.assertTrue(necessidade.notificacao_enviada)
        self.assertEqual(NotificacaoDoador.objects.filter(doador=self.doador).count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_mostra_a_data_do_ultimo_alerta_depois_de_emitir(self):
        self._estoque('O+', 5)
        self.assertIsNone(self._card('O+')['ultimo_alerta'])
        self._emitir('O+')
        self.assertIsNotNone(self._card('O+')['ultimo_alerta'])
        self.assertContains(self.client.get(reverse('hemocentros:painel')), 'Último alerta:')

    def test_nao_emite_alerta_se_o_estoque_nao_esta_critico(self):
        from necessidades.models import NecessidadeSanguinea
        self._estoque('O+', 40)
        self._emitir('O+')
        self.assertEqual(NecessidadeSanguinea.objects.count(), 0)

    def test_nao_emite_alerta_para_tipo_invalido(self):
        from necessidades.models import NecessidadeSanguinea
        self._emitir('X+')
        self.assertEqual(NecessidadeSanguinea.objects.count(), 0)

    def test_novo_alerta_encerra_a_necessidade_ativa_anterior_do_mesmo_tipo(self):
        from necessidades.models import NecessidadeSanguinea
        self._estoque('O+', 5)
        self._emitir('O+')
        self._emitir('O+')
        ativas = NecessidadeSanguinea.objects.filter(tipo_sanguineo='O+', ativa=True)
        self.assertEqual(ativas.count(), 1)
        self.assertEqual(NecessidadeSanguinea.objects.filter(tipo_sanguineo='O+').count(), 2)

    def test_doador_nao_emite_alerta(self):
        from necessidades.models import NecessidadeSanguinea
        self._estoque('O+', 5)
        cliente = Client()
        cliente.force_login(self.doador.usuario)
        cliente.post(reverse('hemocentros:emitir_alerta_estoque'), {'tipo': 'O+'})
        self.assertEqual(NecessidadeSanguinea.objects.count(), 0)

    def test_get_na_rota_de_alerta_nao_emite(self):
        from necessidades.models import NecessidadeSanguinea
        self._estoque('O+', 5)
        self.client.get(reverse('hemocentros:emitir_alerta_estoque'), {'tipo': 'O+'})
        self.assertEqual(NecessidadeSanguinea.objects.count(), 0)


class CadastroPresencialTests(BaseAgenda):
    def _dados(self, **alteracoes):
        dados = {
            'username': 'presencial1', 'email': 'presencial1@email.com',
            'password1': 'SenhaForte!2026', 'password2': 'SenhaForte!2026',
            'nome_completo': 'Doador Presencial', 'cpf': '529.982.247-25',
            'data_nascimento': '1990-01-01', 'sexo': 'M', 'peso': '75.0',
            'tipo_sanguineo': 'O+', 'telefone': '',
            'logradouro': 'Rua A', 'numero': '1', 'bairro': 'Centro',
            'cidade': 'São Paulo', 'estado': 'SP', 'cep': '01001-000',
        }
        dados.update(alteracoes)
        return dados

    def test_cadastro_presencial_cria_doador_e_agendamento_de_hoje(self):
        resp = self.client.post(reverse('hemocentros:cadastrar_doador_presencial'), self._dados())
        doador = Doador.objects.get(cpf='529.982.247-25')
        self.assertRedirects(
            resp, f"{reverse('hemocentros:registrar_doacao')}?doador={doador.pk}", fetch_redirect_response=False,
        )
        agendamento = doador.agendamentos.get()
        self.assertEqual(agendamento.hemocentro, self.hemocentro)
        self.assertEqual(agendamento.data, date.today())
        self.assertEqual(agendamento.status, Agendamento.Status.CONFIRMADO)

    def test_doador_presencial_aparece_na_busca_e_pode_ter_a_doacao_registrada(self):
        self.client.post(reverse('hemocentros:cadastrar_doador_presencial'), self._dados())
        doador = Doador.objects.get(cpf='529.982.247-25')
        resp = self.client.get(reverse('hemocentros:registrar_doacao'), {'doador': doador.pk})
        self.assertEqual(resp.status_code, 200)
        self.client.post(
            reverse('hemocentros:registrar_doacao'),
            {'doador_id': doador.pk, 'data_doacao': date.today().isoformat(), 'local': ''},
        )
        self.assertEqual(doador.historico.count(), 1)
        self.assertEqual(doador.agendamentos.get().status, Agendamento.Status.CONCLUIDO)

    def test_estoque_so_sobe_quando_a_doacao_do_doador_presencial_e_confirmada(self):
        from hemocentros.models import EstoqueSanguineo
        EstoqueSanguineo.objects.create(hemocentro=self.hemocentro, tipo_sanguineo='O+', quantidade_bolsas=10)
        self.client.post(reverse('hemocentros:cadastrar_doador_presencial'), self._dados())
        self.assertEqual(self.hemocentro.estoque.get(tipo_sanguineo='O+').quantidade_bolsas, 10)
        doador = Doador.objects.get(cpf='529.982.247-25')
        self.client.post(
            reverse('hemocentros:registrar_doacao'),
            {'doador_id': doador.pk, 'data_doacao': date.today().isoformat(), 'local': ''},
        )
        self.assertEqual(self.hemocentro.estoque.get(tipo_sanguineo='O+').quantidade_bolsas, 11)

    def test_cadastro_presencial_com_cpf_invalido_nao_cria_nada_e_reabre_o_modal(self):
        resp = self.client.post(
            reverse('hemocentros:cadastrar_doador_presencial'), self._dados(cpf='123.456.789-00'),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context['abrir_modal_cadastro'])
        self.assertFalse(Doador.objects.filter(nome_completo='Doador Presencial').exists())

    def test_cadastro_presencial_com_cpf_ja_cadastrado_e_recusado(self):
        Doador.objects.filter(pk=self.doador.pk).update(cpf='52998224725')
        resp = self.client.post(reverse('hemocentros:cadastrar_doador_presencial'), self._dados())
        self.assertEqual(resp.status_code, 200)
        self.assertIn('cpf', resp.context['formulario_doador'].errors)

    def test_modal_presencial_impede_preenchimento_automatico_do_navegador(self):
        html = self.client.get(reverse('hemocentros:registrar_doacao')).content.decode()
        self.assertIn('autocomplete="new-password"', html)
        modal = html[html.index('modalCadastroPresencial'):]
        self.assertIn('name="username"', modal)
        self.assertIn('autocomplete="off"', modal)
        self.assertIn('max-height: calc(100vh - 3.5rem)', html)

    def test_doador_nao_usa_o_cadastro_presencial(self):
        cliente = Client()
        cliente.force_login(self.doador.usuario)
        resp = cliente.post(reverse('hemocentros:cadastrar_doador_presencial'), self._dados())
        self.assertEqual(resp.status_code, 404)


class AgendaPaginadaTests(BaseAgenda):
    def test_agenda_e_paginada_e_mantem_o_filtro(self):
        for dia in range(25):
            self._agendamento(-(dia + 1), Agendamento.Status.CANCELADO)
        primeira = self.client.get(reverse('hemocentros:painel'), {'status': 'cancelado'})
        self.assertEqual(len(primeira.context['agendamentos']), 20)
        self.assertContains(primeira, 'status=cancelado&pagina=2')
        segunda = self.client.get(reverse('hemocentros:painel'), {'status': 'cancelado', 'pagina': 2})
        self.assertEqual(len(segunda.context['agendamentos']), 5)

    def test_pagina_invalida_nao_quebra(self):
        resp = self.client.get(reverse('hemocentros:painel'), {'pagina': 'abc'})
        self.assertEqual(resp.status_code, 200)

    def test_doador_acima_de_70_mostra_aviso_de_avaliacao_medica(self):
        self.doador.data_nascimento = date(date.today().year - 72, 1, 1)
        self.doador.save()
        self._agendamento(1)
        self.assertContains(self.client.get(reverse('hemocentros:painel')), 'Avaliação médica')

    def test_concluir_cancelar_voltam_na_mesma_pagina(self):
        agendamento = self._agendamento(0)
        resp = self.client.post(
            reverse('hemocentros:atualizar_agendamento', args=[agendamento.pk]),
            {'acao': 'concluir', 'voltar': 'status=confirmado&pagina=2'},
        )
        self.assertIn('pagina=2', resp.url)


class EstoqueEmLoteTests(BaseAgenda):
    def test_salvar_sem_mudancas_nao_altera_a_data_de_atualizacao(self):
        dados = {f'tipo_{t}': 20 for t in ['Apos', 'Aneg', 'Bpos', 'Bneg', 'ABpos', 'ABneg', 'Opos', 'Oneg']}
        url = reverse('hemocentros:atualizar_estoque')
        self.client.post(url, dados)
        antes = {e.tipo_sanguineo: e.atualizado_em for e in self.hemocentro.estoque.all()}
        dados['tipo_Opos'] = 33
        self.client.post(url, dados)
        depois = {e.tipo_sanguineo: e.atualizado_em for e in self.hemocentro.estoque.all()}
        self.assertEqual(antes['A+'], depois['A+'])
        self.assertNotEqual(antes['O+'], depois['O+'])
        self.assertEqual(self.hemocentro.estoque.get(tipo_sanguineo='O+').quantidade_bolsas, 33)


class AgendamentoAusenteTests(BaseAgenda):
    def test_agendamento_confirmado_de_data_passada_vira_ausente(self):
        passado = self._agendamento(-2)
        hoje = self._agendamento(0, Agendamento.Status.CONCLUIDO)
        Agendamento.marcar_ausentes()
        passado.refresh_from_db()
        hoje.refresh_from_db()
        self.assertEqual(passado.status, Agendamento.Status.AUSENTE)
        self.assertEqual(hoje.status, Agendamento.Status.CONCLUIDO)

    def test_agendamento_de_hoje_e_de_data_futura_nao_viram_ausentes(self):
        Agendamento.marcar_ausentes()
        hoje = self._agendamento(0)
        Agendamento.marcar_ausentes()
        hoje.refresh_from_db()
        self.assertEqual(hoje.status, Agendamento.Status.CONFIRMADO)

    def test_painel_do_hemocentro_marca_e_mostra_ausente(self):
        passado = self._agendamento(-2)
        resp = self.client.get(reverse('hemocentros:painel'))
        passado.refresh_from_db()
        self.assertEqual(passado.status, Agendamento.Status.AUSENTE)
        self.assertContains(resp, 'Ausente')
        filtrado = self.client.get(reverse('hemocentros:painel'), {'status': 'ausente'})
        self.assertEqual(list(filtrado.context['agendamentos']), [passado])

    def test_ausente_e_um_estado_final_sem_acoes(self):
        passado = self._agendamento(-2)
        resp = self.client.get(reverse('hemocentros:painel'))
        html = resp.content.decode()
        self.assertNotIn(f'/painel/agendamento/{passado.pk}/status/', html)
        self._acao(passado, 'concluir')
        passado.refresh_from_db()
        self.assertEqual(passado.status, Agendamento.Status.AUSENTE)
        self.assertEqual(self.doador.historico.count(), 0)

    def test_hemocentro_nao_cancela_um_ausente(self):
        passado = self._agendamento(-2)
        self.client.get(reverse('hemocentros:painel'))
        self._acao(passado, 'cancelar')
        passado.refresh_from_db()
        self.assertEqual(passado.status, Agendamento.Status.AUSENTE)

    def test_doador_com_ausente_pode_fazer_novo_agendamento(self):
        passado = self._agendamento(-2)
        cliente = Client()
        cliente.force_login(self.doador.usuario)
        cliente.post(
            reverse('doadores:criar_agendamento', args=[self.hemocentro.id]),
            {'data': (date.today() + timedelta(days=3)).isoformat(), 'horario': '09:00', 'aceite_requisitos': 'on'},
        )
        passado.refresh_from_db()
        self.assertEqual(passado.status, Agendamento.Status.AUSENTE)
        self.assertEqual(self.doador.agendamentos.filter(status=Agendamento.Status.CONFIRMADO).count(), 1)
        self.assertEqual(self.doador.agendamentos.count(), 2)

    def test_painel_do_doador_mostra_ausente(self):
        self._agendamento(-2)
        cliente = Client()
        cliente.force_login(self.doador.usuario)
        self.assertContains(cliente.get(reverse('doadores:painel')), 'Ausente')

    def test_comando_popular_estoque_nao_roda_com_debug_desligado_sem_forcar(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        from io import StringIO
        with self.assertRaises(CommandError):
            call_command('popular_estoque', hemocentro='hemo_agenda', stdout=StringIO())
        self.assertEqual(self.hemocentro.estoque.count(), 0)

    def test_comando_popular_estoque_roda_com_debug_ligado(self):
        from django.core.management import call_command
        from django.test import override_settings
        from io import StringIO
        with override_settings(DEBUG=True):
            call_command('popular_estoque', hemocentro='hemo_agenda', stdout=StringIO())
        self.assertEqual(self.hemocentro.estoque.count(), 8)


class AptidaoNaConfirmacaoTests(BaseAgenda):
    def _registrar(self, data=None):
        return self.client.post(
            reverse('hemocentros:registrar_doacao'),
            {'doador_id': self.doador.pk, 'data_doacao': (data or date.today()).isoformat(), 'local': ''},
        )

    def test_registro_bloqueado_para_doador_abaixo_do_peso(self):
        self.doador.peso = Decimal('45.0')
        self.doador.save()
        self._agendamento(0)
        resp = self._registrar()
        self.assertEqual(self.doador.historico.count(), 0)
        self.assertContains(resp, 'não está apto a doar')

    def test_registro_bloqueado_para_gestante(self):
        self.doador.esta_gestante = True
        self.doador.save()
        self._registrar()
        self.assertEqual(self.doador.historico.count(), 0)

    def test_concluir_bloqueado_para_doador_inapto(self):
        self.doador.peso = Decimal('45.0')
        self.doador.save()
        agendamento = self._agendamento(0)
        self._acao(agendamento, 'concluir')
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, Agendamento.Status.CONFIRMADO)
        self.assertEqual(self.doador.historico.count(), 0)

    def test_idade_fica_para_a_triagem_e_nao_bloqueia_a_confirmacao(self):
        self.doador.data_nascimento = date(date.today().year - 73, 1, 1)
        self.doador.save()
        self.assertFalse(self.doador.apto_para_doar()[0])
        self.assertTrue(self.doador.apto_para_doar(considerar_idade=False)[0])
        self._registrar()
        self.assertEqual(self.doador.historico.count(), 1)

    def test_tela_de_registro_desativa_o_botao_e_mostra_os_motivos(self):
        self.doador.peso = Decimal('45.0')
        self.doador.save()
        resp = self.client.get(reverse('hemocentros:registrar_doacao'), {'doador': self.doador.pk})
        self.assertContains(resp, 'Não é possível confirmar a doação')
        self.assertIn('disabled', resp.content.decode()[resp.content.decode().index('Confirmar doação') - 120:])
        self.assertContains(resp, 'A avaliação por idade é feita pela triagem')

    def test_tela_de_registro_com_doador_apto_mantem_o_botao_ativo(self):
        resp = self.client.get(reverse('hemocentros:registrar_doacao'), {'doador': self.doador.pk})
        self.assertNotContains(resp, 'Não é possível confirmar a doação')

