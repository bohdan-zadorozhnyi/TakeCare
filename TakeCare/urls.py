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
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
