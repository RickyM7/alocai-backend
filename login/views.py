import os
from dotenv import load_dotenv

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

@csrf_exempt
def sign_in(request):
    """
    Renderiza a página de login. Se o usuário já estiver logado,
    mostra as informações dele.
    """
    # Constrói a URI de callback dinamicamente para não ter um link fixo.
    login_uri = request.build_absolute_uri(reverse('auth_receiver'))
    context = {
        'login_uri': login_uri,
         'google_client_id': os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
    }
    return render(request, 'login/sign_in.html', context)

@csrf_exempt
def auth_receiver(request):
    """
    URL chamada pelo Google depois que o usuário faz login com sucesso.
    Essa view verifica o token e cria a sessão do usuário.
    """
    token = request.POST.get('credential')

    if not token:
        # Se o Google não enviar a credencial
        return HttpResponse(status=400, content="Credential POST data not found.")

    try:
        client_id = os.environ.get('GOOGLE_OAUTH_CLIENT_ID')
        
        # Verifica se o token é válido
        user_data = id_token.verify_oauth2_token(
            token, requests.Request(), client_id
        )
    except ValueError:
        # Se o token for inválido
        return HttpResponse(status=403) # 403 Forbidden é apropriado aqui

    # Se o token for válido, os dados de usuário são salvos na sessão do Django
    request.session['user_data'] = user_data

    # Redireciona o usuário de volta para a página inicial, que agora o mostrará logado.
    return redirect('sign_in')

def sign_out(request):
    if 'user_data' in request.session:
        del request.session['user_data']
    return redirect('sign_in')