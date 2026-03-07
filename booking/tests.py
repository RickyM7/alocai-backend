from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from login.models import Usuario
from resources.models import Recurso
from .models import Agendamento, AgendamentoPai, UsoImediato
from datetime import date, time, timedelta
from django.utils import timezone
from alocai.test_base import BaseTestCase

class BookingAPITestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.another_user = Usuario.objects.create_user(email='another_server@teste.com', nome='Another Server', password='pw', id_perfil=self.server_profile)
        self.recurso = Recurso.objects.create(nome_recurso="Laboratório de Testes", status_recurso="disponivel")
        self.agendamento_pai = AgendamentoPai.objects.create(id_usuario=self.server_user, id_recurso=self.recurso, finalidade="Aula de Testes", id_responsavel=self.server_user)
        self.agendamento_pendente = Agendamento.objects.create(agendamento_pai=self.agendamento_pai, data_inicio=date(2025, 10, 1), hora_inicio=time(10, 0), data_fim=date(2025, 10, 1), hora_fim=time(12, 0), status_agendamento='pendente')
        self.agendamento_aprovado = Agendamento.objects.create(agendamento_pai=self.agendamento_pai, data_inicio=date(2025, 10, 2), hora_inicio=time(14, 0), data_fim=date(2025, 10, 2), hora_fim=time(16, 0), status_agendamento='aprovado')

    def test_criar_agendamento_como_servidor(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('criar-agendamento')
        data = {
            "id_recurso": self.recurso.id_recurso, "finalidade": "Nova Aula", "id_responsavel": self.server_user.id_usuario,
            "datas_agendamento": [{"data_inicio": "2025-11-01", "hora_inicio": "10:00", "data_fim": "2025-11-01", "hora_fim": "12:00"}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AgendamentoPai.objects.filter(finalidade="Nova Aula").exists())

    def test_criar_agendamento_sem_autenticacao(self):
        url = reverse('criar-agendamento')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_listar_minhas_reservas(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('listar-agendamentos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_lista_todos_agendamentos(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-listar-agendamentos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_aprova_agendamento(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'aprovado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pendente.refresh_from_db()
        self.assertEqual(self.agendamento_pendente.status_agendamento, 'aprovado')

    @patch('booking.views.criar_notificacao_resumida_conflito')
    def test_negacao_de_conflito_ao_aprovar(self, mock_notificacao):
        pai_conflitante = AgendamentoPai.objects.create(id_usuario=self.another_user, id_recurso=self.recurso, id_responsavel=self.another_user)
        agendamento_conflitante = Agendamento.objects.create(agendamento_pai=pai_conflitante, data_inicio=date(2025, 10, 1), hora_inicio=time(10, 30), data_fim=date(2025, 10, 1), hora_fim=time(11, 30), status_agendamento='pendente')

        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        self.client.patch(url, {'status_agendamento': 'aprovado'}, format='json')
        
        agendamento_conflitante.refresh_from_db()
        self.assertEqual(agendamento_conflitante.status_agendamento, 'negado')
        self.assertTrue(mock_notificacao.called)

    def test_admin_deleta_agendamento_pai(self):
        self.client.force_authenticate(user=self.admin_user)
        pai_pk = self.agendamento_pai.pk
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': pai_pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(AgendamentoPai.objects.filter(pk=pai_pk).exists())

    def test_usuario_cancela_propria_reserva_pai(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pai.refresh_from_db()
        for ag in self.agendamento_pai.agendamentos_filhos.all():
            self.assertEqual(ag.status_agendamento, 'cancelado')

    def test_usuario_nao_pode_modificar_reserva_de_outro(self):
        self.client.force_authenticate(user=self.another_user)
        url = reverse('user-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_verificar_disponibilidade_recurso(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('recurso-disponibilidade', kwargs={'recurso_id': self.recurso.id_recurso})
        response = self.client.get(url, {'ano': 2025, 'mes': 10})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_data = {'2025-10-02': [{'start': '14:00', 'end': '16:00'}]}
        self.assertEqual(response.data, expected_data)

    def test_admin_nega_agendamento(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'negado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pendente.refresh_from_db()
        self.assertEqual(self.agendamento_pendente.status_agendamento, 'negado')

    def test_admin_aprova_com_status_invalido_retorna_400(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'status_invalido'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_aprova_conflito_existente_retorna_409(self):
        """Tenta aprovar um horário que já tem outro aprovado — deve retornar 409."""
        conflitante_pai = AgendamentoPai.objects.create(
            id_usuario=self.another_user, id_recurso=self.recurso, id_responsavel=self.another_user
        )
        conflitante = Agendamento.objects.create(
            agendamento_pai=conflitante_pai,
            data_inicio=date(2025, 10, 2), hora_inicio=time(14, 0),
            data_fim=date(2025, 10, 2), hora_fim=time(16, 0),
            status_agendamento='pendente'
        )
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-atualizar-status-agendamento', kwargs={'id_agendamento': conflitante.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'aprovado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_admin_aprova_todos_os_pendentes_do_pai(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.patch(url, {'status_agendamento': 'aprovado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pendente.refresh_from_db()
        self.assertEqual(self.agendamento_pendente.status_agendamento, 'aprovado')

    def test_admin_nega_todos_os_pendentes_do_pai(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.patch(url, {'status_agendamento': 'negado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pendente.refresh_from_db()
        self.assertEqual(self.agendamento_pendente.status_agendamento, 'negado')

    @patch('booking.views.notificar_admins')
    def test_admin_edita_agendamento_pai(self, mock_notif):
        """Admin pode alterar finalidade/observacoes de um agendamento pai."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        payload = {
            'finalidade': 'Finalidade Atualizada',
            'observacoes': 'Obs nova',
            'id_responsavel': self.admin_user.id_usuario,
            'agendamentos_filhos': [
                {
                    'id_agendamento': self.agendamento_pendente.id_agendamento,
                    'data_inicio': '2025-10-01', 'hora_inicio': '10:00',
                    'data_fim': '2025-10-01', 'hora_fim': '12:00',
                }
            ]
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pai.refresh_from_db()
        self.assertEqual(self.agendamento_pai.finalidade, 'Finalidade Atualizada')

    def test_usuario_conclui_propria_reserva(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_aprovado.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'concluido'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_aprovado.refresh_from_db()
        self.assertEqual(self.agendamento_aprovado.status_agendamento, 'concluido')

    def test_usuario_status_invalido_retorna_400(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'aprovado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_detalhe_agendamento_pai_pelo_dono(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('detalhe-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id_agendamento_pai'], self.agendamento_pai.id_agendamento_pai)

    def test_detalhe_agendamento_pai_outro_usuario_retorna_404(self):
        self.client.force_authenticate(user=self.another_user)
        url = reverse('detalhe-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_disponibilidade_sem_parametros_retorna_400(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('recurso-disponibilidade', kwargs={'recurso_id': self.recurso.id_recurso})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_nao_pode_alterar_agendamento_ja_concluido(self):
        self.agendamento_aprovado.status_agendamento = 'concluido'
        self.agendamento_aprovado.save()
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_aprovado.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_status_invalido_para_pai_retorna_400(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Validação do AgendamentoFilhoInputSerializer

    def test_criar_agendamento_hora_fim_anterior_hora_inicio_retorna_400(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('criar-agendamento')
        data = {
            "id_recurso": self.recurso.id_recurso, "finalidade": "Teste",
            "id_responsavel": self.server_user.id_usuario,
            "datas_agendamento": [{"data_inicio": "2025-11-01", "hora_inicio": "14:00", "data_fim": "2025-11-01", "hora_fim": "10:00"}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_agendamento_data_fim_anterior_data_inicio_retorna_400(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('criar-agendamento')
        data = {
            "id_recurso": self.recurso.id_recurso, "finalidade": "Teste",
            "id_responsavel": self.server_user.id_usuario,
            "datas_agendamento": [{"data_inicio": "2025-11-10", "hora_inicio": "10:00", "data_fim": "2025-11-01", "hora_fim": "12:00"}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_agendamento_datas_vazio_retorna_400(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('criar-agendamento')
        data = {
            "id_recurso": self.recurso.id_recurso, "finalidade": "Teste",
            "id_responsavel": self.server_user.id_usuario,
            "datas_agendamento": []
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_agendamento_sem_id_recurso_retorna_400(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('criar-agendamento')
        data = {
            "finalidade": "Teste", "id_responsavel": self.server_user.id_usuario,
            "datas_agendamento": [{"data_inicio": "2025-11-01", "hora_inicio": "10:00", "data_fim": "2025-11-01", "hora_fim": "12:00"}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_criar_agendamento_como_terceirizado_retorna_403(self):
        from user_profile.models import PerfilAcesso
        terc_profile = PerfilAcesso.objects.create(nome_perfil='Terceirizado', visibilidade=True)
        terc_user = Usuario.objects.create_user(email='terc_booking@teste.com', nome='Terc', id_perfil=terc_profile)
        self.client.force_authenticate(user=terc_user)
        url = reverse('criar-agendamento')
        data = {
            "id_recurso": self.recurso.id_recurso, "finalidade": "Teste",
            "id_responsavel": terc_user.id_usuario,
            "datas_agendamento": [{"data_inicio": "2025-11-01", "hora_inicio": "10:00", "data_fim": "2025-11-01", "hora_fim": "12:00"}]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Auto-expiração

    def test_auto_expiracao_aprovado_vira_concluido(self):
        ag = Agendamento.objects.create(
            agendamento_pai=self.agendamento_pai,
            data_inicio=date(2020, 1, 1), hora_inicio=time(8, 0),
            data_fim=date(2020, 1, 1), hora_fim=time(10, 0),
            status_agendamento='aprovado'
        )
        self.client.force_authenticate(user=self.server_user)
        self.client.get(reverse('listar-agendamentos'))
        ag.refresh_from_db()
        self.assertEqual(ag.status_agendamento, 'concluido')

    def test_auto_expiracao_pendente_vira_negado(self):
        ag = Agendamento.objects.create(
            agendamento_pai=self.agendamento_pai,
            data_inicio=date(2020, 1, 1), hora_inicio=time(8, 0),
            data_fim=date(2020, 1, 1), hora_fim=time(10, 0),
            status_agendamento='pendente'
        )
        self.client.force_authenticate(user=self.server_user)
        self.client.get(reverse('listar-agendamentos'))
        ag.refresh_from_db()
        self.assertEqual(ag.status_agendamento, 'negado')

    def test_admin_auto_expiracao(self):
        """Auto-expiração também ocorre na lista admin."""
        ag = Agendamento.objects.create(
            agendamento_pai=self.agendamento_pai,
            data_inicio=date(2020, 1, 1), hora_inicio=time(8, 0),
            data_fim=date(2020, 1, 1), hora_fim=time(10, 0),
            status_agendamento='aprovado'
        )
        self.client.force_authenticate(user=self.admin_user)
        self.client.get(reverse('admin-listar-agendamentos'))
        ag.refresh_from_db()
        self.assertEqual(ag.status_agendamento, 'concluido')

    # Permissões admin

    def test_servidor_nao_acessa_admin_listar_agendamentos(self):
        self.client.force_authenticate(user=self.server_user)
        response = self.client.get(reverse('admin-listar-agendamentos'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_servidor_nao_acessa_admin_atualizar_status(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('admin-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'aprovado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_servidor_nao_acessa_admin_gerenciar_pai(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # Admin GET agendamento pai

    def test_admin_get_agendamento_pai(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id_agendamento_pai'], self.agendamento_pai.id_agendamento_pai)

    # Admin status cancelado

    def test_admin_cancela_agendamento_individual(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_pendente.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pendente.refresh_from_db()
        self.assertEqual(self.agendamento_pendente.status_agendamento, 'cancelado')

    # Status concluído do agendamento pai pelo usuário

    def test_usuario_conclui_pai_altera_filhos_pendentes_e_aprovados(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.patch(url, {'status_agendamento': 'concluido'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pendente.refresh_from_db()
        self.agendamento_aprovado.refresh_from_db()
        self.assertEqual(self.agendamento_pendente.status_agendamento, 'concluido')
        self.assertEqual(self.agendamento_aprovado.status_agendamento, 'concluido')

    def test_usuario_pai_status_invalido_retorna_400(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        response = self.client.patch(url, {'status_agendamento': 'aprovado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Restauração de recurso ao cancelar

    def test_cancelar_pai_restaura_recurso_disponivel(self):
        """Recurso reservado sem outras reservas → volta a disponivel."""
        self.recurso.status_recurso = 'reservado'
        self.recurso.save()
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.status_recurso, 'disponivel')

    def test_cancelar_pai_nao_restaura_recurso_com_outras_reservas(self):
        """Recurso com outra reserva aprovada → permanece reservado."""
        self.recurso.status_recurso = 'reservado'
        self.recurso.save()
        outro_pai = AgendamentoPai.objects.create(id_usuario=self.another_user, id_recurso=self.recurso, id_responsavel=self.another_user)
        Agendamento.objects.create(
            agendamento_pai=outro_pai, data_inicio=date(2025, 12, 1),
            hora_inicio=time(8, 0), data_fim=date(2025, 12, 1), hora_fim=time(10, 0),
            status_agendamento='aprovado'
        )
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.status_recurso, 'reservado')

    # Cancelamento individual de agendamento

    def test_cancelar_agendamento_individual_aprovado(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_aprovado.id_agendamento})
        response = self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_aprovado.refresh_from_db()
        self.assertEqual(self.agendamento_aprovado.status_agendamento, 'cancelado')

    def test_cancelar_agendamento_individual_restaura_recurso(self):
        self.recurso.status_recurso = 'reservado'
        self.recurso.save()
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_aprovado.id_agendamento})
        self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.status_recurso, 'disponivel')

    def test_cancelar_agendamento_individual_nao_restaura_se_outras_reservas(self):
        self.recurso.status_recurso = 'reservado'
        self.recurso.save()
        outro_pai = AgendamentoPai.objects.create(id_usuario=self.another_user, id_recurso=self.recurso, id_responsavel=self.another_user)
        Agendamento.objects.create(
            agendamento_pai=outro_pai, data_inicio=date(2025, 12, 1),
            hora_inicio=time(8, 0), data_fim=date(2025, 12, 1), hora_fim=time(10, 0),
            status_agendamento='aprovado'
        )
        self.client.force_authenticate(user=self.server_user)
        url = reverse('user-atualizar-status-agendamento', kwargs={'id_agendamento': self.agendamento_aprovado.id_agendamento})
        self.client.patch(url, {'status_agendamento': 'cancelado'}, format='json')
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.status_recurso, 'reservado')

    # Disponibilidade com parâmetros inválidos

    def test_disponibilidade_ano_nao_numerico_retorna_400(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('recurso-disponibilidade', kwargs={'recurso_id': self.recurso.id_recurso})
        response = self.client.get(url, {'ano': 'abc', 'mes': '10'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # AdminAgendamentoPaiUpdateSerializer — criar, remover e atualizar filhos

    @patch('booking.views.notificar_admins')
    def test_admin_edita_pai_cria_novo_filho(self, mock_notif):
        """Filho sem id_agendamento é criado como pendente."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        payload = {
            'finalidade': 'Atualizada',
            'id_responsavel': self.admin_user.id_usuario,
            'agendamentos_filhos': [
                {'id_agendamento': self.agendamento_pendente.id_agendamento, 'data_inicio': '2025-10-01', 'hora_inicio': '10:00', 'data_fim': '2025-10-01', 'hora_fim': '12:00'},
                {'data_inicio': '2025-10-05', 'hora_inicio': '08:00', 'data_fim': '2025-10-05', 'hora_fim': '09:00'},
            ]
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        novo_filho = Agendamento.objects.filter(agendamento_pai=self.agendamento_pai, data_inicio=date(2025, 10, 5))
        self.assertTrue(novo_filho.exists())
        self.assertEqual(novo_filho.first().status_agendamento, 'pendente')

    @patch('booking.views.notificar_admins')
    def test_admin_edita_pai_remove_filho_ausente(self, mock_notif):
        """Filhos não incluídos no payload são deletados."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        # Envia apenas o pendente, omite o aprovado → aprovado deve ser deletado
        payload = {
            'finalidade': 'Atualizada',
            'id_responsavel': self.admin_user.id_usuario,
            'agendamentos_filhos': [
                {'id_agendamento': self.agendamento_pendente.id_agendamento, 'data_inicio': '2025-10-01', 'hora_inicio': '10:00', 'data_fim': '2025-10-01', 'hora_fim': '12:00'},
            ]
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Agendamento.objects.filter(pk=self.agendamento_aprovado.pk).exists())

    @patch('booking.views.notificar_admins')
    def test_admin_edita_pai_atualiza_horario_filho(self, mock_notif):
        """Altera horário de um filho existente."""
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        payload = {
            'finalidade': 'Atualizada',
            'id_responsavel': self.admin_user.id_usuario,
            'agendamentos_filhos': [
                {'id_agendamento': self.agendamento_pendente.id_agendamento, 'data_inicio': '2025-10-01', 'hora_inicio': '08:00', 'data_fim': '2025-10-01', 'hora_fim': '09:00'},
            ]
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agendamento_pendente.refresh_from_db()
        self.assertEqual(self.agendamento_pendente.hora_inicio, time(8, 0))

    @patch('booking.views.notificar_admins')
    def test_admin_edita_pai_conflito_retorna_400(self, mock_notif):
        """Conflito de horário na validação do update retorna 400."""
        # Cria agendamento aprovado em outro pai no mesmo recurso
        outro_pai = AgendamentoPai.objects.create(id_usuario=self.another_user, id_recurso=self.recurso, id_responsavel=self.another_user)
        Agendamento.objects.create(
            agendamento_pai=outro_pai, data_inicio=date(2025, 10, 1),
            hora_inicio=time(10, 0), data_fim=date(2025, 10, 1), hora_fim=time(12, 0),
            status_agendamento='aprovado'
        )
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-gerenciar-agendamento-pai', kwargs={'id_agendamento_pai': self.agendamento_pai.id_agendamento_pai})
        payload = {
            'finalidade': 'Conflito',
            'id_responsavel': self.admin_user.id_usuario,
            'agendamentos_filhos': [
                {'data_inicio': '2025-10-01', 'hora_inicio': '10:30', 'data_fim': '2025-10-01', 'hora_fim': '11:30'},
            ]
        }
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # _negar_conflitos_em_massa

    @patch('booking.views.criar_notificacao_resumida_conflito')
    def test_negar_conflitos_lista_vazia_sem_erro(self, mock_notif):
        from booking.views import _negar_conflitos_em_massa
        _negar_conflitos_em_massa([])
        mock_notif.assert_not_called()

    @patch('booking.views.criar_notificacao_resumida_conflito')
    def test_negar_conflitos_agrupa_por_usuario(self, mock_notif):
        """Dois usuários com conflitos recebem notificações separadas."""
        from booking.views import _negar_conflitos_em_massa
        user_a = Usuario.objects.create_user(email='usera@teste.com', nome='User A', id_perfil=self.server_profile)
        user_b = Usuario.objects.create_user(email='userb@teste.com', nome='User B', id_perfil=self.server_profile)
        pai_a = AgendamentoPai.objects.create(id_usuario=user_a, id_recurso=self.recurso, id_responsavel=user_a)
        pai_b = AgendamentoPai.objects.create(id_usuario=user_b, id_recurso=self.recurso, id_responsavel=user_b)
        Agendamento.objects.create(agendamento_pai=pai_a, data_inicio=date(2025, 10, 1), hora_inicio=time(10, 0), data_fim=date(2025, 10, 1), hora_fim=time(12, 0), status_agendamento='pendente')
        Agendamento.objects.create(agendamento_pai=pai_b, data_inicio=date(2025, 10, 1), hora_inicio=time(10, 0), data_fim=date(2025, 10, 1), hora_fim=time(12, 0), status_agendamento='pendente')

        aprovado = self.agendamento_pendente
        aprovado.status_agendamento = 'aprovado'
        aprovado.save()
        _negar_conflitos_em_massa([aprovado])
        self.assertEqual(mock_notif.call_count, 2)

    # __str__ dos modelos

    def test_agendamento_pai_str(self):
        s = str(self.agendamento_pai)
        self.assertIn(str(self.agendamento_pai.id_agendamento_pai), s)

    def test_agendamento_str(self):
        s = str(self.agendamento_pendente)
        self.assertIn('pendente', s)

    def test_recurso_str(self):
        self.assertEqual(str(self.recurso), 'Laboratório de Testes')


class UsoImediatoTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        from user_profile.models import PerfilAcesso
        self.terc_profile = PerfilAcesso.objects.create(nome_perfil='Terceirizado', visibilidade=True)
        self.terc_user = Usuario.objects.create_user(email='terc@teste.com', nome='Terceirizado User', password='pw', id_perfil=self.terc_profile)
        self.recurso = Recurso.objects.create(nome_recurso="Sala Teste", status_recurso="disponivel")

    def test_registrar_uso_imediato(self):
        self.client.force_authenticate(user=self.terc_user)
        url = reverse('uso-imediato')
        data = {'id_recurso': self.recurso.id_recurso, 'duracao_minutos': 60, 'finalidade': 'Manutenção'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UsoImediato.objects.filter(id_usuario=self.terc_user).exists())
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.status_recurso, 'reservado')

    def test_registrar_uso_imediato_recurso_indisponivel(self):
        self.recurso.status_recurso = 'em_manutencao'
        self.recurso.save()
        self.client.force_authenticate(user=self.terc_user)
        url = reverse('uso-imediato')
        data = {'id_recurso': self.recurso.id_recurso, 'duracao_minutos': 60}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_listar_usos_imediatos(self):
        UsoImediato.objects.create(id_usuario=self.terc_user, id_recurso=self.recurso, duracao_minutos=60)
        self.client.force_authenticate(user=self.terc_user)
        url = reverse('uso-imediato')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_finalizar_uso_imediato(self):
        uso = UsoImediato.objects.create(id_usuario=self.terc_user, id_recurso=self.recurso, duracao_minutos=60)
        self.recurso.status_recurso = 'reservado'
        self.recurso.save()
        self.client.force_authenticate(user=self.terc_user)
        url = reverse('finalizar-uso-imediato', kwargs={'id_uso': uso.id_uso})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        uso.refresh_from_db()
        self.assertFalse(uso.ativo)
        self.assertIsNotNone(uso.data_fim)
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.status_recurso, 'disponivel')

    def test_finalizar_uso_imediato_ja_finalizado_retorna_400(self):
        uso = UsoImediato.objects.create(id_usuario=self.terc_user, id_recurso=self.recurso, duracao_minutos=60, ativo=False, data_fim=timezone.now())
        self.client.force_authenticate(user=self.terc_user)
        url = reverse('finalizar-uso-imediato', kwargs={'id_uso': uso.id_uso})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_finalizar_uso_de_outro_usuario_retorna_404(self):
        uso = UsoImediato.objects.create(id_usuario=self.terc_user, id_recurso=self.recurso, duracao_minutos=60)
        self.client.force_authenticate(user=self.server_user)
        url = reverse('finalizar-uso-imediato', kwargs={'id_uso': uso.id_uso})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_uso_imediato_expirado_property(self):
        uso = UsoImediato(
            id_usuario=self.terc_user,
            id_recurso=self.recurso,
            duracao_minutos=60,
            data_inicio=timezone.now() - timedelta(minutes=120),
            ativo=True
        )
        self.assertTrue(uso.expirado)

    def test_uso_imediato_nao_expirado_property(self):
        uso = UsoImediato(
            id_usuario=self.terc_user,
            id_recurso=self.recurso,
            duracao_minutos=120,
            data_inicio=timezone.now(),
            ativo=True
        )
        self.assertFalse(uso.expirado)

    def test_uso_imediato_inativo_nao_expirado(self):
        uso = UsoImediato(
            id_usuario=self.terc_user,
            id_recurso=self.recurso,
            duracao_minutos=1,
            data_inicio=timezone.now() - timedelta(minutes=120),
            ativo=False
        )
        self.assertFalse(uso.expirado)

    def test_uso_imediato_sem_autenticacao_retorna_401(self):
        url = reverse('uso-imediato')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_finalizar_com_outros_usos_ativos_mantem_recurso_reservado(self):
        """Se há outro uso ativo para o mesmo recurso, não libera o recurso."""
        uso1 = UsoImediato.objects.create(id_usuario=self.terc_user, id_recurso=self.recurso, duracao_minutos=60)
        outro_terc = Usuario.objects.create_user(email='terc2@teste.com', nome='Terc 2', id_perfil=self.terc_profile)
        uso2 = UsoImediato.objects.create(id_usuario=outro_terc, id_recurso=self.recurso, duracao_minutos=60)
        self.recurso.status_recurso = 'reservado'
        self.recurso.save()

        self.client.force_authenticate(user=self.terc_user)
        url = reverse('finalizar-uso-imediato', kwargs={'id_uso': uso1.id_uso})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        uso1.refresh_from_db()
        self.assertFalse(uso1.ativo)
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.status_recurso, 'reservado')

    def test_uso_imediato_str(self):
        uso = UsoImediato.objects.create(id_usuario=self.terc_user, id_recurso=self.recurso, duracao_minutos=60)
        s = str(uso)
        self.assertIn('ativo', s)
        uso.finalizar()
        s = str(uso)
        self.assertIn('finalizado', s)

    def test_listar_auto_finaliza_usos_expirados(self):
        uso = UsoImediato.objects.create(
            id_usuario=self.terc_user,
            id_recurso=self.recurso,
            duracao_minutos=1,
        )
        # Retrocede data_inicio manualmente para forçar expiração
        UsoImediato.objects.filter(pk=uso.pk).update(data_inicio=timezone.now() - timedelta(minutes=120))

        self.recurso.status_recurso = 'reservado'
        self.recurso.save()

        self.client.force_authenticate(user=self.terc_user)
        url = reverse('uso-imediato')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        uso.refresh_from_db()
        self.assertFalse(uso.ativo)
        self.recurso.refresh_from_db()
        self.assertEqual(self.recurso.status_recurso, 'disponivel')