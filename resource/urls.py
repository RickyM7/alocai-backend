from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecursoAdminViewSet

# Cria um router e registra nossas viewsets
router = DefaultRouter()
router.register(r'recursos', RecursoAdminViewSet, basename='recurso-admin')

urlpatterns = [
    path('admin/', include(router.urls)),
]
