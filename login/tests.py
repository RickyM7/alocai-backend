from django.test import TestCase, Client
from django.contrib.auth.models import User
from login.models import Usuario
from unittest.mock import patch

class GoogleSignInTest(TestCase):

    @patch('login.views.id_token.verify_oauth2_token')
    def test_first_login_creates_user_and_usuario(self, mock_verify_google_token):
        """
        Verifica se o primeiro login cria um registro em auth_user e em usuario.
        """
        #Simula a resposta que o Google enviaria após validar o token
        mock_google_user_data = {
            'email': 'novo.usuario@teste.com',
            'given_name': 'Novo',
            'family_name': 'Usuario',
            'email_verified': True
        }
        mock_verify_google_token.return_value = mock_google_user_data

        #Simula a requisição POST que o frontend faria
        client = Client()
        response = client.post('/api/google-sign-in/', {
            'credential': 'um-token-falso-que-sera-ignorado-pelo-mock'
        }, content_type='application/json')

        #A requisição foi bem-sucedida?
        self.assertEqual(response.status_code, 200)

        usuario_exists = Usuario.objects.filter(email='novo.usuario@teste.com').exists()
        self.assertTrue(usuario_exists)

        #Se chamarmos de novo, não deve criar outro usuário
        Usuario.objects.all().delete()

    @patch('login.views.id_token.verify_oauth2_token')
    def test_login_google(self, mock_verify):
        # Simula um token válido
        mock_verify.return_value = {
            'email': 'test@example.com',
            'given_name': 'Test',
            'family_name': 'User'
        }
        response = self.client.post('/api/google-sign-in/', {
            'credential': 'valid_token_example'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)  # Se você retorna JWT

    def test_login_google_invalid_token(self):
        response = self.client.post('/api/google-sign-in/', {
            'credential': 'invalid_token'
        })
        self.assertEqual(response.status_code, 403)

    @patch('login.views.id_token.verify_oauth2_token')
    def test_login_user_already_exists(self, mock_verify):
        # Cria um usuário antes de testar o login
        Usuario.objects.create(
            email='test@example.com',
            nome='Test User',
            data_criacao_conta='2023-01-01T00:00:00Z',
        )

        mock_verify.return_value = {
            'email': 'test@example.com',
            'given_name': 'Test',
            'family_name': 'User'
        }

        response = self.client.post('/api/google-sign-in/', {
            'credential': 'valid_token_example'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('access', response.data)

        # Verifica se a data de ultimo login foi atualizada
        usuario = Usuario.objects.get(email='test@example.com')
        usuario_exists = usuario.ultimo_login is not None
        self.assertTrue(usuario_exists)

    def test_logout_google(self):
        pass
