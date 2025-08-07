# from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from resource.models import Recurso
from .models import Agendamento

class AgendamentoAPITestCase(APITestCase):

    def setUp(self):
        # Cria um usuário de teste com o modelo padrão do Django
        self.user = User.objects.create_user(
            username="teste@exemplo.com",
            email="teste@exemplo.com",
            password="password123"
        )
        self.recurso = Recurso.objects.create(
            nome_recurso="Laboratório de Testes",
            status_recurso="disponivel"
        )
        
    def test_criar_agendamento_com_sucesso(self):
        # Faz o login do usuário de teste no cliente da API
        self.client.force_authenticate(user=self.user)
        url = reverse('criar-agendamento')
        data = {
            "id_recurso": self.recurso.id_recurso,
            "data_inicio": "2025-10-20",
            "hora_inicio": "09:00:00",
            "data_fim": "2025-10-20",
            "hora_fim": "11:00:00",
            "status_agendamento": "Pendente",
            "finalidade": "Teste de API",
            "id_responsavel": 1
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        agendamento_criado = Agendamento.objects.get(pk=response.data['id_agendamento'])
        self.assertEqual(agendamento_criado.id_usuario, self.user)

    def test_nao_permite_criar_agendamento_sem_autenticacao(self):
        # Verifica se um usuário não logado recebe o erro correto
        # Desloga o cliente
        self.client.force_authenticate(user=None)
        url = reverse('criar-agendamento')
        data = {"id_recurso": 1, "data_inicio": "2025-11-01"}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)