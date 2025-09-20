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
from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.conf import settings

from .models import Usuario
from user_profile.models import PerfilAcesso
from user_profile.permissions import IsAdministrador
from .serializers import UserAdminSerializer

load_dotenv()

class GoogleSignInAPIView(APIView):
    """
    Endpoint para autenticação com Google OAuth.
    """
    permission_classes = [AllowAny]

    def post(self, request):
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

        google_id = user_data_from_google.get('sub')
        email = user_data_from_google.get('email')

        if not email:
            return Response({'error': 'Email not found in Google token'}, status=400)

        user = Usuario.objects.filter(google_id=google_id).first()
        if not user:
            user = Usuario.objects.filter(email=email).first()
            if user:
                user.google_id = google_id

        full_name = f"{user_data_from_google.get('given_name', '')} {user_data_from_google.get('family_name', '')}".strip()
        picture_url = user_data_from_google.get('picture')

        if user:
            user.nome = full_name
            user.foto_perfil = picture_url
            user.ultimo_login = timezone.now()
            user.save()
        else:
            user = Usuario.objects.create_user(
                email=email,
                nome=full_name,
                foto_perfil=picture_url,
                google_id=google_id
            )

        refresh = RefreshToken.for_user(user)

        # Prepara os dados do usuário para a resposta
        user_data = {
            'id_usuario': user.id_usuario, 'email': user.email, 'nome': user.nome,
            'foto_perfil': user.foto_perfil, 'data_criacao_conta': user.data_criacao_conta,
            'id_perfil': user.id_perfil.id_perfil if user.id_perfil else None,
            'nome_perfil': user.id_perfil.nome_perfil if user.id_perfil else None,
            'google_id': user.google_id
        }
        # Adiciona o campo tem_senha se o usuário for admin
        if user.id_perfil and user.id_perfil.nome_perfil == 'Administrador':
            user_data['tem_senha'] = user.has_usable_password()

        response = Response({
            'access': str(refresh.access_token),
            'user_data': user_data
        }, status=200)

        response.set_cookie(
            key='refresh_token', 
            value=str(refresh), 
            httponly=True, 
            secure=True,
            samesite='None', 
            path='/'
        )
        return response

