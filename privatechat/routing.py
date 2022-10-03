from django.urls import re_path

from . import consumers
websocket_urlpatterns = [re_path(r'^privatechat/(?P<room_id>\w+)/$', consumers.PrivateChatConsumer.as_asgi())]