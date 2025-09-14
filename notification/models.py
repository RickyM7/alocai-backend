from django.db import models
from django.conf import settings
from booking.models import AgendamentoPai

class Notificacao(models.Model):
    id_notificacao = models.AutoField(primary_key=True)
    destinatario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notificacoes'
    )
    agendamento_pai = models.ForeignKey(
        AgendamentoPai,
        on_delete=models.CASCADE,
        related_name='notificacoes',
        null=True,
        blank=True
    )
    mensagem = models.TextField()
    lida = models.BooleanField(default=False)
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificacao'
        ordering = ['-data_criacao']

    def __str__(self):
        return f"Notificação para {self.destinatario.nome}: {self.mensagem}"