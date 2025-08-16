from django.urls import path
from .views import PerfilAcessoView

urlpatterns = [
    path('perfil-acesso/', PerfilAcessoView.as_view(), name='perfil_acesso'),
]