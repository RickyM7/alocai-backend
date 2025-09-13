from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from user_profile.permissions import IsServidor, IsAdministrador
from .models import Agendamento, AgendamentoPai
from .serializers import (
    AgendamentoPaiCreateSerializer, ListarAgendamentosSerializer, 
    AgendamentoPaiDetailSerializer, AdminAgendamentoSerializer, 
    AdminAgendamentoPaiSerializer, AdminAgendamentoPaiUpdateSerializer
)
from collections import defaultdict
from datetime import datetime
from django.utils import timezone

class ListarAgendamentosView(generics.ListAPIView):
    """
    Endpoint para o usuário listar suas solicitações de agendamento,
    agrupadas por AgendamentoPai
    """
    serializer_class = AdminAgendamentoPaiSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        now = timezone.localtime()

        agendamentos_aprovados_expirados = Agendamento.objects.filter(
            agendamento_pai__id_usuario=user,
            status_agendamento='aprovado',
            data_fim__lt=now.date()
        )
        agendamentos_aprovados_expirados_hoje = Agendamento.objects.filter(
            agendamento_pai__id_usuario=user,
            status_agendamento='aprovado',
            data_fim=now.date(),
            hora_fim__lt=now.time()
        )
        (agendamentos_aprovados_expirados | agendamentos_aprovados_expirados_hoje).update(status_agendamento='concluido')
        
        agendamentos_pendentes_expirados = Agendamento.objects.filter(
            agendamento_pai__id_usuario=user,
            status_agendamento='pendente',
            data_fim__lt=now.date()
        )
        agendamentos_pendentes_expirados_hoje = Agendamento.objects.filter(
            agendamento_pai__id_usuario=user,
            status_agendamento='pendente',
            data_fim=now.date(),
            hora_fim__lt=now.time()
        )
        (agendamentos_pendentes_expirados | agendamentos_pendentes_expirados_hoje).update(status_agendamento='negado')

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
    serializer_class = AdminAgendamentoPaiSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdministrador]

    def get_queryset(self):
        now = timezone.localtime()

        agendamentos_aprovados_expirados = Agendamento.objects.filter(
            status_agendamento='aprovado',
            data_fim__lt=now.date()
        )
        agendamentos_aprovados_expirados_hoje = Agendamento.objects.filter(
            status_agendamento='aprovado',
            data_fim=now.date(),
            hora_fim__lt=now.time()
        )
        (agendamentos_aprovados_expirados | agendamentos_aprovados_expirados_hoje).update(status_agendamento='concluido')
        
        agendamentos_pendentes_expirados = Agendamento.objects.filter(
            status_agendamento='pendente',
            data_fim__lt=now.date()
        )
        agendamentos_pendentes_expirados_hoje = Agendamento.objects.filter(
            status_agendamento='pendente',
            data_fim=now.date(),
            hora_fim__lt=now.time()
        )
        (agendamentos_pendentes_expirados | agendamentos_pendentes_expirados_hoje).update(status_agendamento='negado')

        return AgendamentoPai.objects.prefetch_related('agendamentos_filhos').order_by('-data_criacao')

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
            return Response({"error": "Status inválido. Use 'aprovado' ou 'negado'."}, status=status.HTTP_400_BAD_REQUEST)
        
        instance.status_agendamento = novo_status
        instance.gerenciado_por = request.user
        instance.save()
        
        if novo_status == 'negado' and instance.agendamento_pai:
            instance.agendamento_pai.agendamentos_filhos.exclude(pk=instance.pk).update(status_agendamento='negado', gerenciado_por=request.user)

        return Response(self.get_serializer(instance).data)

