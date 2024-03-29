"""
ASGI config for chatserver project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os
import django
from decouple import config
from channels.routing import get_default_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE",  "chatserver.settings")
django.setup()
import notify.routing
import public_chatroom.routing
import privatechat.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatserver.settings")
print('asgi')
application = ProtocolTypeRouter({
  "http": get_asgi_application(),
  "websocket": AuthMiddlewareStack(
        URLRouter(
            public_chatroom.routing.websocket_urlpatterns +
            privatechat.routing.websocket_urlpatterns +
            notify.routing.websocket_urlpatterns

        )
    ),
})

