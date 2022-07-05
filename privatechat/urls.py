from django.urls import path
from privatechat.views import *
app_name = 'privatechat'
urlpatterns = [path('', private_chat_room_view, name='private-chat-room'),
               path('create_or_return_private_chat/', create_or_return_private_chat, name='create-or-return-private-chat'),
               path('get_Chat_Message/', getChatMessage, name='get-chat-messages'),]