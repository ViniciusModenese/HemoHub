from django.test import TestCase, Client
from django.urls import reverse
from usuarios.models import Usuario

class UsuarioLoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('usuarios:login')
        self.doador = Usuario.objects.create_user(
            username='doador_teste',
            email='doador_teste@email.com',
            password='senha_teste_123',
            tipo_usuario=Usuario.TipoUsuario.DOADOR
        )
        self.hemocentro = Usuario.objects.create_user(
            username='hemo_teste',
            email='hemo_teste@email.com',
            password='senha_teste_123',
            tipo_usuario=Usuario.TipoUsuario.HEMOCENTRO
        )

    def test_login_doador_sucesso(self):
        resp = self.client.post(self.login_url, {
            'username': 'doador_teste',
            'password': 'senha_teste_123',
            'tipo_perfil': 'doador'
        })
        self.assertEqual(resp.status_code, 302)

    def test_login_doador_com_email(self):
        resp = self.client.post(self.login_url, {
            'username': 'doador_teste@email.com',
            'password': 'senha_teste_123',
            'tipo_perfil': 'doador'
        })
        self.assertEqual(resp.status_code, 302)

    def test_login_hemocentro_sucesso(self):
        resp = self.client.post(self.login_url, {
            'username': 'hemo_teste',
            'password': 'senha_teste_123',
            'tipo_perfil': 'hemocentro'
        })
        self.assertEqual(resp.status_code, 302)

    def test_bloqueio_doador_na_opcao_hemocentro(self):
        resp = self.client.post(self.login_url, {
            'username': 'doador_teste',
            'password': 'senha_teste_123',
            'tipo_perfil': 'hemocentro'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Esta conta pertence a um Doador')

    def test_bloqueio_hemocentro_na_opcao_doador(self):
        resp = self.client.post(self.login_url, {
            'username': 'hemo_teste',
            'password': 'senha_teste_123',
            'tipo_perfil': 'doador'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Esta conta pertence a um Hemocentro')

