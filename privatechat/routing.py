from django.urls import re_path
from django.conf.urls import url
from . import consumers
websocket_urlpatterns = [url(r'^privatechat/(?P<room_id>\w+)/$', consumers.PrivateChatConsumer.as_asgi())]