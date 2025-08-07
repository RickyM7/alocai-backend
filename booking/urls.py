from django.urls import path
from .views import CriarAgendamentoView

urlpatterns = [
    # URL para criar um agendamento (POST)
    path('agendamentos/', CriarAgendamentoView.as_view(), name='criar-agendamento'),
]