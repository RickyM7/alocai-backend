from django.urls import path
from .views import ListarNotificacoesView, MarcarNotificacoesComoLidasView, GerenciarNotificacaoView, MarcarNotificacaoComoLidaView

urlpatterns = [
    path('notificacoes/', ListarNotificacoesView.as_view(), name='listar-notificacoes'),
    path('notificacoes/marcar-como-lidas/', MarcarNotificacoesComoLidasView.as_view(), name='marcar-notificacoes-lidas'),
    path('notificacoes/<int:pk>/marcar-como-lida/', MarcarNotificacaoComoLidaView.as_view(), name='marcar-notificacao-lida'),
    path('notificacoes/<int:pk>/', GerenciarNotificacaoView.as_view(), name='gerenciar-notificacao'),
]