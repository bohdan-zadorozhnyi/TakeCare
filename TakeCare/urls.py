from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path, include

from TakeCare import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('TakeCare.api')),
    path('accounts/', include('accounts.urls')),
    path('', include('core.urls')),
    path('', include('appointments.urls')),
    path('chat/', include('chat.urls')),
    path('prescriptions/', include('prescriptions.urls')),
    path('calendar/', include('calendar_app.urls')),  # Added the calendar app URLs
    path('notifications/', include('notifications.urls')),  # Add notification URLs
    path('referrals/', include('referrals.urls')),  # Add referrals URLs
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
