from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from login.models import Usuario
from resources.models import Recurso
from .models import Agendamento, AgendamentoPai
from datetime import date, time
from alocai.test_base import BaseTestCase

class BookingAPITestCase(BaseTestCase):

    def setUp(self):
        self.another_user = Usuario.objects.create_user(email='another_server@teste.com', nome='Another Server', password='pw', id_perfil=self.server_profile)
        self.recurso = Recurso.objects.create(nome_recurso="Laboratório de Testes", status_recurso="disponivel")
        self.agendamento_pai = AgendamentoPai.objects.create(id_usuario=self.server_user, id_recurso=self.recurso, finalidade="Aula de Testes", id_responsavel=self.server_user)
        self.agendamento_pendente = Agendamento.objects.create(agendamento_pai=self.agendamento_pai, data_inicio=date(2025, 10, 1), hora_inicio=time(10, 0), data_fim=date(2025, 10, 1), hora_fim=time(12, 0), status_agendamento='pendente')
        self.agendamento_aprovado = Agendamento.objects.create(agendamento_pai=self.agendamento_pai, data_inicio=date(2025, 10, 2), hora_inicio=time(14, 0), data_fim=date(2025, 10, 2), hora_fim=time(16, 0), status_agendamento='aprovado')

    def testar_criar_agendamento_como_servidor(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('criar-agendamento')
        data = {
            "id_recurso": self.recurso.id_recurso, "finalidade": "Nova Aula", "id_responsavel": self.server_user.id_usuario,
            "datas_agendamento": [{"data_inicio": "2025-11-01", "hora_inicio": "10:00", "data_fim": "2025-11-01", "hora_fim": "12:00"}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AgendamentoPai.objects.filter(finalidade="Nova Aula").exists())

    def testar_criar_agendamento_sem_autenticacao(self):
        url = reverse('criar-agendamento')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def testar_listar_minhas_reservas(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('listar-agendamentos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def testar_admin_lista_todos_agendamentos(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-listar-agendamentos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def testar_admin_aprova_agendamento(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'aprovado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pendente.refresh_from_db()
        self.assertEqual(self.agendamento_pendente.status_agendamento, 'aprovado')

    @patch('booking.views.criar_notificacao_resumida_conflito')
    def testar_negacao_de_conflito_ao_aprovar(self, mock_notificacao):
        pai_conflitante = AgendamentoPai.objects.create(id_usuario=self.another_user, id_recurso=self.recurso, id_responsavel=self.another_user)
        agendamento_conflitante = Agendamento.objects.create(agendamento_pai=pai_conflitante, data_inicio=date(2025, 10, 1), hora_inicio=time(10, 30), data_fim=date(2025, 10, 1), hora_fim=time(11, 30), status_agendamento='pendente')

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        self.client.patch(url, {'status_agendamento': 'aprovado'}, format='json')
        
        agendamento_conflitante.refresh_from_db()
        self.assertEqual(agendamento_conflitante.status_agendamento, 'negado')
        self.assertTrue(mock_notificacao.called)

    def testar_admin_deleta_agendamento_pai(self):
        self.client.force_authenticate(user=self.admin_user)
        pai_pk = self.agendamento_pai.pk
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': pai_pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AgendamentoPai.objects.filter(pk=pai_pk).exists())

    def testar_usuario_cancela_propria_reserva_pai(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pai.refresh_from_db()
        for ag in self.agendamento_pai.agendamentos_filhos.all():
            self.assertEqual(ag.status_agendamento, 'cancelado')

    def testar_usuario_nao_pode_modificar_reserva_de_outro(self):
        self.client.force_authenticate(user=self.another_user)
        url = reverse('user-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def testar_verificar_disponibilidade_recurso(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('recurso-disponibilidade', kwargs={'recurso_id': self.recurso.id_recurso})
        response = self.client.get(url, {'ano': 2025, 'mes': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {'2025-10-02': [{'start': '14:00', 'end': '16:00'}]}
        self.assertEqual(response.data, expected_data)