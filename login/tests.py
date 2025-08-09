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

        #O usuário foi criado na tabela auth_user?
        user_exists = User.objects.filter(email='novo.usuario@teste.com').exists()
        self.assertTrue(user_exists)

        #O usuário foi criado na sua tabela personalizada 'usuario'?
        usuario_exists = Usuario.objects.filter(email='novo.usuario@teste.com').exists()
        self.assertTrue(usuario_exists)

        #Se chamarmos de novo, não deve criar outro usuário
        Usuario.objects.all().delete()
        User.objects.all().delete()
