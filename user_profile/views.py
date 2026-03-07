from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from user_profile.models import PerfilAcesso
from user_profile.serializers import PerfilAcessoSerializer


class PerfilAcessoView(APIView):
    """
    Lista perfis de acesso. Admins veem todos; outros veem apenas os visíveis.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        is_admin = (
            user and
            user.is_authenticated and
            user.id_perfil and
            user.id_perfil.nome_perfil == 'Administrador'
        )
        profiles = PerfilAcesso.objects.all() if is_admin else PerfilAcesso.objects.filter(visibilidade=True)
        return Response(PerfilAcessoSerializer(profiles, many=True).data)