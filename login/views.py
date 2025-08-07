import os
from dotenv import load_dotenv

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from google.oauth2 import id_token
from google.auth.transport import requests
from django.http import JsonResponse
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken

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
            user_data = id_token.verify_oauth2_token(
                token, requests.Request(), client_id
            )
        except ValueError:
            return Response({'error': 'Invalid token'}, status=403)

        email = user_data.get('email')
        if not email:
            return Response({'error': 'Email not found in Google token'}, status=400)

        # Busca ou cria o usuário
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': user_data.get('given_name', ''),
                'last_name': user_data.get('family_name', ''),
            }
        )

        # Se o usuário foi criado agora, define uma senha inutilizável
        if created:
            user.set_unusable_password()
            user.save()

        # Gera os tokens para o usuário
        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            }
        }, status=200)


class GoogleSignOutAPIView(APIView):
    """
    Endpoint para logout do usuário.
    """
    def post(self, request):
        """
        Remove os dados do usuário da sessão.
        """
        if 'user_data' in request.session:
            del request.session['user_data']
            return Response({'message': 'User logged out successfully'}, status=200)
        return Response({'error': 'No user logged in'}, status=400)


# Função para "health check" que verifica se o app está funcionando
def health_check(request):
    data = {
        'status': 'ok',
        'message': 'App está rodando'
    }
    return JsonResponse(data)



