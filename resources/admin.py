from django.contrib import admin
from .models import Recurso

@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ('nome_recurso', 'status_recurso', 'localizacao', 'capacidade', 'data_cadastro')
    list_filter = ('status_recurso', 'data_cadastro')
    search_fields = ('nome_recurso', 'descricao', 'localizacao')
    readonly_fields = ('data_cadastro', 'data_atualizacao')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome_recurso', 'descricao', 'status_recurso')
        }),
        ('Detalhes', {
            'fields': ('capacidade', 'localizacao', 'politicas_uso_especificas')
        }),
        ('Metadados', {
            'fields': ('data_cadastro', 'data_atualizacao'),
            'classes': ('collapse',),
        }),
    )
