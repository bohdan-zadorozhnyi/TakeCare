"""
ASGI config for TakeCare project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from django.conf import settings
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'TakeCare.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import chat.routing
import notifications.routing

# Combine websocket URL patterns from both apps
all_websocket_urlpatterns = chat.routing.websocket_urlpatterns + notifications.routing.websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": ASGIStaticFilesHandler(get_asgi_application()),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(all_websocket_urlpatterns)
        )
    ),
})
