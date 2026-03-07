from django.db import models


class StatusRecurso(models.TextChoices):
    DISPONIVEL = 'disponivel', 'Disponível'
    EM_MANUTENCAO = 'em_manutencao', 'Em Manutenção'
    INDISPONIVEL = 'indisponivel', 'Indisponível'
    RESERVADO = 'reservado', 'Reservado'


class Recurso(models.Model):
    id_recurso = models.AutoField(primary_key=True)
    nome_recurso = models.CharField(max_length=255)
    descricao = models.TextField(null=True, blank=True)
    capacidade = models.IntegerField(null=True, blank=True)
    localizacao = models.CharField(max_length=255, null=True, blank=True)
    status_recurso = models.CharField(
        max_length=20,
        choices=StatusRecurso.choices,
        default=StatusRecurso.DISPONIVEL
    )
    politicas_uso_especificas = models.TextField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recurso'

    def __str__(self):
        return self.nome_recurso