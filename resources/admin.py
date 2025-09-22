from django.contrib import admin
from .models import Recurso
from django.utils.html import format_html

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
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('tipo_recurso') if hasattr(Recurso, 'tipo_recurso') else qs
