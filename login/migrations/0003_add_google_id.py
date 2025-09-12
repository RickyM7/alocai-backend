from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('login', '0002_create_admin_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='usuario',
            name='google_id',
            field=models.CharField(blank=True, db_index=True, max_length=255, null=True, unique=True),
        ),
    ]