from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from user_profile.models import PerfilAcesso, PerfilAcessoSerializer


# Create your views here.
class PerfilAcessoView(APIView):
    """ 
        Endpoint para gerenciar o perfil de acesso do usuário. 
    """

    def get(self, request):
        """
        Método GET para retornar informações do perfil de acesso.
        """
        permission_classes = [AllowAny]
        #permission_classes = [IsAuthenticated]

        profiles = PerfilAcesso.objects.all()

        # Serializa os dados dos perfis de acesso
        serializer = PerfilAcessoSerializer(profiles, many=True)
        return Response(serializer.data)
