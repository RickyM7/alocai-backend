from rest_framework import serializers
from .models import Agendamento

class AgendamentoSerializer(serializers.ModelSerializer):
	# O id de usuário será o do usuário logado
	id_usuario = serializers.PrimaryKeyRelatedField(read_only=True)
	class Meta:
		model = Agendamento
		fields = [
		'id_agendamento',
		'id_recurso',
        'data_inicio',
        'hora_inicio',
        'data_fim',
        'hora_fim',
        'status_agendamento',
        'finalidade',
        'observacoes',
        'id_responsavel',
        'id_usuario',
        'data_criacao'
		]