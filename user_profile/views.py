from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from user_profile.models import PerfilAcesso, PerfilAcessoSerializer

class PerfilAcessoView(APIView):
    """ 
    Endpoint para gerenciar o perfil de acesso do usuário. 
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Método GET para retornar informações do perfil de acesso.
        """
        profiles = PerfilAcesso.objects.filter(visibilidade=True)  # Filtra apenas perfis visíveis

        # Serializa os dados dos perfis de acesso
        serializer = PerfilAcessoSerializer(profiles, many=True)
        return Response(serializer.data)
