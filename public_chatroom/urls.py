from django.contrib import admin
from django.urls import path,include
from . import views
app_name = "public_chatroom"
urlpatterns = [
    path('<str:room_id>/',views.room,name='room'),
    path('<room_id>/get_chat_room_messages/',views.get_room_chat_messages,name='get_chat_room_messages'),

]