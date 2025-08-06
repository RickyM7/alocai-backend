from django.db import models

# Create your models here.
class Recurso(models.Model):
    id_recurso = models.AutoField(primary_key=True)
    #id_instituicao = models.IntegerField()
    nome_recurso = models.CharField(max_length=255)
    #id_tipo_recurso = models.IntegerField()
    descricao = models.TextField(null=True, blank=True)
    capacidade = models.IntegerField(null=True, blank=True)
    localizacao = models.CharField(max_length=255, null=True, blank=True)
    status_recurso = models.CharField(max_length=20)
    politicas_uso_especificas = models.TextField(null=True, blank=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)
    data_atualizacao = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'recurso'