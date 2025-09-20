import time
from datetime import timedelta
from django.urls import reverse
from django.test import override_settings
from rest_framework import status
from unittest.mock import patch
from .models import Usuario
from alocai.test_base import BaseTestCase

class LoginAPITestCase(BaseTestCase):

    @patch('login.views.id_token.verify_oauth2_token')
    def testar_login_google_novo_usuario(self, mock_verify):
        mock_verify.return_value = {
            'email': 'novo.usuario@google.com',
            'given_name': 'Novo',
            'family_name': 'Usuario',
            'sub': 'google-id-123'
        }
        url = reverse('google_sign_in')
        response = self.client.post(url, {'credential': 'test_token'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue(Usuario.objects.filter(email='novo.usuario@google.com').exists())

    @patch('login.views.id_token.verify_oauth2_token')
    def testar_login_google_usuario_existente(self, mock_verify):
        mock_verify.return_value = {
            'email': 'servidor@teste.com',
            'given_name': 'Servidor',
            'family_name': 'User',
            'sub': 'google-id-456'
        }
        url = reverse('google_sign_in')
        response = self.client.post(url, {'credential': 'test_token'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = Usuario.objects.get(email='servidor@teste.com')
        self.assertEqual(user.google_id, 'google-id-456')

    @patch('login.views.id_token.verify_oauth2_token', side_effect=ValueError)
    def testar_login_google_token_invalido(self, mock_verify):
        url = reverse('google_sign_in')
        response = self.client.post(url, {'credential': 'invalid_token'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testar_login_admin_sucesso(self):
        url = reverse('admin_login')
        data = {'email': 'admin@teste.com', 'password': 'password123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def testar_login_admin_falha_nao_admin(self):
        url = reverse('admin_login')
        data = {'email': 'servidor@teste.com', 'password': 'password123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testar_permissao_lista_usuarios(self):
        url = reverse('admin_user_list')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.server_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testar_permissoes_atualizacao_perfil_usuario(self):
        outro_user = Usuario.objects.create_user(email='outro@teste.com', nome='Outro', password='pw')
        url = reverse('user_api_view', kwargs={'id_usuario': outro_user.id_usuario})
        data = {'id_perfil': self.server_profile.id_perfil}
        
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        outro_user.refresh_from_db()
        self.assertEqual(outro_user.id_perfil, self.server_profile)
        
        self.client.force_authenticate(user=self.server_user)
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        admin_url = reverse('user_api_view', kwargs={'id_usuario': self.admin_user.id_usuario})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(admin_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testar_admin_pode_deletar_usuario(self):
        user_to_delete = Usuario.objects.create(email='delete@me.com', nome='Delete Me')
        url = reverse('user_api_view', kwargs={'id_usuario': user_to_delete.id_usuario})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Usuario.objects.filter(email='delete@me.com').exists())

    def testar_admin_nao_pode_deletar_a_si_mesmo(self):
        url = reverse('user_api_view', kwargs={'id_usuario': self.admin_user.id_usuario})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('login.views.id_token.verify_oauth2_token')
    def testar_vincular_conta_google(self, mock_verify):
        mock_verify.return_value = {
            'email': 'admin.google@teste.com',
            'given_name': 'Admin',
            'family_name': 'Google',
            'sub': 'google-admin-123'
        }
        url = reverse('admin_link_google')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, {'credential': 'test_token'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.google_id, 'google-admin-123')
        self.assertEqual(self.admin_user.email, 'admin.google@teste.com')

    def testar_mudanca_de_senha(self):
        url = reverse('admin_change_password')
        data = {'new_password': 'new_password123'}
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password('new_password123'))
        
    def testar_propriedades_customizadas_model_usuario(self):
        self.assertEqual(self.admin_user.id, self.admin_user.id_usuario)
        self.assertEqual(self.admin_user.pk, self.admin_user.id_usuario)
        self.assertTrue(self.admin_user.is_authenticated)

    def testar_fluxo_de_refresh_token(self):
        login_url = reverse('admin_login')
        data = {'email': self.admin_user.email, 'password': 'password123'}
        response = self.client.post(login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']
        refresh_token = response.cookies['refresh_token'].value

        protected_url = reverse('admin_user_list')
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.credentials(HTTP_AUTHORIZATION='Bearer token_invalido')
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        refresh_url = reverse('token_refresh')
        self.client.credentials()
        self.client.cookies['refresh_token'] = refresh_token
        response = self.client.post(refresh_url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_access_token = response.data['access']
        self.assertNotEqual(access_token, new_access_token)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        response = self.client.get(protected_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)