from django.contrib import admin
from .models import Notificacao


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ('id_notificacao', 'destinatario', 'mensagem_curta', 'lida', 'data_criacao')
    list_filter = ('lida', 'data_criacao')
    search_fields = ('destinatario__nome', 'mensagem')
    readonly_fields = ('data_criacao',)

    def mensagem_curta(self, obj):
        return obj.mensagem[:80] + '...' if len(obj.mensagem) > 80 else obj.mensagem
    mensagem_curta.short_description = 'Mensagem'
