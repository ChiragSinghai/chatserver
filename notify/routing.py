from django.urls import path

from . import consumers
websocket_urlpatterns = [path(r'^notify/', consumers.NotifyConsumer.as_asgi())]