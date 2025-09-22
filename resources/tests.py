from django.urls import reverse
from rest_framework import status
from .models import Recurso
from alocai.test_base import BaseTestCase

class ResourcesAPITestCase(BaseTestCase):

    def setUp(self):
        self.recurso1 = Recurso.objects.create(nome_recurso="Laboratório A", status_recurso="disponivel")
        self.recurso2 = Recurso.objects.create(nome_recurso="Sala de Reunião B", status_recurso="em_manutencao")

    def testar_admin_cria_recurso(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-list')
        data = {"nome_recurso": "Projetor", "status_recurso": "disponivel"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def testar_servidor_nao_pode_criar_recurso(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('recurso-admin-list')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testar_listar_recursos_para_usuario_logado(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('listar-recursos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def testar_admin_lista_todos_recursos(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def testar_admin_atualiza_recurso(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-detail', kwargs={'pk': self.recurso1.pk})
        data = {'nome_recurso': 'Laboratório A Renovado', 'status_recurso': 'disponivel'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recurso1.refresh_from_db()
        self.assertEqual(self.recurso1.nome_recurso, 'Laboratório A Renovado')

    def testar_admin_deleta_recurso(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-detail', kwargs={'pk': self.recurso1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recurso.objects.filter(pk=self.recurso1.pk).exists())
        
    def testar_action_alterar_status_recurso(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-alterar-status', kwargs={'pk': self.recurso1.pk})
        response = self.client.post(url, {'status': 'em_manutencao'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recurso1.refresh_from_db()
        self.assertEqual(self.recurso1.status_recurso, 'em_manutencao')
        
    def testar_action_status_disponiveis(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-status-disponiveis')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status_disponiveis', response.data)
        self.assertIsInstance(response.data['status_disponiveis'], list)