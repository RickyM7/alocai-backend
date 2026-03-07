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
    RecursoDisponibilidadeView,
    RegistrarUsoImediatoView,
    FinalizarUsoImediatoView
)

urlpatterns = [
    path('agendamentos/', CriarAgendamentoView.as_view(), name='criar-agendamento'),
    path('agendamentos/minhas-reservas/', ListarAgendamentosView.as_view(), name='listar-agendamentos'),
    path('agendamentos/pai/<int:id_agendamento_pai>/', AgendamentoPaiDetailView.as_view(), name='detalhe-agendamento-pai'),
    path('admin/agendamentos/', AdminAgendamentoListView.as_view(), name='admin-listar-agendamentos'),
    path('admin/agendamentos/<int:id_agendamento>/status/', AdminAgendamentoStatusUpdateView.as_view(), name='admin-atualizar-status-agendamento'),
    path('admin/agendamentos/pai/<int:id_agendamento_pai>/', AdminAgendamentoPaiManageView.as_view(), name='admin-gerenciar-agendamento-pai'),
    path('agendamentos/pai/<int:id_agendamento_pai>/status/', UserAgendamentoPaiStatusUpdateView.as_view(), name='user-atualizar-status-agendamento-pai'),
    path('agendamentos/<int:id_agendamento>/status/', UserAgendamentoStatusUpdateView.as_view(), name='user-atualizar-status-agendamento'),
    path('recursos/<int:recurso_id>/disponibilidade/', RecursoDisponibilidadeView.as_view(), name='recurso-disponibilidade'),
    path('uso-imediato/', RegistrarUsoImediatoView.as_view(), name='uso-imediato'),
    path('uso-imediato/<int:id_uso>/finalizar/', FinalizarUsoImediatoView.as_view(), name='finalizar-uso-imediato'),
]