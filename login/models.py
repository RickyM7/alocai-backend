from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from user_profile.models import PerfilAcesso

class UsuarioManager(BaseUserManager):
    def create_user(self, email, nome, password=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, nome=nome, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(email, nome, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    id_usuario = models.AutoField(primary_key=True)
    id_perfil = models.ForeignKey(PerfilAcesso, on_delete=models.CASCADE, db_column='id_perfil', null=True, blank=True)
    nome = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, unique=True)
    foto_perfil = models.URLField(max_length=255, null=True, blank=True)
    numero_matricula = models.CharField(max_length=100, null=True, blank=True)
    telefone = models.CharField(max_length=20, null=True, blank=True)
    status_conta = models.CharField(max_length=20, default='ativo')
    data_criacao_conta = models.DateTimeField(auto_now_add=True)
    ultimo_login = models.DateTimeField(null=True, blank=True)
    
    objects = UsuarioManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']
    
    @property
    def is_authenticated(self):
        return True

    @property
    def id(self):
        return self.id_usuario
    
    @property
    def pk(self):
        return self.id_usuario

    is_staff = models.BooleanField(default=False)

    class Meta:
        db_table = 'usuario'