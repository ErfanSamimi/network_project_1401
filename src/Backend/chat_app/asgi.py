

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

import core.routing
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat_app.settings")
django_asgi_app = get_asgi_application()

import chat.routing


application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket":
            AuthMiddlewareStack(
                URLRouter(chat.routing.websocket_urlpatterns + core.routing.websocket_urlpatterns)
            )
    }
)