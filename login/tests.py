from unittest.mock import patch
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class LoginAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass'
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

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

    def test_logout_google(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.access_token)
        response = self.client.post('/api/google-sign-out/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('detail', response.data)