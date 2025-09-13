from django.urls import path
from .views import (
    ListarAgendamentosView,
    CriarAgendamentoView,
    AgendamentoPaiDetailView,
    AdminAgendamentoListView,
    AdminAgendamentoStatusUpdateView,
    AdminAgendamentoPaiManageView,
    UserAgendamentoPaiStatusUpdateView,
    UserAgendamentoStatusUpdateView,
    RecursoDisponibilidadeView
)

urlpatterns = [
    # URL para criar um agendamento (POST)
    path('agendamentos/', CriarAgendamentoView.as_view(), name='criar-agendamento'),
    # URL para listar os agendamentos do usuário (GET)
    path('agendamentos/minhas-reservas/', ListarAgendamentosView.as_view(), name='listar-agendamentos'),
    # URL para retornar os detalhes completos de um agendamento pai (GET)
    path('agendamentos/pai/<int:id_agendamento_pai>/', AgendamentoPaiDetailView.as_view(), name='detalhe-agendamento-pai'),
    # URL para o adm listar todas as solicitações (GET)
    path('admin/agendamentos/', AdminAgendamentoListView.as_view(), name='admin-listar-agendamentos'), 
    # URL para o adm atualizar o status de uma solicitação individual (PUT/PATCH)
    path('admin/agendamentos/<int:id_agendamento>/status/', AdminAgendamentoStatusUpdateView.as_view(), name='admin-atualizar-status-agendamento'),
    # URL para o adm aprovar/negar/apagar todas as solicitações de um agendamento pai (PUT/PATCH/DELETE)
    path('admin/agendamentos/pai/<int:id_agendamento_pai>/', AdminAgendamentoPaiManageView.as_view(), name='admin-gerenciar-agendamento-pai'),
    # URL para o usuário marcar sua reserva como concluída (PUT/PATCH)
    path('agendamentos/pai/<int:id_agendamento_pai>/status/', UserAgendamentoPaiStatusUpdateView.as_view(), name='user-atualizar-status-agendamento-pai'),
    # URL para o usuário marcar um horário específico como concluído (PUT/PATCH)
    path('agendamentos/<int:id_agendamento>/status/', UserAgendamentoStatusUpdateView.as_view(), name='user-atualizar-status-agendamento'),
    # URL para verificar horários já agendados para um recurso (GET)
    path('recursos/<int:recurso_id>/disponibilidade/', RecursoDisponibilidadeView.as_view(), name='recurso-disponibilidade'),
]