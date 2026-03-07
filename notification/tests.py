from django.urls import reverse
from rest_framework import status
from unittest.mock import patch
from login.models import Usuario
from resources.models import Recurso
from booking.models import AgendamentoPai
from .models import Notificacao
from .utils import criar_e_enviar_notificacao
from alocai.test_base import BaseTestCase

class NotificationAPITestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.user2 = Usuario.objects.create_user(email='user2@teste.com', nome='User 2', password='pw', id_perfil=self.server_profile)
        self.notif1 = Notificacao.objects.create(destinatario=self.server_user, mensagem="Sua reserva foi aprovada.", lida=False)
        self.notif2 = Notificacao.objects.create(destinatario=self.server_user, mensagem="Sua reserva foi negada.", lida=True)
        self.notif3 = Notificacao.objects.create(destinatario=self.user2, mensagem="Manutenção no Lab A.", lida=False)

    def test_listar_proprias_notificacoes(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('listar-notificacoes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_marcar_notificacoes_como_lidas(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('marcar-notificacoes-lidas')
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.lida)
        self.assertFalse(Notificacao.objects.filter(destinatario=self.server_user, lida=False).exists())

    def test_deletar_notificacao(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('gerenciar-notificacao', kwargs={'pk': self.notif1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notificacao.objects.filter(pk=self.notif1.pk).exists())

    def test_usuario_nao_pode_acessar_notificacoes_de_outro(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse('gerenciar-notificacao', kwargs={'pk': self.notif1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('notification.utils.threading.Thread')
    def test_utilitario_criar_e_enviar_notificacao(self, mock_thread):
        recurso = Recurso.objects.create(nome_recurso="Recurso para Notif")
        ag_pai = AgendamentoPai.objects.create(id_usuario=self.server_user, id_recurso=recurso, id_responsavel=self.server_user)

        criar_e_enviar_notificacao(self.server_user, ag_pai, "Mensagem de teste")
        
        self.assertTrue(Notificacao.objects.filter(destinatario=self.server_user, mensagem="Mensagem de teste").exists())
        self.assertTrue(mock_thread.called)

    @patch('notification.utils.threading.Thread')
    def test_notificar_admins_cria_notificacao_por_admin(self, mock_thread):
        from notification.utils import notificar_admins
        recurso = Recurso.objects.create(nome_recurso="Recurso Admins")
        ag_pai = AgendamentoPai.objects.create(id_usuario=self.server_user, id_recurso=recurso, id_responsavel=self.server_user)

        notificar_admins(ag_pai, "Nova solicitação")

        self.assertEqual(Notificacao.objects.filter(agendamento_pai=ag_pai).count(), 1)

    @patch('notification.utils.threading.Thread')
    def test_criar_notificacao_resumida_conflito(self, mock_thread):
        from notification.utils import criar_notificacao_resumida_conflito
        from booking.models import Agendamento
        from datetime import date, time
        recurso = Recurso.objects.create(nome_recurso="Recurso Conflito")
        ag_pai = AgendamentoPai.objects.create(id_usuario=self.server_user, id_recurso=recurso, id_responsavel=self.server_user)
        ag1 = Agendamento.objects.create(
            agendamento_pai=ag_pai, data_inicio=date(2025, 12, 1),
            hora_inicio=time(9, 0), data_fim=date(2025, 12, 1),
            hora_fim=time(10, 0), status_agendamento='negado'
        )

        criar_notificacao_resumida_conflito(self.server_user, ag_pai, [ag1])

        self.assertEqual(Notificacao.objects.filter(destinatario=self.server_user, agendamento_pai=ag_pai).count(), 1)

    def test_marcar_notificacao_individual_como_lida(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('marcar-notificacao-lida', kwargs={'pk': self.notif1.pk})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.lida)

    def test_marcar_notificacao_de_outro_usuario_retorna_404(self):
        self.client.force_authenticate(user=self.user2)
        url = reverse('marcar-notificacao-lida', kwargs={'pk': self.notif1.pk})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_listar_notificacoes_sem_autenticacao_retorna_401(self):
        url = reverse('listar-notificacoes')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_deletar_notificacao_sem_autenticacao_retorna_401(self):
        url = reverse('gerenciar-notificacao', kwargs={'pk': self.notif1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Permissões sem autenticação

    def test_marcar_notificacoes_como_lidas_sem_auth_retorna_401(self):
        url = reverse('marcar-notificacoes-lidas')
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_marcar_notificacao_individual_sem_auth_retorna_401(self):
        url = reverse('marcar-notificacao-lida', kwargs={'pk': self.notif1.pk})
        response = self.client.put(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # __str__

    def test_notificacao_str(self):
        s = str(self.notif1)
        self.assertIn(self.server_user.nome, s)
        self.assertIn('aprovada', s)


class NotificationUtilsTestCase(BaseTestCase):
    """Testes das funções utilitárias de notificação."""

    def setUp(self):
        super().setUp()
        self.recurso = Recurso.objects.create(nome_recurso="Recurso Utils")
        self.ag_pai = AgendamentoPai.objects.create(
            id_usuario=self.server_user, id_recurso=self.recurso,
            id_responsavel=self.server_user, finalidade='Aula', observacoes='Obs de teste'
        )

    def test_build_horarios_html_5_ou_menos(self):
        from notification.utils import _build_horarios_html
        from booking.models import Agendamento
        from datetime import date, time
        ags = [
            Agendamento(agendamento_pai=self.ag_pai, data_inicio=date(2025, 1, i+1),
                        hora_inicio=time(8, 0), data_fim=date(2025, 1, i+1), hora_fim=time(10, 0))
            for i in range(3)
        ]
        html = _build_horarios_html(ags)
        self.assertIn('<ul>', html)
        self.assertEqual(html.count('<li>'), 3)

    def test_build_horarios_html_mais_de_5(self):
        from notification.utils import _build_horarios_html
        from booking.models import Agendamento
        from datetime import date, time
        ags = [
            Agendamento(agendamento_pai=self.ag_pai, data_inicio=date(2025, 1, i+1),
                        hora_inicio=time(8, 0), data_fim=date(2025, 1, i+1), hora_fim=time(10, 0))
            for i in range(7)
        ]
        html = _build_horarios_html(ags)
        self.assertNotIn('<ul>', html)
        self.assertIn('7 agendamentos', html)

    def test_build_email_html_com_observacoes(self):
        from notification.utils import _build_email_html
        from booking.models import Agendamento
        from datetime import date, time
        Agendamento.objects.create(
            agendamento_pai=self.ag_pai, data_inicio=date(2025, 1, 1),
            hora_inicio=time(8, 0), data_fim=date(2025, 1, 1), hora_fim=time(10, 0)
        )
        html = _build_email_html(self.ag_pai, 'Teste de mensagem')
        self.assertIn('Obs de teste', html)
        self.assertIn('Aula', html)
        self.assertIn(self.server_user.nome, html)

    def test_build_email_html_sem_observacoes(self):
        from notification.utils import _build_email_html
        from booking.models import Agendamento
        from datetime import date, time
        self.ag_pai.observacoes = None
        self.ag_pai.save()
        Agendamento.objects.create(
            agendamento_pai=self.ag_pai, data_inicio=date(2025, 1, 1),
            hora_inicio=time(8, 0), data_fim=date(2025, 1, 1), hora_fim=time(10, 0)
        )
        html = _build_email_html(self.ag_pai, 'Mensagem')
        self.assertNotIn('Observações', html)

    def test_build_email_html_com_saudacao(self):
        from notification.utils import _build_email_html
        from booking.models import Agendamento
        from datetime import date, time
        Agendamento.objects.create(
            agendamento_pai=self.ag_pai, data_inicio=date(2025, 1, 1),
            hora_inicio=time(8, 0), data_fim=date(2025, 1, 1), hora_fim=time(10, 0)
        )
        html = _build_email_html(self.ag_pai, 'Msg', saudacao='Olá Admin,')
        self.assertIn('Olá Admin,', html)

    @patch('notification.utils._disparar_email')
    def test_criar_e_enviar_notificacao_com_email_host(self, mock_email):
        from django.test import override_settings
        with override_settings(EMAIL_HOST_USER='test@host.com'):
            criar_e_enviar_notificacao(self.server_user, self.ag_pai, 'Msg com email')
        self.assertTrue(Notificacao.objects.filter(mensagem='Msg com email').exists())
        mock_email.assert_called_once()

    @patch('notification.utils._disparar_email')
    def test_criar_e_enviar_notificacao_sem_email_host(self, mock_email):
        from django.test import override_settings
        with override_settings(EMAIL_HOST_USER=''):
            criar_e_enviar_notificacao(self.server_user, self.ag_pai, 'Msg sem email')
        self.assertTrue(Notificacao.objects.filter(mensagem='Msg sem email').exists())
        mock_email.assert_not_called()

    @patch('notification.utils._disparar_email')
    def test_criar_notificacao_resumida_com_email(self, mock_email):
        from notification.utils import criar_notificacao_resumida_conflito
        from booking.models import Agendamento
        from datetime import date, time
        from django.test import override_settings
        ag = Agendamento.objects.create(
            agendamento_pai=self.ag_pai, data_inicio=date(2025, 1, 1),
            hora_inicio=time(8, 0), data_fim=date(2025, 1, 1), hora_fim=time(10, 0),
            status_agendamento='negado'
        )
        with override_settings(EMAIL_HOST_USER='test@host.com'):
            criar_notificacao_resumida_conflito(self.server_user, self.ag_pai, [ag])
        mock_email.assert_called_once()