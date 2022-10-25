from django.urls import re_path
from django.conf.urls import url
from . import consumers

websocket_urlpatterns = [
    re_path(r'^public_chat/(?P<room_id>\w+)/$', consumers.ChatConsumer.as_asgi()),
]