class GoogleSignOutAPIView(APIView):
    """
    Endpoint para logout do usuário.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        return Response({"detail": "User logged out successfully'"}, status=200)

class CookieTokenRefreshView(TokenRefreshView):
    """
    Endpoint para renovar o token de acesso.
    """
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'Refresh token not found in cookie'}, status=status.HTTP_401_UNAUTHORIZED)
        
        request.data['refresh'] = refresh_token
        
        try:
            response = super().post(request, *args, **kwargs)
            if 'refresh' in response.data:
                new_refresh_token = response.data['refresh']
                response.set_cookie(
                    key='refresh_token', 
                    value=new_refresh_token, 
                    httponly=True, 
                    secure=True,
                    samesite='None',
                    path='/'
                )
            return response
        except (InvalidToken, TokenError) as e:
            return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

class LinkGoogleAccountView(APIView):
    """
    Endpoint para um admin logado vincular uma conta Google.
    """
    permission_classes = [IsAuthenticated, IsAdministrador]

    def post(self, request):
        credential = request.data.get('credential')
        if not credential:
            return Response({'error': 'Credential não fornecido.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
            idinfo = id_token.verify_oauth2_token(credential, requests.Request(), client_id)
            google_id = idinfo['sub']
            google_email = idinfo.get('email')
            google_name = f"{idinfo.get('given_name', '')} {idinfo.get('family_name', '')}".strip()
            google_picture = idinfo.get('picture')
            admin_user = request.user
            with transaction.atomic():
                if Usuario.objects.filter(email=google_email).exclude(pk=admin_user.pk).exists():
                    return Response({'error': 'O e-mail desta conta Google já está em uso por outro usuário.'}, status=status.HTTP_409_CONFLICT)
                if Usuario.objects.filter(google_id=google_id).exclude(pk=admin_user.pk).exists():
                    return Response({'error': 'Esta conta Google já está vinculada a outro usuário.'}, status=status.HTTP_409_CONFLICT)
                admin_user.email = google_email
                admin_user.nome = google_name
                admin_user.google_id = google_id
                fields_to_update = ['email', 'nome', 'google_id']
                if google_picture:
                    admin_user.foto_perfil = google_picture
                    fields_to_update.append('foto_perfil')
                admin_user.save(update_fields=fields_to_update)
            user_data = {
                'id_usuario': admin_user.id_usuario, 'email': admin_user.email, 'nome': admin_user.nome,
                'foto_perfil': admin_user.foto_perfil, 'data_criacao_conta': admin_user.data_criacao_conta.isoformat(),
                'id_perfil': admin_user.id_perfil.id_perfil if admin_user.id_perfil else None,
                'nome_perfil': admin_user.id_perfil.nome_perfil if admin_user.id_perfil else None,
                'google_id': admin_user.google_id,
                'tem_senha': admin_user.has_usable_password()
            }
            return Response({
                'detail': 'Conta Google vinculada e dados atualizados com sucesso.',
                'user_data': user_data
            }, status=status.HTTP_200_OK)
        except ValueError:
            return Response({'error': 'Token do Google inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Ocorreu um erro inesperado no servidor.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminLoginView(APIView):
    """
    Endpoint para autenticação de admin via e-mail e senha.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        if not email or not password:
            return Response({'error': 'Email e senha são obrigatórios.'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if user.id_perfil and user.id_perfil.nome_perfil == 'Administrador':
                user.ultimo_login = timezone.now()
                user.save()
                refresh = RefreshToken.for_user(user)
                response = Response({
                    'access': str(refresh.access_token),
                    'user_data': {
                        'id_usuario': user.id_usuario, 'email': user.email, 'nome': user.nome,
                        'foto_perfil': user.foto_perfil, 'data_criacao_conta': user.data_criacao_conta,
                        'id_perfil': user.id_perfil.id_perfil, 'nome_perfil': user.id_perfil.nome_perfil,
                        'google_id': user.google_id,
                        'tem_senha': user.has_usable_password()
                    }
                })
                response.set_cookie(
                    key='refresh_token', 
                    value=str(refresh), 
                    httponly=True, 
                    secure=True,
                    samesite='None', 
                    path='/'
                )
                return response
            else:
                return Response({'error': 'Acesso negado. Esta área é restrita para administradores.'}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({'error': 'Credenciais inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

class ChangePasswordView(APIView):
    """
    Endpoint para um admin logado alterar a própria senha.
    """
    permission_classes = [IsAuthenticated, IsAdministrador]

    def post(self, request):
        new_password = request.data.get('new_password')
        if not new_password or len(new_password) < 8:
            return Response(
                {"error": "A nova senha é obrigatória e deve ter no mínimo 8 caracteres."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user = request.user
        user.set_password(new_password)
        user.save(update_fields=['password'])
        return Response({"detail": "Senha alterada com sucesso."}, status=status.HTTP_200_OK)

class UserAPIView(APIView):
    """
    Endpoint para definir tipo do usuário ou deletar um usuário.
    """
    permission_classes = [IsAuthenticated]

    def put(self, request, id_usuario):
        usuario_logado = request.user
        is_admin = usuario_logado.id_perfil and usuario_logado.id_perfil.nome_perfil == 'Administrador'

        # Um usuário só pode editar a si mesmo, a menos que seja um administrador
        if not (usuario_logado.id_usuario == id_usuario or is_admin):
            return Response(
                {"error": "Você não tem permissão para alterar este perfil."},
                status=status.HTTP_403_FORBIDDEN
            )

        id_perfil_novo = request.data.get('id_perfil')
        if not id_perfil_novo:
            return Response({"error": "id_perfil is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            perfil_novo = PerfilAcesso.objects.get(id_perfil=id_perfil_novo)
            user_a_ser_editado = Usuario.objects.get(id_usuario=id_usuario)

            # Impede que um admin remova o próprio privilégio
            if (usuario_logado.id_usuario == user_a_ser_editado.id_usuario and is_admin and perfil_novo.nome_perfil != 'Administrador'):
                return Response(
                    {"error": "Administradores não podem remover o próprio privilégio."},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Se o usuário é rebaixado de admin, invalida a senha
            if user_a_ser_editado.id_perfil and user_a_ser_editado.id_perfil.nome_perfil == 'Administrador' and perfil_novo.nome_perfil != 'Administrador':
                user_a_ser_editado.set_unusable_password()

            user_a_ser_editado.id_perfil = perfil_novo
            user_a_ser_editado.save()
            return Response({"detail": "Perfil do usuário definido com sucesso"}, status=status.HTTP_200_OK)

        except PerfilAcesso.DoesNotExist:
            return Response({"error": "Perfil de acesso não encontrado"}, status=status.HTTP_404_NOT_FOUND)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuário não encontrado"}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, id_usuario):
        """
        Deleta um usuário. Apenas administradores podem fazer isso, e não podem deletar a si mesmos.
        """
        usuario_logado = request.user
        is_admin = usuario_logado.id_perfil and usuario_logado.id_perfil.nome_perfil == 'Administrador'

        if not is_admin:
            return Response({"error": "Apenas administradores podem remover usuários."}, status=status.HTTP_403_FORBIDDEN)

        if usuario_logado.id_usuario == id_usuario:
            return Response({"error": "Você não pode deletar sua própria conta."}, status=status.HTTP_403_FORBIDDEN)

        try:
            user_to_delete = Usuario.objects.get(id_usuario=id_usuario)
            user_to_delete.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Usuario.DoesNotExist:
            return Response({"error": "Usuário não encontrado."}, status=status.HTTP_404_NOT_FOUND)


class UserListView(generics.ListAPIView):
    """
    Endpoint para o admin listar todos os usuários.
    """
    queryset = Usuario.objects.all().order_by('nome')
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdministrador]

def health_check(request):
    """
    Função para "health check" que verifica se o app está funcionando.
    """
    data = { 'status': 'ok', 'message': 'App está rodando' }
    return JsonResponse(data)