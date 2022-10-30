from django.shortcuts import render,redirect
from urllib.parse import urlencode
from django.urls import reverse
from privatechat.utils import find_or_create_private_chat
from django.conf import settings
from account.models import Account
from django.http import HttpResponse
from friend.models import FriendList
from .models import PrivateChatRoom,RoomChatMessage,UnreadChatRoomMessages
from account.utils import LazyAccountEncoder
from .utils import LazyRoomChatMessageEncoder
import json
from itertools import chain
from datetime import datetime
import pytz
from django.utils import timezone


# Create your views here.
DEBUG = False
def private_chat_room_view(request, *args, **kwargs):
	room_id = request.GET.get("room_id")
	user = request.user
	if not user.is_authenticated:
		base_url = reverse('login')
		query_string = urlencode({'next': f"/privatechat/?room_id={room_id}"})
		url = f"{base_url}?{query_string}"
		return redirect(url)
	try:
		account = Account.objects.get(pk=user.id)
	except Account.DoesNotExist:
		return HttpResponse("That user doesn't exist.")
	context = {}
	try:
		friend_list = FriendList.objects.get(user=account)
	except FriendList.DoesNotExist:
		friend_list = FriendList(user=account)
		friend_list.save()
	#context['m_and_f'] = get_recent_chatroom_messages(user)
	#context['friends'] = getChatMessage(user)

	context["BASE_URL"] = settings.BASE_URL
	if room_id:
		context["room_id"] = room_id
		room = PrivateChatRoom.objects.get(pk=room_id)
		context['room'] = room
	context['debug'] = DEBUG
	context['debug_mode'] = settings.DEBUG
	return render(request, "privatechat/room.html", context)


def create_or_return_private_chat(request, *args, **kwargs):
	user1 = request.user
	payload = {}
	if user1.is_authenticated:
		if request.method == "POST":
			user2_id = request.POST.get("user2_id")
			try:
				user2 = Account.objects.get(pk=user2_id)
				chat = find_or_create_private_chat(user1, user2)
				print("Successfully got the chat")
				payload['response'] = "Successfully got the chat."
				payload['chatroom_id'] = chat.id
			except Account.DoesNotExist:
				payload['response'] = "Unable to start a chat with that user."
	else:
		payload['response'] = "You can't start a chat if you are not authenticated."
	return HttpResponse(json.dumps(payload), content_type="application/json")


def getChatMessage(request,*args,**kwargs):
	user = request.user
	rooms1 = PrivateChatRoom.objects.filter(user1=user,is_active=False)
	rooms2 = PrivateChatRoom.objects.filter(user2=user,is_active=False)
	rooms = list(chain(rooms1,rooms2))
	payload = {}
	friendsMessage = []

	for room in rooms:
		if room.user1 == user:
			friend = room.user2
		else:
			friend = room.user1
		friend_list = FriendList.objects.get(user=user)
		if not friend_list.is_mutual_friend(friend):
			chat = find_or_create_private_chat(user, friend)
			chat.is_active = True
			chat.save()
		else:
			try:
				message = RoomChatMessage.objects.filter(room=room).latest("timestamp")
			except RoomChatMessage.DoesNotExist:
				today = datetime(
					year=1950,
					month=1,
					day=1,
					hour=1,
					minute=1,
					second=1,
					tzinfo=pytz.UTC
				)
				message = RoomChatMessage(
					user=friend,
					room=room,
					timestamp=today,
					content="",
				)
			try:
				chat = UnreadChatRoomMessages.objects.get(user=user, room=room)
				count = chat.count
			except:
				UnreadChatRoomMessages(room=room, user=user).save()
				count = 0


			friendsMessage.append({'message':message,'friend': friend,'count': count})


	content = sorted(friendsMessage, key=lambda x: x['message'].timestamp, reverse=True)

	s = LazyRoomChatMessageEncoder()
	A = LazyAccountEncoder()
	friend = []
	for element in content:
		context = A.serialize([element['friend']])[0]
		context.update(s.serialize([element['message']])[0])
		context.update({'count':element['count']})
		friend.append(context)

	payload['friends'] = friend


	return HttpResponse(json.dumps(payload), content_type="application/json")


def check_New_Messages(request,*args,**kwargs):
	payload = {}
	user = request.user
	#chat = UnreadChatRoomMessages.objects.get(user=user)
	try:
		chat = UnreadChatRoomMessages.objects.filter(user=user)

	except:
		UnreadChatRoomMessages(room=room, user=user).save()
		count = 0
	return HttpResponse(json.dumps(payload), content_type="application/json")






