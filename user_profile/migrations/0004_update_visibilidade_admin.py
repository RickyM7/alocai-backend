from django.db import migrations

def update_visibilidade_admin(apps, schema_editor):
    PerfilAcesso = apps.get_model('user_profile', 'PerfilAcesso')
    PerfilAcesso.objects.filter(nome_perfil='Administrador').update(visibilidade=False)

class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0003_perfilacesso_visibilidade'),
    ]

    operations = [
        migrations.RunPython(update_visibilidade_admin),
    ]