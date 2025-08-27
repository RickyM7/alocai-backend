from rest_framework import serializers
from .models import Recurso
from booking.models import Agendamento
from booking.serializers import PublicAgendamentoSerializer

class RecursoSerializer(serializers.ModelSerializer):
    """
    Serializer para o modelo Recurso.
    """
    class Meta:
        model = Recurso
        fields = [
            'id_recurso', 'nome_recurso', 'descricao', 'capacidade', 
            'localizacao', 'status_recurso', 'politicas_uso_especificas',
            'data_cadastro', 'data_atualizacao'
        ]
        read_only_fields = ('data_cadastro', 'data_atualizacao')

    def validate_status_recurso(self, value):
        """
        Valida se o status do recurso é um dos valores permitidos.
        """
        status_validos = ['disponivel', 'em_manutencao', 'indisponivel', 'reservado']
        if value not in status_validos:
            raise serializers.ValidationError(f"Status inválido. Deve ser um dos seguintes: {', '.join(status_validos)}")
        return value

class DashboardRecursoSerializer(serializers.ModelSerializer):
    """
    Serializer para a visualização do dashboard
    (mostra recursos e os agendamentos aprovados)
    """
    agendamentos = serializers.SerializerMethodField()

    class Meta:
        model = Recurso
        fields = [
            'id_recurso', 'nome_recurso', 'descricao', 'localizacao',
            'status_recurso', 'agendamentos'
        ]

    def get_agendamentos(self, obj):
        # Filtra os agendamentos para pegar apenas os 'aprovados' para este recurso
        agendamentos_aprovados = Agendamento.objects.filter(
            agendamento_pai__id_recurso=obj.id_recurso,
            status_agendamento='aprovado'
        ).order_by('data_inicio', 'hora_inicio')
        
        serializer = PublicAgendamentoSerializer(agendamentos_aprovados, many=True)
        return serializer.data