from django.urls import path
from .views import CriarAgendamentoView, ListarAgendamentosView, AgendamentoPaiDetailView, AdminAgendamentoListView, AdminAgendamentoStatusUpdateView

urlpatterns = [
    # URL para criar um agendamento (POST)
    path('agendamentos/', CriarAgendamentoView.as_view(), name='criar-agendamento'),
    # URL para listar os agendamentos do usuário (GET)
    path('agendamentos/minhas-reservas/', ListarAgendamentosView.as_view(), name='listar-agendamentos'),
    # URL para retornar os detalhes completos de um agendamento pai (GET)
    path('agendamentos/pai/<int:id_agendamento_pai>/', AgendamentoPaiDetailView.as_view(), name='detalhe-agendamento-pai'),
    # URL para o adm listar todas as solicitações (GET)
    path('admin/agendamentos/', AdminAgendamentoListView.as_view(), name='admin-listar-agendamentos'),
    # URL para o adm atualizar o status de uma solicitação (PATCH)
    path('admin/agendamentos/<int:id_agendamento>/status/', AdminAgendamentoStatusUpdateView.as_view(), name='admin-atualizar-status-agendamento'),
]
