from django.contrib import admin
from .models import AgendamentoPai, Agendamento, UsoImediato


class AgendamentoInline(admin.TabularInline):
    model = Agendamento
    extra = 0
    readonly_fields = ('data_ultima_atualizacao',)


@admin.register(AgendamentoPai)
class AgendamentoPaiAdmin(admin.ModelAdmin):
    list_display = ('id_agendamento_pai', 'id_usuario', 'id_recurso', 'finalidade', 'data_criacao')
    list_filter = ('data_criacao',)
    search_fields = ('id_usuario__nome', 'id_recurso__nome_recurso', 'finalidade')
    readonly_fields = ('data_criacao',)
    inlines = [AgendamentoInline]


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('id_agendamento', 'agendamento_pai', 'data_inicio', 'hora_inicio', 'hora_fim', 'status_agendamento')
    list_filter = ('status_agendamento', 'data_inicio')
    search_fields = ('agendamento_pai__id_recurso__nome_recurso',)
    readonly_fields = ('data_ultima_atualizacao',)


@admin.register(UsoImediato)
class UsoImediatoAdmin(admin.ModelAdmin):
    list_display = ('id_uso', 'id_usuario', 'id_recurso', 'duracao_minutos', 'ativo', 'data_inicio')
    list_filter = ('ativo', 'data_inicio')
    search_fields = ('id_usuario__nome', 'id_recurso__nome_recurso')
    readonly_fields = ('data_inicio',)
