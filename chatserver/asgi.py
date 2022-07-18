"""
ASGI config for chatserver project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""

import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.handlers.asgi import ASGIHandler


def get_asgi_application():
    """
    The public interface to Django's ASGI support. Return an ASGI 3 callable.

    Avoids making django.core.handlers.ASGIHandler a public API, in case the
    internal implementation changes or moves in the future.
    """
    django.setup(set_prefix=False)
    return ASGIHandler()


# from django.core.asgi import get_asgi_application

import notify.routing
import public_chatroom.routing
import privatechat.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatserver.settings")

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
