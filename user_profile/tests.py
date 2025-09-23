from django.urls import reverse
from rest_framework import status
from .models import PerfilAcesso
from alocai.test_base import BaseTestCase

class UserProfileAPITestCase(BaseTestCase):

    def setUp(self):
        self.terc_profile = PerfilAcesso.objects.create(nome_perfil='Terceirizado', visibilidade=True)
    
    def testar_admin_pode_ver_todos_perfis(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('perfil_acesso')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def testar_usuario_nao_logado_ve_perfis_visiveis(self):
        url = reverse('perfil_acesso')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        profile_names = {p['nome_perfil'] for p in response.data}
        self.assertNotIn('Administrador', profile_names)

    def testar_usuario_logado_ve_perfis_visiveis(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('perfil_acesso')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        profile_names = {p['nome_perfil'] for p in response.data}
        self.assertNotIn('Administrador', profile_names)