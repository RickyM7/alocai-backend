from django.db import models

class PerfilAcesso(models.Model):
    id_perfil = models.AutoField(primary_key=True)
    nome_perfil = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'perfil_acesso'

    def __str__(self):
        return self.nome_perfil