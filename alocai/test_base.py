from rest_framework.test import APITestCase
from login.models import Usuario
from user_profile.models import PerfilAcesso
from resource.models import Recurso
from booking.models import Agendamento, AgendamentoPai
from notification.models import Notificacao

class BaseTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        Usuario.objects.all().delete()
        PerfilAcesso.objects.all().delete()
        Recurso.objects.all().delete()
        Agendamento.objects.all().delete()
        AgendamentoPai.objects.all().delete()
        Notificacao.objects.all().delete()

        cls.admin_profile = PerfilAcesso.objects.create(nome_perfil='Administrador', visibilidade=False)
        cls.server_profile = PerfilAcesso.objects.create(nome_perfil='Servidor', visibilidade=True)

        cls.admin_user = Usuario.objects.create_user(
            email='admin@teste.com',
            nome='Admin User',
            password='password123',
            id_perfil=cls.admin_profile,
            is_staff=True,
            is_superuser=True
        )
        cls.server_user = Usuario.objects.create_user(
            email='servidor@teste.com',
            nome='Servidor User',
            password='password123',
            id_perfil=cls.server_profile
        )