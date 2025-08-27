from rest_framework import permissions

def _has_profile(user, profile_name):
    # Função auxiliar para verificar o perfil do usuário
    return (
        user and
        user.is_authenticated and
        user.id_perfil and
        user.id_perfil.nome_perfil == profile_name
    )

class IsAdministrador(permissions.BasePermission):
    # Permissão para acesso exclusivo de Administradores
    def has_permission(self, request, view):
        return _has_profile(request.user, 'Administrador')

class IsServidor(permissions.BasePermission):
    # Permissão para acesso exclusivo de Servidores
    def has_permission(self, request, view):
        return _has_profile(request.user, 'Servidor')

class IsTerceirizado(permissions.BasePermission):
    # Permissão para acesso exclusivo de Terceirizados
    def has_permission(self, request, view):
        return _has_profile(request.user, 'Terceirizado')