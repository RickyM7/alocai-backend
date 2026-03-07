from django.urls import reverse
from rest_framework import status
from .models import Recurso
from alocai.test_base import BaseTestCase

class ResourcesAPITestCase(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.recurso1 = Recurso.objects.create(nome_recurso="Laboratório A", status_recurso="disponivel")
        self.recurso2 = Recurso.objects.create(nome_recurso="Sala de Reunião B", status_recurso="em_manutencao")

    def test_admin_cria_recurso(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-list')
        data = {"nome_recurso": "Projetor", "status_recurso": "disponivel"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_servidor_nao_pode_criar_recurso(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('recurso-admin-list')
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_listar_recursos_para_usuario_logado(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('listar-recursos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_admin_lista_todos_recursos(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_admin_atualiza_recurso(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-detail', kwargs={'pk': self.recurso1.pk})
        data = {'nome_recurso': 'Laboratório A Renovado', 'status_recurso': 'disponivel'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recurso1.refresh_from_db()
        self.assertEqual(self.recurso1.nome_recurso, 'Laboratório A Renovado')

    def test_admin_deleta_recurso(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-detail', kwargs={'pk': self.recurso1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Recurso.objects.filter(pk=self.recurso1.pk).exists())
        
    def test_action_alterar_status_recurso(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-alterar-status', kwargs={'pk': self.recurso1.pk})
        response = self.client.post(url, {'status': 'em_manutencao'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recurso1.refresh_from_db()
        self.assertEqual(self.recurso1.status_recurso, 'em_manutencao')
        
    def test_action_status_disponiveis(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-status-disponiveis')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('status_disponiveis', response.data)
        self.assertIsInstance(response.data['status_disponiveis'], list)

    def test_dashboard_acessivel_sem_autenticacao(self):
        """Dashboard é público — qualquer um pode acessar."""
        url = reverse('dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_dashboard_calendar_acessivel_sem_autenticacao(self):
        """Calendar do dashboard é público — qualquer um pode acessar."""
        url = reverse('dashboard-calendar')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_recurso_agendamentos_publico(self):
        """Endpoint de agendamentos de um recurso é público."""
        from booking.models import AgendamentoPai, Agendamento
        from login.models import Usuario
        from datetime import date, time
        user = Usuario.objects.create_user(email='tmp@t.com', nome='Tmp')
        pai = AgendamentoPai.objects.create(id_usuario=user, id_recurso=self.recurso1, id_responsavel=user)
        Agendamento.objects.create(
            agendamento_pai=pai, data_inicio=date(2025, 11, 1),
            hora_inicio=time(9, 0), data_fim=date(2025, 11, 1),
            hora_fim=time(10, 0), status_agendamento='aprovado'
        )
        url = reverse('recurso-agendamentos', kwargs={'id_recurso': self.recurso1.id_recurso})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_recurso_agendamentos_sem_dados(self):
        """Recurso sem agendamentos aprovados retorna lista vazia."""
        url = reverse('recurso-agendamentos', kwargs={'id_recurso': self.recurso1.id_recurso})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_admin_filtra_recursos_por_status(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-list')
        response = self.client.get(url, {'status': 'disponivel'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nome_recurso'], 'Laboratório A')

    def test_admin_filtra_recursos_por_status_manutencao(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-list')
        response = self.client.get(url, {'status': 'em_manutencao'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['nome_recurso'], 'Sala de Reunião B')

    def test_admin_alterar_status_sem_status_retorna_400(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-alterar-status', kwargs={'pk': self.recurso1.pk})
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_alterar_status_invalido_retorna_400(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-alterar-status', kwargs={'pk': self.recurso1.pk})
        response = self.client.post(url, {'status': 'inexistente'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_servidor_nao_pode_deletar_recurso(self):
        self.client.force_authenticate(user=self.server_user)
        url = reverse('recurso-admin-detail', kwargs={'pk': self.recurso1.pk})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_sem_autenticacao_nao_lista_recursos_privados(self):
        url = reverse('listar-recursos')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Auto-finalização de usos imediatos expirados

    def test_listar_recursos_auto_finaliza_uso_imediato_expirado(self):
        """Uso imediato expirado é finalizado e recurso liberado ao listar."""
        from booking.models import UsoImediato
        from login.models import Usuario
        from user_profile.models import PerfilAcesso
        from datetime import timedelta
        from django.utils import timezone

        terc_profile = PerfilAcesso.objects.create(nome_perfil='Terceirizado', visibilidade=True)
        terc_user = Usuario.objects.create_user(email='terc_res@teste.com', nome='Terc', id_perfil=terc_profile)
        uso = UsoImediato.objects.create(id_usuario=terc_user, id_recurso=self.recurso1, duracao_minutos=1)
        UsoImediato.objects.filter(pk=uso.pk).update(data_inicio=timezone.now() - timedelta(minutes=120))
        self.recurso1.status_recurso = 'reservado'
        self.recurso1.save()

        self.client.force_authenticate(user=self.server_user)
        response = self.client.get(reverse('listar-recursos'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        uso.refresh_from_db()
        self.assertFalse(uso.ativo)
        self.recurso1.refresh_from_db()
        self.assertEqual(self.recurso1.status_recurso, 'disponivel')

    # PATCH parcial de recurso

    def test_admin_patch_recurso_parcial(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-detail', kwargs={'pk': self.recurso1.pk})
        response = self.client.patch(url, {'descricao': 'Nova desc'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.recurso1.refresh_from_db()
        self.assertEqual(self.recurso1.descricao, 'Nova desc')
        self.assertEqual(self.recurso1.nome_recurso, 'Laboratório A')

    # Validação de status no serializer

    def test_admin_cria_recurso_com_status_invalido_retorna_400(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('recurso-admin-list')
        data = {"nome_recurso": "Teste", "status_recurso": "inexistente"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # __str__

    def test_recurso_str(self):
        self.assertEqual(str(self.recurso1), 'Laboratório A')

    # PerfilAcesso __str__

    def test_perfil_acesso_str(self):
        from user_profile.models import PerfilAcesso
        perfil = PerfilAcesso.objects.get(nome_perfil='Servidor')
        self.assertEqual(str(perfil), 'Servidor')