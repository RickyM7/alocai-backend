from django.db import models
from django.conf import settings
from resource.models import Recurso

class AgendamentoPai(models.Model):
    id_agendamento_pai = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="agendamentos_pai"
    )
    id_recurso = models.ForeignKey(
        Recurso,
        on_delete=models.CASCADE
    )
    finalidade = models.CharField(max_length=255, null=True, blank=True)
    observacoes = models.TextField(null=True, blank=True)
    id_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="responsabilidades_pai"
    )
    data_criacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'agendamento_pai'


class Agendamento(models.Model):
    id_agendamento = models.AutoField(primary_key=True)
    agendamento_pai = models.ForeignKey(
        AgendamentoPai,
        on_delete=models.CASCADE,
        related_name="agendamentos_filhos",
        null=True,
        blank=True
    )
    data_inicio = models.DateField()
    hora_inicio = models.TimeField()
    data_fim = models.DateField()
    hora_fim = models.TimeField()
    status_agendamento = models.CharField(max_length=20)
    data_ultima_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agendamento'