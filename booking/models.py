from django.db import models
from django.conf import settings
# from login.models import Usuario
from resource.models import Recurso

# Create your models here.
class Agendamento(models.Model):
    id_agendamento = models.AutoField(primary_key=True)
    id_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    id_recurso = models.ForeignKey(Recurso, on_delete=models.CASCADE, db_column='id_recurso')
    data_inicio = models.DateField()
    hora_inicio = models.TimeField()
    data_fim = models.DateField()
    hora_fim = models.TimeField()
    status_agendamento = models.CharField(max_length=20)
    finalidade = models.CharField(max_length=255, null=True, blank=True)
    observacoes = models.TextField(null=True, blank=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    data_ultima_atualizacao = models.DateTimeField(auto_now=True)
    id_responsavel = models.IntegerField()

    class Meta:
        db_table = 'agendamento'