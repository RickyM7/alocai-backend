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

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        # Usa o campo 'status_conta' para determinar se o usuário está ativo
        return self.status_conta == 'ativo'

    # O Django precisa disso para o cliente de teste e o admin
    is_staff = False

    class Meta:
        db_table = 'usuario'