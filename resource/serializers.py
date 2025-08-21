from rest_framework import serializers
from .models import Recurso

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
