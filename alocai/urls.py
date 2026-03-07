from django.contrib import admin
from django.urls import include, path
from login.views import health_check, CookieTokenRefreshView
from resources.views import RecursoListView, DashboardView, CalendarAgendamentosView
from rest_framework_simplejwt.views import TokenObtainPairView

urlpatterns = [
    path('django-admin/', admin.site.urls),

    path('', include('login.urls')),
    path('health_check', health_check, name='health_check'),
    path('api/', include('booking.urls')),
    path('api/', include('user_profile.urls')),
    path('api/', include('notification.urls')),

    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/dashboard/calendar/', CalendarAgendamentosView.as_view(), name='dashboard-calendar'),
    path('api/recursos/', RecursoListView.as_view(), name='listar-recursos'),
    path('api/admin/', include('resources.urls')),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
]