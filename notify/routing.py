from django.urls import re_path

from . import consumers
websocket_urlpatterns = [re_path(r'^notify/', consumers.NotifyConsumer.as_asgi())]