# from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from .models import Agendamento
from .serializers import AgendamentoSerializer

class CriarAgendamentoView(generics.CreateAPIView):
    # Endpoint para criar um novo agendamento
    # Apenas usuários autenticados podem criar agendamentos
    queryset = Agendamento.objects.all()
    serializer_class = AgendamentoSerializer

    # Apenas usuários autenticados possam acessar
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        # Associa automaticamente o agendamento ao usuário que fez a requisição
        # Isso aqui tem que mudar (se necessário) pra quando a parte de persistência for implementada
        serializer.save(id_usuario=self.request.user)