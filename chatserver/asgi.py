"""
ASGI config for chatserver project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/howto/deployment/asgi/
"""


import os
import django
#from decouple import config
#from channels.routing import get_default_application
from django.urls import re_path,path
from . import consumers

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
#from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE",  "chatserver.settings")
django.setup()
from notify.consumers import NotifyConsumer
from public_chatroom.consumers import ChatConsumer
from privatechat.consumers import PrivateChatConsumer
#import notify.routing
#import public_chatroom.routing
#import privatechat.routing

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatserver.settings")

application = ProtocolTypeRouter({
	'websocket': AllowedHostsOriginValidator(
		AuthMiddlewareStack(
			URLRouter([
					re_path(r'/notify/', NotifyConsumer),
                    re_path(r'^privatechat/(?P<room_id>\w+)/$', PrivateChatConsumer),
					re_path(r'^public_chat/(?P<room_id>\w+)/$', ChatConsumer),
			])
		)
	),
})

'''
application = ProtocolTypeRouter({
  "websocket": AuthMiddlewareStack(
        URLRouter(
            public_chatroom.routing.websocket_urlpatterns +
            privatechat.routing.websocket_urlpatterns +
            notify.routing.websocket_urlpatterns

        )
    ),
})

'''
'''
import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.handlers.asgi import ASGIHandler


# from django.core.asgi import get_asgi_application



os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chatserver.settings")

import notify.routing
import public_chatroom.routing
import privatechat.routing
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
'''