class AdminAgendamentoPaiManageView(generics.RetrieveUpdateDestroyAPIView):
    """
    Endpoint para o administrador gerenciar um agendamento pai:
    - Aprovar/negar todos os filhos (PUT)
    - Deletar a solicitação inteira (DELETE)
    """
    queryset = AgendamentoPai.objects.all()
    permission_classes = [IsAdministrador]
    lookup_field = 'id_agendamento_pai'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            if 'finalidade' in self.request.data:
                 return AdminAgendamentoPaiUpdateSerializer
            return AdminAgendamentoPaiSerializer
        return AdminAgendamentoPaiSerializer

    def update(self, request, *args, **kwargs):
        if "status_agendamento" in request.data:
            instance = self.get_object()
            novo_status = request.data.get("status_agendamento")

            if novo_status not in ['aprovado', 'negado']:
                return Response(
                    {"error": "Status inválido. Use 'aprovado' ou 'negado'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            instance.agendamentos_filhos.update(status_agendamento=novo_status, gerenciado_por=request.user)
            instance.refresh_from_db()
            serializer = AdminAgendamentoPaiSerializer(instance)
            return Response(serializer.data)
        
        return super().update(request, *args, **kwargs)

class UserAgendamentoPaiStatusUpdateView(generics.UpdateAPIView):
    """
    Endpoint para um usuário marcar sua própria reserva como concluída
    """
    serializer_class = AgendamentoPaiDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id_agendamento_pai'

    def get_queryset(self):
        return AgendamentoPai.objects.filter(id_usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        novo_status = request.data.get("status_agendamento")

        if novo_status != 'concluido':
            return Response({"error": "Status inválido. Apenas 'concluido' é permitido por esta rota."}, status=status.HTTP_400_BAD_REQUEST)

        instance.agendamentos_filhos.update(status_agendamento=novo_status)
        recurso = instance.id_recurso
        outras_reservas_ativas = Agendamento.objects.filter(
            agendamento_pai__id_recurso=recurso,
            status_agendamento='aprovado'
        ).exists()

        if not outras_reservas_ativas:
            recurso.status_recurso = 'disponivel'
            recurso.save()

        instance.refresh_from_db()
        return Response(self.get_serializer(instance).data)

class UserAgendamentoStatusUpdateView(generics.UpdateAPIView):
    """
    Endpoint para um usuário marcar um de seus próprios agendamentos como concluído
    """
    serializer_class = AdminAgendamentoSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id_agendamento'

    def get_queryset(self):
        return Agendamento.objects.filter(agendamento_pai__id_usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        novo_status = request.data.get("status_agendamento")

        if novo_status != 'concluido':
            return Response({"error": "Ação não permitida. Apenas 'concluido' é válido."}, status=status.HTTP_400_BAD_REQUEST)

        instance.status_agendamento = novo_status
        instance.save()
        
        recurso = instance.agendamento_pai.id_recurso
        outras_reservas_ativas = Agendamento.objects.filter(
            agendamento_pai__id_recurso=recurso,
            status_agendamento='aprovado'
        ).exists()

        if not outras_reservas_ativas:
            recurso.status_recurso = 'disponivel'
            recurso.save()

        return Response(self.get_serializer(instance).data)

class RecursoDisponibilidadeView(APIView):
    """
    Retorna os intervalos de horários já agendados e aprovados para um recurso
    em um mês/ano específico.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, recurso_id):
        try:
            ano = int(request.query_params.get('ano'))
            mes = int(request.query_params.get('mes'))
        except (TypeError, ValueError):
            return Response({'error': 'Parâmetros "ano" e "mes" são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            agendamentos_aprovados = Agendamento.objects.filter(
                agendamento_pai__id_recurso=recurso_id,
                data_inicio__year=ano,
                data_inicio__month=mes,
                status_agendamento='aprovado'
            ).values('data_inicio', 'hora_inicio', 'hora_fim')

            booked_slots = defaultdict(list)
            for agendamento in agendamentos_aprovados:
                data_str = agendamento['data_inicio'].strftime('%Y-%m-%d')
                booked_slots[data_str].append({
                    'start': agendamento['hora_inicio'].strftime('%H:%M'),
                    'end': agendamento['hora_fim'].strftime('%H:%M')
                })

            return Response(booked_slots)
        except Exception as e:
            return Response({'error': f'Ocorreu um erro interno: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)