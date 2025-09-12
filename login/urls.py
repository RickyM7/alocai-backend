from django.urls import path
from .views import GoogleSignInAPIView, GoogleSignOutAPIView, UserAPIView, UserListView, AdminLoginView, LinkGoogleAccountView, ChangePasswordView

urlpatterns = [
    path('api/google-sign-in/', GoogleSignInAPIView.as_view(), name='google_sign_in'),
    path('api/google-sign-out/', GoogleSignOutAPIView.as_view(), name='google_sign_out'),
    path('api/user/<int:id_usuario>/', UserAPIView.as_view(), name='user_api_view'),
    
    # Rota para o admin listar usuários
    path('api/admin/users/', UserListView.as_view(), name='admin_user_list'),
    # Rota para o admin logar com usuário e senha
    path('api/admin/login/', AdminLoginView.as_view(), name='admin_login'),
    # Rota pra linkar conta google à conta de admin
    path('api/admin/link-google/', LinkGoogleAccountView.as_view(), name='admin_link_google'),
    # Rota para o admin editar a própria senha
    path('api/admin/change-password/', ChangePasswordView.as_view(), name='admin_change_password'),
]