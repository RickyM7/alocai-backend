# from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from login.models import Usuario
from resource.models import Recurso
from .models import Agendamento

class AgendamentoAPITestCase(APITestCase):

    def setUp(self):

        # Cria um usuário de teste
        self.user = Usuario.objects.create(
            nome="Usuário de Teste",
            email="teste@exemplo.com",
            status_conta="ativo",
            senha_hash="test"
        )

        # Cria um recurso de teste
        self.recurso = Recurso.objects.create(
            nome_recurso="Laboratório de Testes",
            status_recurso="disponivel"
        )
        
        # Faz o login do usuário de teste no cliente da API
        self.client.force_authenticate(user=self.user)

    def test_criar_agendamento_com_sucesso(self):
        # Verifica se um usuário autenticado pode criar um agendamento
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

        self.assertTrue(Agendamento.objects.filter(finalidade="Teste de API").exists())

        agendamento_criado = Agendamento.objects.get(finalidade="Teste de API")
        self.assertEqual(agendamento_criado.id_usuario, self.user)
        print("Teste de criação de agendamento passou com sucesso!")

    def test_nao_permite_criar_agendamento_sem_autenticacao(self):
        # Verifica se um usuário não logado recebe o erro correto
        # Desloga o cliente
        self.client.force_authenticate(user=None)

        url = reverse('criar-agendamento')
        data = { "id_recurso": 1, "data_inicio": "2025-11-01" }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        print("Teste de bloqueio de usuário não autenticado passou!")
