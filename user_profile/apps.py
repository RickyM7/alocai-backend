from django.apps import AppConfig


PERFIS_BASE = [
    {'nome_perfil': 'Administrador', 'descricao': 'Acesso total ao sistema', 'visibilidade': False},
    {'nome_perfil': 'Servidor',      'descricao': 'Pode solicitar e acompanhar agendamentos', 'visibilidade': True},
    {'nome_perfil': 'Terceirizado',  'descricao': 'Pode registrar uso imediato de recursos', 'visibilidade': True},
]


class UserProfileConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'user_profile'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(_seed_perfis, sender=self)


def _seed_perfis(sender, **kwargs):
    from user_profile.models import PerfilAcesso
    for perfil in PERFIS_BASE:
        PerfilAcesso.objects.get_or_create(nome_perfil=perfil['nome_perfil'], defaults=perfil)
