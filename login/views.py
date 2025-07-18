import os
from dotenv import load_dotenv

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from google.oauth2 import id_token
from google.auth.transport import requests
from django.http import JsonResponse

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

class GoogleSignInAPIView(APIView):
    """
    Endpoint para autenticação com Google OAuth.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Recebe o token do Google e valida. Retorna os dados do usuário.
        """
        token = request.data.get('credential')

        if not token:
            return Response({'error': 'Credential not provided'}, status=400)

        try:
            client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
            
            # Verifica se o token é válido
            user_data = id_token.verify_oauth2_token(
                token, requests.Request(), client_id
            )

        except ValueError:
            return Response({'error': 'Invalid token'}, status=403)

        # Retorna os dados do usuário como resposta JSON
        return Response({'user_data': user_data}, status=200)


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

