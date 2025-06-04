from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include

from TakeCare import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('TakeCare.api')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('', include('core.urls', namespace='core')),
    path('', include('appointments.urls')),
    path('chat/', include('chat.urls')),
    path('prescriptions/', include('prescriptions.urls')),
    path('referrals/', include('referrals.urls')),
    path('calendar/', include('calendar_app.urls')),
    path('articles/', include('articles.urls')),
    path('notifications/', include('notifications.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
