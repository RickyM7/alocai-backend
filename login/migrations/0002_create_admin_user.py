import os
from django.db import migrations
from django.contrib.auth.hashers import make_password

def create_admin_user(apps, schema_editor):
    Usuario = apps.get_model('login', 'Usuario')
    PerfilAcesso = apps.get_model('user_profile', 'PerfilAcesso')

    admin_password = os.environ.get('ADMIN_PASSWORD')
    admin_email = os.environ.get('ADMIN_EMAIL')

    if not admin_password or not admin_email:
        print("Variáveis de ambiente ADMIN_EMAIL ou ADMIN_PASSWORD não definidas. Pulando a criação do superusuário.")
        return

    try:
        admin_profile, created = PerfilAcesso.objects.get_or_create(
            nome_perfil='Administrador',
            defaults={'descricao': 'Gerencia todo o sistema, recursos e agendamentos.'}
        )

        user, created = Usuario.objects.get_or_create(
            email=admin_email,
            defaults={
                'nome': 'Administrador do Sistema',
                'password': make_password(admin_password),
                'id_perfil': admin_profile,
                'is_staff': True,
                'is_superuser': True
            }
        )

        if not created:
            user.id_perfil = admin_profile
            user.is_staff = True
            user.is_superuser = True
            user.set_password(admin_password)
            user.save()
            print(f"Usuário admin '{admin_email}' já existia e foi atualizado.")
        else:
            print(f"Usuário admin '{admin_email}' criado com sucesso.")

    except Exception as e:
        print(f"Ocorreu um erro ao tentar criar ou atualizar o usuário admin: {e}")


def remove_admin_user(apps, schema_editor):
    Usuario = apps.get_model('login', 'Usuario')
    admin_email = os.environ.get('ADMIN_EMAIL')
    if admin_email:
        Usuario.objects.filter(email=admin_email, id_perfil__nome_perfil='Administrador').delete()

class Migration(migrations.Migration):

    dependencies = [
        ('login', '0001_initial'),
        ('user_profile', '0002_seed_user_profiles'),
    ]

    operations = [
        migrations.RunPython(create_admin_user, reverse_code=remove_admin_user),
    ]