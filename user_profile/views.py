from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from user_profile.models import PerfilAcesso, PerfilAcessoSerializer

class PerfilAcessoView(APIView):
    """ 
    Endpoint para retornar os perfis de acesso:
    - Aberto para todos os usuários.
    - Lista todos os perfis se for um Administrador.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Método GET para retornar informações do perfil de acesso.
        """
        user = request.user
        
        # Verifica se o usuário está autenticado e se é um administrador
        is_admin = (
            user and
            user.is_authenticated and
            user.id_perfil and
            user.id_perfil.nome_perfil == 'Administrador'
        )

        if is_admin:
            # Se for admin, retorna todos os perfis
            profiles = PerfilAcesso.objects.all()
        else:
            # Para usuários não logados ou não-admins, retorna apenas os perfis visíveis
            profiles = PerfilAcesso.objects.filter(visibilidade=True)

        serializer = PerfilAcessoSerializer(profiles, many=True)
        return Response(serializer.data)