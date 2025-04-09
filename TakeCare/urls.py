from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('TakeCare.api')),
    path('accounts/', include('accounts.urls')),
    path('', include('core.urls')),
    path('chat/', include('chat.urls')),
]
