from rest_framework import serializers
from .models import Usuario

class UserAdminSerializer(serializers.ModelSerializer):
    """
    Serializer para listar os usuários no painel admin.
    """
    nome_perfil = serializers.CharField(source='id_perfil.nome_perfil', read_only=True, allow_null=True)

    class Meta:
        model = Usuario
        fields = [
            'id_usuario',
            'nome',
            'email',
            'status_conta',
            'ultimo_login',
            'id_perfil',
            'nome_perfil'
        ]