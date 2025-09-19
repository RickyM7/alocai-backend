from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from login.models import Usuario
from resource.models import Recurso
from booking.models import AgendamentoPai
from .models import Notificacao
from .utils import criar_e_enviar_notificacao
from alocai.test_base import BaseTestCase

class NotificationAPITestCase(BaseTestCase):

    def setUp(self):
        self.user2 = Usuario.objects.create_user(email='user2@teste.com', nome='User 2', password='pw', id_perfil=self.server_profile)
        self.notif1 = Notificacao.objects.create(destinatario=self.server_user, mensagem="Sua reserva foi aprovada.", lida=False)
        self.notif2 = Notificacao.objects.create(destinatario=self.server_user, mensagem="Sua reserva foi negada.", lida=True)
        self.notif3 = Notificacao.objects.create(destinatario=self.user2, mensagem="Manutenção no Lab A.", lida=False)

    def testar_listar_proprias_notificacoes(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('listar-notificacoes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def testar_marcar_notificacoes_como_lidas(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('marcar-notificacoes-lidas')
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.lida)
        self.assertFalse(Notificacao.objects.filter(destinatario=self.server_user, lida=False).exists())

    def testar_deletar_notificacao(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('gerenciar-notificacao', kwargs={'pk': self.notif1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notificacao.objects.filter(pk=self.notif1.pk).exists())

    def testar_usuario_nao_pode_acessar_notificacoes_de_outro(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse('gerenciar-notificacao', kwargs={'pk': self.notif1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('notification.utils.threading.Thread')
    def testar_utilitario_criar_e_enviar_notificacao(self, mock_thread):
        recurso = Recurso.objects.create(nome_recurso="Recurso para Notif")
        ag_pai = AgendamentoPai.objects.create(id_usuario=self.server_user, id_recurso=recurso, id_responsavel=self.server_user)

        criar_e_enviar_notificacao(self.server_user, ag_pai, "Mensagem de teste")
        
        self.assertTrue(Notificacao.objects.filter(destinatario=self.server_user, mensagem="Mensagem de teste").exists())
        self.assertTrue(mock_thread.called)