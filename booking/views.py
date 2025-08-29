from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from user_profile.permissions import IsServidor, IsAdministrador
from .models import Agendamento, AgendamentoPai
from .serializers import AgendamentoPaiCreateSerializer, ListarAgendamentosSerializer, AgendamentoPaiDetailSerializer, AdminAgendamentoSerializer

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


# Views do ADM
class AdminAgendamentoListView(generics.ListAPIView):
    """
    Endpoint para o administrador listar todas as solicitações de agendamento
    """
    queryset = Agendamento.objects.all().order_by('-agendamento_pai__data_criacao')
    serializer_class = AdminAgendamentoSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdministrador]

class AdminAgendamentoStatusUpdateView(generics.UpdateAPIView):
    """
    Endpoint para o administrador aprovar ou negar uma solicitação
    """
    queryset = Agendamento.objects.all()
    serializer_class = AdminAgendamentoSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdministrador]
    lookup_field = 'id_agendamento'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        novo_status = request.data.get("status_agendamento")

        if novo_status not in ['aprovado', 'negado']:
            return Response(
                {"error": "Status inválido. Use 'aprovado' ou 'negado'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        instance.status_agendamento = novo_status
        instance.save()

        # Atualiza todos os filhos do mesmo pai se o status for 'negado'
        if novo_status == 'negado' and instance.agendamento_pai:
            instance.agendamento_pai.agendamentos_filhos.exclude(pk=instance.pk).update(status_agendamento='negado')

        return Response(self.get_serializer(instance).data)