from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import Recurso
from .serializers import RecursoSerializer, DashboardRecursoSerializer
from rest_framework.permissions import AllowAny

class RecursoListView(generics.ListAPIView):
    """
    Endpoint para listar todos os recursos disponíveis para agendamento.
    Requer apenas autenticação.
    """
    queryset = Recurso.objects.all().order_by('nome_recurso')
    serializer_class = RecursoSerializer
    permission_classes = [permissions.IsAuthenticated]

class RecursoAdminViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento administrativo de recursos.
    Requer autenticação e permissões de administrador.
    """
    queryset = Recurso.objects.all()
    serializer_class = RecursoSerializer
    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]
    
    def get_queryset(self):
        """
        Filtra os recursos com base nos parâmetros de consulta.
        """
        queryset = Recurso.objects.all()
        status_recurso = self.request.query_params.get('status', None)
        
        if status_recurso:
            queryset = queryset.filter(status_recurso=status_recurso)
            
        return queryset.order_by('nome_recurso')
    
    @action(detail=True, methods=['post'])
    def alterar_status(self, request, pk=None):
        """
        Ação personalizada para alterar o status de um recurso.
        """
        recurso = self.get_object()
        novo_status = request.data.get('status')
        
        if not novo_status:
            return Response(
                {"erro": "O campo 'status' é obrigatório"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        recurso.status_recurso = novo_status
        recurso.save()
        
        return Response({
            "mensagem": f"Status do recurso atualizado para '{novo_status}' com sucesso",
            "recurso": RecursoSerializer(recurso).data
        })
    
    @action(detail=False, methods=['get'])
    def status_disponiveis(self, request):
        """
        Retorna a lista de status disponíveis para os recursos.
        """
        return Response({
            "status_disponiveis": [
                'disponivel', 
                'em_manutencao', 
                'indisponivel', 
                'reservado'
            ]
        })

class DashboardView(generics.ListAPIView):
    """
    Endpoint para a visualização do dashboard
    (mostra recursos e os agendamentos aprovados)
    """
    queryset = Recurso.objects.filter(status_recurso='disponivel').order_by('nome_recurso')
    serializer_class = DashboardRecursoSerializer
    permission_classes = [AllowAny]