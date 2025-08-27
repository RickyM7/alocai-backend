"""
URL configuration for alocai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from login.views import health_check # add rota de health_check
from resource.views import RecursoListView, DashboardView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    # Admin do Django
    path('django-admin/', admin.site.urls),
    
    # Nossas URLs de API
    path('', include('login.urls')),  # Inclui as rotas do app login
    path('health_check', health_check, name='health_check'),
    path('api/', include('booking.urls')),
    path('api/', include('user_profile.urls')),  # Inclui as rotas do app user_profile

    # URL pública para o dashboard
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),

    # URL para listar recursos para todos os usuários logados
    path('api/recursos/', RecursoListView.as_view(), name='listar-recursos'),
    
    # Rotas administrativas para gerenciamento de recursos
    path('api/admin/', include('resource.urls')),  # Inclui as rotas administrativas
    
    # Autenticação JWT
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
