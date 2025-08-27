from rest_framework import generics, permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from user_profile.permissions import IsServidor, IsAdministrador
from .models import Agendamento, AgendamentoPai
from .serializers import AgendamentoPaiCreateSerializer, ListarAgendamentosSerializer, AgendamentoPaiDetailSerializer

class ListarAgendamentosView(generics.ListAPIView):
    serializer_class = ListarAgendamentosSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Agendamento.objects.filter(agendamento_pai__id_usuario=user).order_by('-data_inicio')

class CriarAgendamentoView(generics.CreateAPIView):
    queryset = AgendamentoPai.objects.all()
    serializer_class = AgendamentoPaiCreateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsServidor | IsAdministrador]

    def perform_create(self, serializer):
        serializer.save(id_usuario=self.request.user)

class AgendamentoPaiDetailView(generics.RetrieveAPIView):
    """
    Endpoint para retornar os detalhes completos de um agendamento pai,
    incluindo todos os seus filhos.
    """
    queryset = AgendamentoPai.objects.all()
    serializer_class = AgendamentoPaiDetailSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id_agendamento_pai'

    def get_queryset(self):
        return AgendamentoPai.objects.filter(id_usuario=self.request.user)