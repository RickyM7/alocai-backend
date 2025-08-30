from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from user_profile.permissions import IsServidor, IsAdministrador
from .models import Agendamento, AgendamentoPai
from resource.models import Recurso
from .serializers import AgendamentoPaiCreateSerializer, ListarAgendamentosSerializer, AgendamentoPaiDetailSerializer, AdminAgendamentoSerializer, AdminAgendamentoPaiSerializer

class ListarAgendamentosView(generics.ListAPIView):
    """
    Endpoint para o usuário listar suas solicitações de agendamento,
    agrupadas por AgendamentoPai
    """
    serializer_class = AdminAgendamentoPaiSerializer # Reutiliza o serializer do adm
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return AgendamentoPai.objects.filter(id_usuario=user).prefetch_related('agendamentos_filhos').order_by('-data_criacao')

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

class AdminAgendamentoListView(generics.ListAPIView):
    """
    Endpoint para o administrador listar todas as solicitações de agendamento, agrupadas por AgendamentoPai
    """
    queryset = AgendamentoPai.objects.prefetch_related('agendamentos_filhos').order_by('-data_criacao')
    serializer_class = AdminAgendamentoPaiSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdministrador]

class AdminAgendamentoStatusUpdateView(generics.UpdateAPIView):
    """
    Endpoint para o administrador aprovar ou negar uma solicitação individual
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

        # Se aprovado, marca o recurso como reservado
        if novo_status == 'aprovado' and instance.agendamento_pai:
            recurso = instance.agendamento_pai.id_recurso
            recurso.status_recurso = 'reservado'
            recurso.save()
        
        # Se negado, atualiza todos os filhos do mesmo pai
        if novo_status == 'negado' and instance.agendamento_pai:
            instance.agendamento_pai.agendamentos_filhos.exclude(pk=instance.pk).update(status_agendamento='negado')

        return Response(self.get_serializer(instance).data)

class AdminAgendamentoPaiStatusUpdateView(generics.UpdateAPIView):
    """
    Endpoint para o administrador aprovar ou negar todas as solicitações
    de um agendamento pai
    """
    queryset = AgendamentoPai.objects.all()
    serializer_class = AdminAgendamentoPaiSerializer
    permission_classes = [IsAdministrador]
    lookup_field = 'id_agendamento_pai'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        novo_status = request.data.get("status_agendamento")

        if novo_status not in ['aprovado', 'negado']:
            return Response(
                {"error": "Status inválido. Use 'aprovado' ou 'negado'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atualiza todos os filhos de uma vez
        instance.agendamentos_filhos.update(status_agendamento=novo_status)

        # Se aprovado, marca o recurso como reservado
        if novo_status == 'aprovado':
            recurso = instance.id_recurso
            recurso.status_recurso = 'reservado'
            recurso.save()

        # Recarrega a instância para retornar os dados atualizados
        instance.refresh_from_db()

        return Response(self.get_serializer(instance).data)

class UserAgendamentoPaiStatusUpdateView(generics.UpdateAPIView):
    """
    Endpoint para um usuário marcar sua própria reserva como concluída
    """
    serializer_class = AgendamentoPaiDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id_agendamento_pai'

    def get_queryset(self):
        # Garante que os usuários só possam modificar suas próprias reservas
        return AgendamentoPai.objects.filter(id_usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        novo_status = request.data.get("status_agendamento")

        if novo_status != 'concluido':
            return Response(
                {"error": "Status inválido. Apenas 'concluido' é permitido por esta rota."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Marca todos os agendamentos filhos como 'concluido'
        instance.agendamentos_filhos.update(status_agendamento=novo_status)

        # Verifica se o recurso deve ser liberado
        recurso = instance.id_recurso
        # Procura por outras reservas ativas ('aprovado') para este mesmo recurso
        outras_reservas_ativas = Agendamento.objects.filter(
            agendamento_pai__id_recurso=recurso,
            status_agendamento='aprovado'
        ).exists()

        # Se não houver outras reservas ativas, o recurso volta a ficar disponível
        if not outras_reservas_ativas:
            recurso.status_recurso = 'disponivel'
            recurso.save()

        instance.refresh_from_db()
        return Response(self.get_serializer(instance).data)

class UserAgendamentoStatusUpdateView(generics.UpdateAPIView):
    """
    Endpoint para um usuário marcar um de seus próprios agendamentos como concluído
    """
    serializer_class = AdminAgendamentoSerializer # Reutiliza um serializer simples
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id_agendamento'

    def get_queryset(self):
        # Garante que o usuário só possa modificar seus próprios agendamentos
        return Agendamento.objects.filter(agendamento_pai__id_usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        novo_status = request.data.get("status_agendamento")

        if novo_status != 'concluido':
            return Response(
                {"error": "Ação não permitida. Apenas 'concluido' é válido."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Atualiza o status do agendamento filho
        instance.status_agendamento = novo_status
        instance.save()
        
        # Lógica para liberar o recurso se necessário
        recurso = instance.agendamento_pai.id_recurso
        outras_reservas_ativas = Agendamento.objects.filter(
            agendamento_pai__id_recurso=recurso,
            status_agendamento='aprovado'
        ).exists()

        if not outras_reservas_ativas:
            recurso.status_recurso = 'disponivel'
            recurso.save()

        return Response(self.get_serializer(instance).data)