import os
from dotenv import load_dotenv

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from google.oauth2 import id_token
from google.auth.transport import requests
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from .models import Usuario

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

        # Busca ou cria o usuário no sistema de autenticação do Django
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': user_data_from_google.get('given_name', ''),
                'last_name': user_data_from_google.get('family_name', ''),
            }
        )

        # Se o usuário foi criado agora, executa as ações de primeiro login
        if created:
            user.set_unusable_password()
            user.save()

            Usuario.objects.create(
                nome=f"{user.first_name} {user.last_name}".strip(),
                email=user.email,
                senha_hash='managed_by_google_oauth',
                status_conta='ativo'
            )

        # Gera os tokens para o usuário
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user_data': {
                'id': user.id,
                'email': user.email,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=200)


class GoogleSignOutAPIView(APIView):
    """
    Endpoint para logout do usuário.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Usando o JWT, o logout acontece no próprio frontend
        return Response({"detail": "User logged out successfully'"}, status=200)


# Função para "health check" que verifica se o app está funcionando
def health_check(request):
    data = {
        'status': 'ok',
        'message': 'App está rodando'
    }
    return JsonResponse(data)