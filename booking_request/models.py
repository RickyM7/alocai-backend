from django.db import models

from booking.models import Agendamento
from login.models import Usuario

class Solicitacao(models.Model):
    id_solicitacao = models.AutoField(primary_key=True)
    id_usuario_solicitante = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        db_column='id_usuario_solicitante',
        related_name='solicitacoes_solicitadas'
    )
    id_agendamento = models.ForeignKey(
        Agendamento, 
        on_delete=models.CASCADE, 
        db_column='id_agendamento'
    )
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    descricao_solicitacao = models.TextField(null=True, blank=True)
    status_solicitacao = models.CharField(max_length=20)
    observacoes_admin = models.TextField(null=True, blank=True)
    data_ultima_atualizacao_status = models.DateTimeField(auto_now=True)
    id_responsavel = models.ForeignKey(
        Usuario, 
        on_delete=models.CASCADE, 
        db_column='id_usuario_responsavel',
        related_name='solicitacoes_responsaveis'
    )

    class Meta:
        db_table = 'solicitacao'