from django.urls import path
from .views import GoogleSignInAPIView, GoogleSignOutAPIView, UserAPIView, UserListView

urlpatterns = [
    path('api/google-sign-in/', GoogleSignInAPIView.as_view(), name='google_sign_in'),
    path('api/google-sign-out/', GoogleSignOutAPIView.as_view(), name='google_sign_out'),
    path('api/user/<int:id_usuario>/', UserAPIView.as_view(), name='user_api_view'),
    
    # Rota para o admin listar usuários
    path('api/admin/users/', UserListView.as_view(), name='admin_user_list'),
]