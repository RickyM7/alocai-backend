from django.contrib import admin
from .models import PerfilAcesso


@admin.register(PerfilAcesso)
class PerfilAcessoAdmin(admin.ModelAdmin):
    list_display = ('id_perfil', 'nome_perfil', 'visibilidade')
    list_filter = ('visibilidade',)
    search_fields = ('nome_perfil',)
