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
    def test_login_google_novo_usuario(self, mock_verify):
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
    def test_login_google_usuario_existente(self, mock_verify):
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
    def test_login_google_token_invalido(self, mock_verify):
        url = reverse('google_sign_in')
        response = self.client.post(url, {'credential': 'invalid_token'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_admin_sucesso(self):
        url = reverse('admin_login')
        data = {'email': 'admin@teste.com', 'password': 'password123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_admin_falha_nao_admin(self):
        url = reverse('admin_login')
        data = {'email': 'servidor@teste.com', 'password': 'password123'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permissao_lista_usuarios(self):
        url = reverse('admin_user_list')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.force_authenticate(user=self.server_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_permissoes_atualizacao_perfil_usuario(self):
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

    def test_admin_pode_deletar_usuario(self):
        user_to_delete = Usuario.objects.create(email='delete@me.com', nome='Delete Me')
        url = reverse('user_api_view', kwargs={'id_usuario': user_to_delete.id_usuario})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Usuario.objects.filter(email='delete@me.com').exists())

    def test_admin_nao_pode_deletar_a_si_mesmo(self):
        url = reverse('user_api_view', kwargs={'id_usuario': self.admin_user.id_usuario})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('login.views.id_token.verify_oauth2_token')
    def test_vincular_conta_google(self, mock_verify):
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

    def test_mudanca_de_senha(self):
        url = reverse('admin_change_password')
        data = {'new_password': 'new_password123'}
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.check_password('new_password123'))
        
    def test_propriedades_customizadas_model_usuario(self):
        self.assertEqual(self.admin_user.id, self.admin_user.id_usuario)
        self.assertEqual(self.admin_user.pk, self.admin_user.id_usuario)
        self.assertTrue(self.admin_user.is_authenticated)

    def test_fluxo_de_refresh_token(self):
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

    def test_health_check_retorna_ok(self):
        url = reverse('health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_admin_login_sem_campos_retorna_400(self):
        url = reverse('admin_login')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_login_credenciais_erradas_retorna_401(self):
        url = reverse('admin_login')
        response = self.client.post(url, {'email': 'admin@teste.com', 'password': 'errada'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('login.views.id_token.verify_oauth2_token')
    def test_vincular_google_email_duplicado_retorna_409(self, mock_verify):
        """Se o email do Google já pertence a outro usuário, deve retornar 409."""
        Usuario.objects.create_user(email='already@taken.com', nome='Outro')
        mock_verify.return_value = {
            'email': 'already@taken.com',
            'given_name': 'Outro', 'family_name': 'User',
            'sub': 'google-unique-new-id'
        }
        url = reverse('admin_link_google')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, {'credential': 'tok'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_mudanca_de_senha_muito_curta_retorna_400(self):
        url = reverse('admin_change_password')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, {'new_password': '123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_google_sign_out(self):
        """Logout deve invalidar o refresh token e apagar o cookie."""
        # First login to get a valid refresh token cookie
        login_url = reverse('admin_login')
        response = self.client.post(login_url, {'email': 'admin@teste.com', 'password': 'password123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        url = reverse('google_sign_out')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_google_sign_out_sem_autenticacao_retorna_401(self):
        url = reverse('google_sign_out')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_sem_cookie_retorna_401(self):
        url = reverse('token_refresh')
        self.client.cookies.clear()
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_google_sign_in_sem_credential_retorna_400(self):
        url = reverse('google_sign_in')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_mudanca_de_senha_sem_campo_retorna_400(self):
        url = reverse('admin_change_password')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vincular_google_sem_credential_retorna_400(self):
        url = reverse('admin_link_google')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_atualizar_perfil_sem_id_perfil_retorna_400(self):
        outro_user = Usuario.objects.create_user(email='noperfil@teste.com', nome='Sem Perfil', password='pw')
        url = reverse('user_api_view', kwargs={'id_usuario': outro_user.id_usuario})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deletar_usuario_inexistente_retorna_404(self):
        url = reverse('user_api_view', kwargs={'id_usuario': 99999})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Branches do GoogleSignInAPIView

    @patch('login.views.id_token.verify_oauth2_token')
    def test_login_google_sem_email_retorna_400(self, mock_verify):
        mock_verify.return_value = {'sub': 'abc123', 'given_name': 'No', 'family_name': 'Email'}
        url = reverse('google_sign_in')
        response = self.client.post(url, {'credential': 'tok'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('login.views.id_token.verify_oauth2_token')
    def test_login_google_encontrado_por_google_id(self, mock_verify):
        """Usuário encontrado por google_id (não por email)."""
        self.server_user.google_id = 'existing-gid'
        self.server_user.save()
        mock_verify.return_value = {
            'sub': 'existing-gid', 'email': 'novemail@google.com',
            'given_name': 'Novo', 'family_name': 'Nome', 'picture': 'http://pic.jpg'
        }
        url = reverse('google_sign_in')
        response = self.client.post(url, {'credential': 'tok'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.server_user.refresh_from_db()
        self.assertEqual(self.server_user.nome, 'Novo Nome')

    # Branches do LinkGoogleAccountView

    @patch('login.views.id_token.verify_oauth2_token')
    def test_vincular_google_google_id_duplicado_retorna_409(self, mock_verify):
        """google_id já vinculado a outro usuário retorna 409."""
        outro = Usuario.objects.create_user(email='outro_g@teste.com', nome='Outro', google_id='dup-gid')
        mock_verify.return_value = {
            'sub': 'dup-gid', 'email': 'email_novo@teste.com',
            'given_name': 'A', 'family_name': 'B'
        }
        url = reverse('admin_link_google')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, {'credential': 'tok'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    @patch('login.views.id_token.verify_oauth2_token', side_effect=ValueError)
    def test_vincular_google_token_invalido_retorna_400(self, mock_verify):
        url = reverse('admin_link_google')
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(url, {'credential': 'bad_tok'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Permissão do ChangePasswordView

    def test_mudanca_de_senha_por_nao_admin_retorna_403(self):
        url = reverse('admin_change_password')
        self.client.force_authenticate(user=self.server_user)
        response = self.client.post(url, {'new_password': 'novaSenha123!'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Branches do UserAPIView

    def test_perfil_inexistente_retorna_404(self):
        outro = Usuario.objects.create_user(email='perf404@teste.com', nome='Perf')
        url = reverse('user_api_view', kwargs={'id_usuario': outro.id_usuario})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(url, {'id_perfil': 99999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_rebaixamento_de_admin_invalida_senha(self):
        admin2 = Usuario.objects.create_user(
            email='admin2@teste.com', nome='Admin 2',
            password='pass123', id_perfil=self.admin_profile
        )
        self.assertTrue(admin2.has_usable_password())
        url = reverse('user_api_view', kwargs={'id_usuario': admin2.id_usuario})
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.put(url, {'id_perfil': self.server_profile.id_perfil}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        admin2.refresh_from_db()
        self.assertFalse(admin2.has_usable_password())

    # CookieTokenRefreshView com token inválido

    def test_refresh_com_token_invalido_retorna_401(self):
        url = reverse('token_refresh')
        self.client.cookies['refresh_token'] = 'token_completamente_invalido'
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # health_check com banco indisponível

    @patch('login.views.connection')
    def test_health_check_banco_indisponivel_retorna_503(self, mock_conn):
        mock_conn.ensure_connection.side_effect = Exception('DB down')
        url = reverse('health_check')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['status'], 'error')


class UsuarioManagerTestCase(BaseTestCase):
    """Testes unitários para UsuarioManager."""

    def test_create_user_sem_email_lanca_erro(self):
        with self.assertRaises(ValueError) as ctx:
            Usuario.objects.create_user(email='', nome='Sem Email')
        self.assertIn('obrigatório', str(ctx.exception))

    def test_create_user_sem_senha_nao_tem_senha_usavel(self):
        user = Usuario.objects.create_user(email='nosenha@teste.com', nome='No Senha')
        self.assertFalse(user.has_usable_password())

    def test_create_superuser_com_todos_campos(self):
        su = Usuario.objects.create_superuser(email='su@teste.com', nome='Super', password='pw123')
        self.assertTrue(su.is_staff)
        self.assertTrue(su.is_superuser)

    def test_create_superuser_sem_is_staff_lanca_erro(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser(email='su2@teste.com', nome='Super', password='pw', is_staff=False)

    def test_create_superuser_sem_is_superuser_lanca_erro(self):
        with self.assertRaises(ValueError):
            Usuario.objects.create_superuser(email='su3@teste.com', nome='Super', password='pw', is_superuser=False)