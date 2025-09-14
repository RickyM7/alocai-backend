from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Notificacao
from .serializers import NotificacaoSerializer

class ListarNotificacoesView(generics.ListAPIView):
    serializer_class = NotificacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notificacao.objects.filter(destinatario=self.request.user)

class MarcarNotificacoesComoLidasView(generics.UpdateAPIView):
    serializer_class = NotificacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notificacao.objects.filter(destinatario=self.request.user, lida=False)

    def update(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        queryset.update(lida=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

class GerenciarNotificacaoView(generics.DestroyAPIView):
    """
    View para deletar uma notificação específica.
    """
    serializer_class = NotificacaoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notificacao.objects.filter(destinatario=self.request.user)