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
    path('referrals/', include('referrals.urls')),  # Added the referrals app URLs
    path('calendar/', include('calendar_app.urls')),  # Added the calendar app URLs
    path('articles/', include('articles.urls')),
    path('payments/', include('payments.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
