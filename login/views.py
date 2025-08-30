import os
from dotenv import load_dotenv

from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from google.oauth2 import id_token
from google.auth.transport import requests
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Usuario
from user_profile.models import PerfilAcesso
from user_profile.permissions import IsAdministrador
from .serializers import UserAdminSerializer

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class GoogleSignInAPIView(APIView):
    """
    Endpoint para autenticação com Google OAuth.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Recebe o token do Google, valida, busca ou cria um usuário
        e retorna os tokens de acesso e atualização (JWT).
        """
        token = request.data.get('credential')

        if not token:
            return Response({'error': 'Credential not provided'}, status=400)

        try:
            client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
            user_data_from_google = id_token.verify_oauth2_token(
                token, requests.Request(), client_id
            )
        except ValueError:
            return Response({'error': 'Invalid token'}, status=403)

        email = user_data_from_google.get('email')
        if not email:
            return Response({'error': 'Email not found in Google token'}, status=400)

        full_name = f"{user_data_from_google.get('given_name', '')} {user_data_from_google.get('family_name', '')}".strip()
        picture_url = user_data_from_google.get('picture')

        # Busca ou cria o usuário
        user, created = Usuario.objects.get_or_create(
            email=email,
            defaults={
                'email': email,
                'nome': full_name,
                'foto_perfil': picture_url,
                'data_criacao_conta': timezone.now(),
                # 'senha_hash': 'manage_google_oauth',  # Senha não é necessária para login via Google
                'status_conta': 'ativo',
            }
        )

        if not created:
            # Usuário já existia
            user.ultimo_login = timezone.now()
            user.foto_perfil = picture_url
            if user.status_conta != 'ativo':
                user.status_conta = 'ativo'
            user.save()

        # Gera os tokens para o usuário
        refresh = RefreshToken.for_user(user)

        response = Response({
            'access': str(refresh.access_token),
            'user_data': {
                'id_usuario': user.id_usuario,
                'email': user.email,
                'nome': user.nome,
                'foto_perfil': user.foto_perfil,
                'data_criacao_conta': user.data_criacao_conta,
                'id_perfil': user.id_perfil.id_perfil if user.id_perfil else None,
                'nome_perfil': user.id_perfil.nome_perfil if user.id_perfil else None
            }
        }, status=200)

        # Define o cookie de refresh token
        response.set_cookie(
            key='refresh_token',
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite='Lax',
            path='/'
        )

        return response


class GoogleSignOutAPIView(APIView):
    """
    Endpoint para logout do usuário.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Usando o JWT, o logout acontece no próprio frontend
        return Response({"detail": "User logged out successfully'"}, status=200)

class UserAPIView(APIView):
    """
    Endpoint para definir tipo do usuário.
    Recebe o id_perfil e atribui ao usuário autenticado.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, id_usuario):
        id_perfil_novo = request.data.get('id_perfil')
        if not id_perfil_novo:
            return Response({"error": "id_perfil is required"}, status=status.HTTP_400_BAD_REQUEST)

        usuario_logado = request.user
        
        try:
            perfil_novo = PerfilAcesso.objects.get(id_perfil=id_perfil_novo)
            user_a_ser_editado = Usuario.objects.get(id_usuario=id_usuario)

            # Impede que o admin altere o próprio perfil para um não-admin
            is_admin_editing_self = (
                usuario_logado.id_usuario == user_a_ser_editado.id_usuario and
                usuario_logado.id_perfil and
                usuario_logado.id_perfil.nome_perfil == 'Administrador'
            )

            if is_admin_editing_self and perfil_novo.nome_perfil != 'Administrador':
                return Response(
                    {"error": "Administradores não podem remover o próprio privilégio."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Um usuário só pode editar a si mesmo, a menos que seja um administrador
            is_admin = usuario_logado.id_perfil and usuario_logado.id_perfil.nome_perfil == 'Administrador'
            if not (usuario_logado.id_usuario == user_a_ser_editado.id_usuario or is_admin):
                 return Response(
                    {"error": "Você não tem permissão para alterar este perfil."},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Se passar pelas verificações, atualiza o perfil
            user_a_ser_editado.id_perfil = perfil_novo
            user_a_ser_editado.save()

        except PerfilAcesso.DoesNotExist:
            return Response({"error": "Perfil de acesso não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuário não encontrado"}, status=status.HTTP_404_NOT_FOUND)

        return Response({"detail": "Perfil do usuário definido com sucesso"}, status=status.HTTP_200_OK)


class UserListView(generics.ListAPIView):
    """
    Endpoint para o admin listar todos os usuários
    """
    queryset = Usuario.objects.all().order_by('nome')
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdministrador]

# Função para "health check" que verifica se o app está funcionando
def health_check(request):
    data = {
        'status': 'ok',
        'message': 'App está rodando'
    }
    return JsonResponse(data)