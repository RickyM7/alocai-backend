from rest_framework import serializers
from .models import PerfilAcesso

class PerfilAcessoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilAcesso
        fields = ['id_perfil', 'nome_perfil', 'descricao', 'visibilidade']
