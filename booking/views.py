from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q
from django.db import transaction
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
from notification.utils import criar_e_enviar_notificacao, notificar_admins, criar_notificacao_resumida_conflito

def _verificar_e_negar_conflitos(agendamento_aprovado):
    """
    Função auxiliar para encontrar e negar agendamentos pendentes que conflitam
    com um agendamento recém-aprovado
    """
    recurso = agendamento_aprovado.agendamento_pai.id_recurso
    data_inicio = agendamento_aprovado.data_inicio
    hora_inicio = agendamento_aprovado.hora_inicio
    hora_fim = agendamento_aprovado.hora_fim

    conflitos = Agendamento.objects.select_related('agendamento_pai', 'agendamento_pai__id_usuario').filter(
        agendamento_pai__id_recurso=recurso,
        data_inicio=data_inicio,
        hora_inicio__lt=hora_fim,
        hora_fim__gt=hora_inicio,
        status_agendamento='pendente'
    ).exclude(id_agendamento=agendamento_aprovado.id_agendamento)

    if conflitos.exists():
        conflitos_ids = list(conflitos.values_list('id_agendamento', flat=True))
        Agendamento.objects.filter(id_agendamento__in=conflitos_ids).update(status_agendamento='negado')

        for ag_conflitante in conflitos:
            ag_pai_conflitante = ag_conflitante.agendamento_pai
            mensagem = (f"Seu agendamento para '{recurso.nome_recurso}' no dia "
                        f"{data_inicio.strftime('%d/%m/%Y')} foi negado devido a um conflito de horário.")
            criar_e_enviar_notificacao(ag_pai_conflitante.id_usuario, ag_pai_conflitante, mensagem)

def _negar_conflitos_em_massa(agendamentos_aprovados):
    """
    Encontra todos os conflitos para uma lista de agendamentos aprovados,
    agrupa por usuário e envia uma única notificação de resumo
    """
    if not agendamentos_aprovados:
        return

    recurso = agendamentos_aprovados[0].agendamento_pai.id_recurso
    
    condicoes_conflito = Q()
    for ag in agendamentos_aprovados:
        condicoes_conflito |= Q(
            data_inicio=ag.data_inicio,
            hora_inicio__lt=ag.hora_fim,
            hora_fim__gt=ag.hora_inicio
        )

    conflitos_qs = Agendamento.objects.select_related('agendamento_pai', 'agendamento_pai__id_usuario').filter(
        condicoes_conflito,
        agendamento_pai__id_recurso=recurso,
        status_agendamento='pendente'
    ).exclude(id_agendamento__in=[a.id_agendamento for a in agendamentos_aprovados])
    
    if not conflitos_qs.exists():
        return

    conflitos_agrupados = defaultdict(list)
    for conflito in conflitos_qs:
        conflitos_agrupados[conflito.agendamento_pai].append(conflito)

    ids_para_negar = list(conflitos_qs.values_list('id_agendamento', flat=True))
    Agendamento.objects.filter(id_agendamento__in=ids_para_negar).update(status_agendamento='negado')

    for ag_pai, agendamentos_negados in conflitos_agrupados.items():
        criar_notificacao_resumida_conflito(ag_pai.id_usuario, ag_pai, agendamentos_negados)


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

        agendamentos_aprovados_expirados_filter = Q(
            agendamento_pai__id_usuario=user,
            status_agendamento='aprovado'
        ) & (Q(data_fim__lt=now.date()) | Q(data_fim=now.date(), hora_fim__lt=now.time()))
        
        Agendamento.objects.filter(agendamentos_aprovados_expirados_filter).update(status_agendamento='concluido')
        
        agendamentos_pendentes_expirados_filter = Q(
            agendamento_pai__id_usuario=user,
            status_agendamento='pendente'
        ) & (Q(data_fim__lt=now.date()) | Q(data_fim=now.date(), hora_fim__lt=now.time()))
        
        Agendamento.objects.filter(agendamentos_pendentes_expirados_filter).update(status_agendamento='negado')

        return AgendamentoPai.objects.filter(id_usuario=user).select_related('id_recurso', 'id_usuario', 'id_responsavel').prefetch_related('agendamentos_filhos').order_by('-data_criacao')

