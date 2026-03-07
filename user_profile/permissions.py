from rest_framework import permissions


def _has_profile(user, profile_name):
    return (
        user and
        user.is_authenticated and
        user.id_perfil and
        user.id_perfil.nome_perfil == profile_name
    )


class IsAdministrador(permissions.BasePermission):
    def has_permission(self, request, view):
        return _has_profile(request.user, 'Administrador')


class IsServidor(permissions.BasePermission):
    def has_permission(self, request, view):
        return _has_profile(request.user, 'Servidor')