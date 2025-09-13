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
            'hora_fim',
            'finalidade', 'status_agendamento', 'agendamento_pai', 'observacoes'
        ]

# Serializers do ADM
class AdminAgendamentoSerializer(serializers.ModelSerializer):
    gerenciado_por_nome = serializers.CharField(source='gerenciado_por.nome', read_only=True, allow_null=True)
    class Meta:
        model = Agendamento
        fields = [
            'id_agendamento', 'data_inicio', 'hora_inicio', 'hora_fim',
            'status_agendamento', 'gerenciado_por_nome', 'data_ultima_atualizacao'
        ]

class AdminAgendamentoPaiSerializer(serializers.ModelSerializer):
    agendamentos_filhos = AdminAgendamentoSerializer(many=True, read_only=True)
    recurso = serializers.CharField(source='id_recurso.nome_recurso', read_only=True)
    solicitante = serializers.CharField(source='id_usuario.nome', read_only=True)
    gerenciado_info = serializers.SerializerMethodField()

    class Meta:
        model = AgendamentoPai
        fields = [
            'id_agendamento_pai', 'recurso', 'finalidade', 'observacoes',
            'solicitante', 'data_criacao', 'agendamentos_filhos', 'id_responsavel',
            'gerenciado_info'
        ]

    def get_gerenciado_info(self, obj):
        # Pega o agendamento filho que foi atualizado mais recentemente
        last_updated_child = obj.agendamentos_filhos.order_by('-data_ultima_atualizacao').first()
        if last_updated_child and last_updated_child.gerenciado_por:
            return {
                'nome': last_updated_child.gerenciado_por.nome,
                'data': last_updated_child.data_ultima_atualizacao
            }
        return None


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id_usuario', 'nome', 'email']

class PublicAgendamentoSerializer(serializers.ModelSerializer):
    # Visualização pública de agendamentos (para usar no dashboard)
    recurso = serializers.CharField(source='agendamento_pai.id_recurso.nome_recurso', read_only=True)
    finalidade = serializers.CharField(source='agendamento_pai.finalidade', read_only=True)

    class Meta:
        model = Agendamento
        fields = [
            'id_agendamento', 'recurso', 'data_inicio', 'hora_inicio',
            'data_fim', 'hora_fim', 'status_agendamento', 'finalidade'
        ]

class AgendamentoUpdateSerializer(serializers.ModelSerializer):
    id_agendamento = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Agendamento
        fields = [
            'id_agendamento',
            'data_inicio',
            'hora_inicio',
            'data_fim',
            'hora_fim',
        ]

class AdminAgendamentoPaiUpdateSerializer(serializers.ModelSerializer):
    agendamentos_filhos = AgendamentoUpdateSerializer(many=True)

    class Meta:
        model = AgendamentoPai
        fields = [
            'id_agendamento_pai', 'finalidade', 'observacoes',
            'id_responsavel', 'agendamentos_filhos'
        ]

    def validate(self, data):
        agendamentos_data = data.get('agendamentos_filhos', [])
        recurso = self.instance.id_recurso
        agendamento_pai_id = self.instance.id_agendamento_pai

        for agendamento_data in agendamentos_data:
            data_inicio = agendamento_data.get('data_inicio')
            hora_inicio = agendamento_data.get('hora_inicio')
            hora_fim = agendamento_data.get('hora_fim')
            agendamento_id = agendamento_data.get('id_agendamento')

            conflitos = Agendamento.objects.filter(
                agendamento_pai__id_recurso=recurso,
                data_inicio=data_inicio,
                hora_inicio__lt=hora_fim,
                hora_fim__gt=hora_inicio,
                status_agendamento='aprovado'
            )

            if agendamento_id:
                conflitos = conflitos.exclude(id_agendamento=agendamento_id)

            if conflitos.exists():
                raise serializers.ValidationError(
                    f"Conflito de horário no dia {data_inicio.strftime('%d/%m/%Y')} entre {hora_inicio.strftime('%H:%M')} e {hora_fim.strftime('%H:%M')}."
                )
        return data

    def update(self, instance, validated_data):
        instance.finalidade = validated_data.get('finalidade', instance.finalidade)
        instance.observacoes = validated_data.get('observacoes', instance.observacoes)
        instance.id_responsavel_id = validated_data.get('id_responsavel', instance.id_responsavel_id)
        instance.save()

        children_data = validated_data.get('agendamentos_filhos', [])
        
        children_ids_from_payload = {item.get('id_agendamento') for item in children_data if item.get('id_agendamento')}

        instance.agendamentos_filhos.exclude(id_agendamento__in=children_ids_from_payload).delete()

        for child_data in children_data:
            child_id = child_data.get('id_agendamento')
            child_data.pop('id_agendamento', None)

            if child_id:
                Agendamento.objects.filter(id_agendamento=child_id, agendamento_pai=instance).update(**child_data)
            else:
                Agendamento.objects.create(agendamento_pai=instance, status_agendamento='pendente', **child_data)

        return instance