class CriarAgendamentoView(generics.CreateAPIView):
    queryset = AgendamentoPai.objects.all()
    serializer_class = AgendamentoPaiCreateSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsServidor | IsAdministrador]

    def perform_create(self, serializer):
        agendamento_pai = serializer.save(id_usuario=self.request.user)
        mensagem = f"Nova solicitação de agendamento para o recurso '{agendamento_pai.id_recurso.nome_recurso}' por {self.request.user.nome}."
        notificar_admins(agendamento_pai, mensagem)

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

        agendamentos_aprovados_expirados_filter = Q(status_agendamento='aprovado') & (
            Q(data_fim__lt=now.date()) | Q(data_fim=now.date(), hora_fim__lt=now.time())
        )
        Agendamento.objects.filter(agendamentos_aprovados_expirados_filter).update(status_agendamento='concluido')
        
        agendamentos_pendentes_expirados_filter = Q(status_agendamento='pendente') & (
            Q(data_fim__lt=now.date()) | Q(data_fim=now.date(), hora_fim__lt=now.time())
        )
        Agendamento.objects.filter(agendamentos_pendentes_expirados_filter).update(status_agendamento='negado')

        return AgendamentoPai.objects.select_related('id_recurso', 'id_usuario').prefetch_related('agendamentos_filhos').order_by('-data_criacao')

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

        if novo_status not in ['aprovado', 'negado', 'cancelado']:
            return Response({"error": "Status inválido. Use 'aprovado', 'negado' ou 'cancelado'."}, status=status.HTTP_400_BAD_REQUEST)
        
        with transaction.atomic():
            if novo_status == 'aprovado':
                ag_pai = instance.agendamento_pai
                conflitos = Agendamento.objects.filter(
                    agendamento_pai__id_recurso=ag_pai.id_recurso,
                    data_inicio=instance.data_inicio,
                    hora_inicio__lt=instance.hora_fim,
                    hora_fim__gt=instance.hora_inicio,
                    status_agendamento='aprovado'
                ).exclude(id_agendamento=instance.id_agendamento)
                
                if conflitos.exists():
                    return Response(
                        {"error": "Este horário já foi aprovado para outro agendamento."},
                        status=status.HTTP_409_CONFLICT
                    )

            instance.status_agendamento = novo_status
            instance.gerenciado_por = request.user
            instance.save()
            
            agendamento_pai = instance.agendamento_pai
            mensagem = f"O status do seu agendamento para '{agendamento_pai.id_recurso.nome_recurso}' no dia {instance.data_inicio.strftime('%d/%m/%Y')} foi atualizado para '{novo_status}'."
            criar_e_enviar_notificacao(agendamento_pai.id_usuario, agendamento_pai, mensagem)

            if novo_status == 'aprovado':
                _negar_conflitos_em_massa([instance])

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
            
            with transaction.atomic():
                agendamentos_pendentes = instance.agendamentos_filhos.filter(status_agendamento='pendente')
                agendamentos_para_atualizar = list(agendamentos_pendentes)

                if agendamentos_para_atualizar:
                    agendamentos_pendentes.update(
                        status_agendamento=novo_status,
                        gerenciado_por=request.user
                    )
                    
                    if novo_status == 'aprovado':
                        _negar_conflitos_em_massa(agendamentos_para_atualizar)
                    
                    mensagem = f"Todos os horários pendentes da sua solicitação para '{instance.id_recurso.nome_recurso}' foram atualizados para '{novo_status}'."
                    criar_e_enviar_notificacao(instance.id_usuario, instance, mensagem)

            instance.refresh_from_db()
            serializer = AdminAgendamentoPaiSerializer(instance)
            return Response(serializer.data)
        
        return super().update(request, *args, **kwargs)

class UserAgendamentoPaiStatusUpdateView(generics.UpdateAPIView):
    """
    Endpoint para um usuário marcar sua própria reserva como concluída ou cancelada
    """
    serializer_class = AgendamentoPaiDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id_agendamento_pai'

    def get_queryset(self):
        return AgendamentoPai.objects.filter(id_usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        novo_status = request.data.get("status_agendamento")

        if novo_status not in ['concluido', 'cancelado']:
            return Response({"error": "Status inválido. Apenas 'concluido' ou 'cancelado' é permitido por esta rota."}, status=status.HTTP_400_BAD_REQUEST)

        # Apenas horários aprovados ou pendentes podem ser alterados para concluído/cancelado
        status_para_alterar = ['aprovado', 'pendente']
        instance.agendamentos_filhos.filter(status_agendamento__in=status_para_alterar).update(status_agendamento=novo_status)

        # Se cancelou, verifica se o recurso pode voltar a ficar disponível
        if novo_status == 'cancelado':
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
    Endpoint para um usuário marcar um de seus próprios agendamentos como concluído ou cancelado
    """
    serializer_class = AdminAgendamentoSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id_agendamento'

    def get_queryset(self):
        return Agendamento.objects.filter(agendamento_pai__id_usuario=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        novo_status = request.data.get("status_agendamento")

        if novo_status not in ['concluido', 'cancelado']:
            return Response({"error": "Ação não permitida. Apenas 'concluido' ou 'cancelado' é válido."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Apenas agendamentos aprovados ou pendentes podem ser alterados
        if instance.status_agendamento not in ['aprovado', 'pendente']:
             return Response({"error": f"Ação não permitida para agendamentos com status '{instance.status_agendamento}'."}, status=status.HTTP_400_BAD_REQUEST)

        instance.status_agendamento = novo_status
        instance.save()
        
        if novo_status == 'cancelado':
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