from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from decouple import config


class Command(BaseCommand):
    help = 'Cria o usuário administrador inicial a partir das variáveis de ambiente ADMIN_EMAIL e ADMIN_PASSWORD.'

    def handle(self, *args, **options):
        # Import aqui para evitar problemas de importação circular no boot
        from login.models import Usuario
        from user_profile.models import PerfilAcesso

        admin_email = config('ADMIN_EMAIL', default='')
        admin_password = config('ADMIN_PASSWORD', default='')

        if not admin_email or not admin_password:
            self.stderr.write(self.style.WARNING(
                'ADMIN_EMAIL ou ADMIN_PASSWORD não definidos no .env. Abortando.'
            ))
            return

        try:
            admin_profile = PerfilAcesso.objects.get(nome_perfil='Administrador')
        except PerfilAcesso.DoesNotExist:
            self.stderr.write(self.style.ERROR(
                "Perfil 'Administrador' não encontrado. Execute as migrations primeiro."
            ))
            return

        user, created = Usuario.objects.get_or_create(
            email=admin_email,
            defaults={
                'email_admin': admin_email,
                'nome': 'Administrador do Sistema',
                'password': make_password(admin_password),
                'id_perfil': admin_profile,
                'is_staff': True,
                'is_superuser': True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Admin '{admin_email}' criado com sucesso."))
        else:
            self.stdout.write(self.style.WARNING(f"Admin '{admin_email}' já existe. Nenhuma ação foi tomada."))
