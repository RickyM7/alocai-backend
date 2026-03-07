from rest_framework import serializers
from .models import Notificacao

class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = [
            'id_notificacao', 'destinatario', 'agendamento_pai',
            'mensagem', 'lida', 'data_criacao'
        ]
        read_only_fields = ('id_notificacao', 'destinatario', 'agendamento_pai', 'mensagem', 'data_criacao')