from django.db import models

class Usuario(models.Model):
    id_usuario = models.AutoField(primary_key=True)
    #id_instituicao = models.IntegerField()
    #id_perfil = models.IntegerField()
    nome = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    senha_hash = models.CharField(max_length=255)
    numero_matricula = models.CharField(max_length=100, null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    status_conta = models.CharField(max_length=20)
    data_criacao_conta = models.DateTimeField(auto_now_add=True)
    ultimo_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'usuario'