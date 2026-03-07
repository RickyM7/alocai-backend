from django.contrib import admin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id_usuario', 'nome', 'email', 'id_perfil', 'status_conta', 'ultimo_login')
    list_filter = ('status_conta', 'id_perfil')
    search_fields = ('nome', 'email')
    readonly_fields = ('data_criacao_conta', 'ultimo_login')
