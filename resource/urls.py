from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecursoAdminViewSet, RecursoAgendamentosView

# Cria um router e registra nossas viewsets
router = DefaultRouter()
router.register(r'recursos', RecursoAdminViewSet, basename='recurso-admin')

urlpatterns = [
    path('', include(router.urls)),
    path('recursos/<int:id_recurso>/agendamentos/', RecursoAgendamentosView.as_view(), name='recurso-agendamentos'),
]
