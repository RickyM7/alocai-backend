from rest_framework import serializers
from .models import Agendamento, AgendamentoPai
from resource.models import Recurso
from login.models import Usuario

class AgendamentoFilhoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Agendamento
        fields = [
            'id_agendamento',
            'data_inicio',
            'hora_inicio',
            'data_fim',
            'hora_fim',
            'status_agendamento',
        ]

class AgendamentoPaiCreateSerializer(serializers.ModelSerializer):
    datas_agendamento = serializers.ListField(
        child=serializers.DictField(), write_only=True
    )

    class Meta:
        model = AgendamentoPai
        fields = [
            'id_agendamento_pai', 'id_recurso', 'finalidade', 'observacoes',
            'id_responsavel', 'id_usuario', 'data_criacao', 'datas_agendamento',
        ]
        read_only_fields = ('id_usuario', 'data_criacao')

    def create(self, validated_data):
        datas_agendamento = validated_data.pop('datas_agendamento')
        agendamento_pai = AgendamentoPai.objects.create(**validated_data)
        for data in datas_agendamento:
            Agendamento.objects.create(
                agendamento_pai=agendamento_pai,
                data_inicio=data['data_inicio'],
                hora_inicio=data['hora_inicio'],
                data_fim=data['data_fim'],
                hora_fim=data['hora_fim'],
                status_agendamento='pendente'
            )
        return agendamento_pai

class AgendamentoPaiDetailSerializer(serializers.ModelSerializer):
    agendamentos_filhos = AgendamentoFilhoSerializer(many=True, read_only=True)
    recurso = serializers.CharField(source='id_recurso.nome_recurso', read_only=True)
    responsavel = serializers.CharField(source='id_responsavel.nome', read_only=True)

    class Meta:
        model = AgendamentoPai
        fields = [
            'id_agendamento_pai', 'recurso', 'finalidade', 'observacoes', 
            'responsavel', 'data_criacao', 'agendamentos_filhos'
        ]

class ListarAgendamentosSerializer(serializers.ModelSerializer):
    recurso = serializers.CharField(source='agendamento_pai.id_recurso.nome_recurso', read_only=True)
    finalidade = serializers.CharField(source='agendamento_pai.finalidade', read_only=True)
    observacoes = serializers.CharField(source='agendamento_pai.observacoes', read_only=True)
    
    class Meta:
        model = Agendamento
        fields = [
            'id_agendamento', 'recurso', 'data_inicio', 'hora_inicio',
            'finalidade', 'status_agendamento', 'agendamento_pai', 'observacoes'
        ]

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id_usuario', 'nome', 'email']