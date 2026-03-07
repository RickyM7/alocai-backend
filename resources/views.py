from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Recurso, StatusRecurso
from .serializers import RecursoSerializer, DashboardRecursoSerializer
from rest_framework.permissions import AllowAny
from user_profile.permissions import IsAdministrador
from booking.models import Agendamento
from booking.serializers import PublicAgendamentoSerializer

class RecursoListView(generics.ListAPIView):
    """
    Endpoint para listar todos os recursos disponíveis para agendamento.
    Requer apenas autenticação.
    """
    serializer_class = RecursoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Auto-finaliza recursos de uso imediato expirados
        from booking.models import UsoImediato
        usos_expirados = UsoImediato.objects.select_related('id_recurso').filter(
            ativo=True
        )
        for uso in usos_expirados:
            if uso.expirado:
                uso.finalizar()

        return Recurso.objects.filter(status_recurso=StatusRecurso.DISPONIVEL).order_by('nome_recurso')

class RecursoAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento administrativo de recursos.
    Requer autenticação e permissões de administrador.
    """
    queryset = Recurso.objects.all()
    serializer_class = RecursoSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdministrador]
    
    def get_queryset(self):
        queryset = Recurso.objects.all()
        status_recurso = self.request.query_params.get('status', None)
        if status_recurso:
            queryset = queryset.filter(status_recurso=status_recurso)
        return queryset.order_by('nome_recurso')
    
    @action(detail=True, methods=['post'])
    def alterar_status(self, request, pk=None):
        recurso = self.get_object()
        novo_status = request.data.get('status')
        status_validos = [choice[0] for choice in StatusRecurso.choices]

        if not novo_status:
            return Response(
                {"erro": "O campo 'status' é obrigatório"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if novo_status not in status_validos:
            return Response(
                {"erro": f"Status inválido. Opções: {', '.join(status_validos)}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        recurso.status_recurso = novo_status
        recurso.save(update_fields=['status_recurso'])

        return Response({
            "mensagem": f"Status do recurso atualizado para '{novo_status}' com sucesso",
            "recurso": RecursoSerializer(recurso).data
        })
    
    @action(detail=False, methods=['get'])
    def status_disponiveis(self, request):
        return Response({
            "status_disponiveis": [choice[0] for choice in StatusRecurso.choices]
        })

class DashboardView(generics.ListAPIView):
    """
    Endpoint para a visualização do dashboard
    (mostra recursos e os agendamentos aprovados)
    """
    serializer_class = DashboardRecursoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Recurso.objects.all().order_by('nome_recurso')

class CalendarAgendamentosView(generics.ListAPIView):
    """
    Endpoint que retorna todos os agendamentos aprovados
    para serem exibidos no calendário do dashboard
    """
    queryset = Agendamento.objects.filter(status_agendamento='aprovado').order_by('data_inicio')
    serializer_class = PublicAgendamentoSerializer
    permission_classes = [AllowAny]

class RecursoAgendamentosView(generics.ListAPIView):
    """
    Endpoint que retorna os agendamentos aprovados de um recurso
    """
    serializer_class = PublicAgendamentoSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        recurso_id = self.kwargs.get('id_recurso')
        return Agendamento.objects.filter(
            agendamento_pai__id_recurso=recurso_id,
            status_agendamento='aprovado'
        ).order_by('data_inicio')
