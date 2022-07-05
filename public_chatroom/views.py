from django.shortcuts import render,HttpResponse
from .models import PublicChatRoom,PublicChatRoomMessage
from account.models import Account
from account.utils import LazyAccountEncoder
from .utils import LazyRoomChatMessageEncoder
import json
from django.conf import settings



from django.core.paginator import Paginator
# Create your views here.
DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE = 20


def room(request, *args, **kwargs):
    room_id = kwargs.get("room_id")
    room = PublicChatRoom.objects.get(pk=room_id)
    context = {'room_id': room_id, 'room_name': room.title, 'has_joined': False,'debug_mode':settings.DEBUG}

    if request.user.is_authenticated:
        account = Account.objects.get(pk=request.user.id)
        if account in room.users.all():
            context['has_joined'] = True



    return render(request, 'public_chatroom/room.html',context)


def get_room_chat_messages(request, *args, **kwargs):
	if request.GET:
		has_joined_room = request.GET.get("has_joined_room")
		if has_joined_room == "true":
			room_id = request.GET.get("room_id")
			room = PublicChatRoom.objects.get(pk=room_id)
			qs = PublicChatRoomMessage.objects.by_room(room)
			page_number = request.GET.get("page_number")
			p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)
			# sleep(1) # for testing
			payload = {}
			messages_data = None
			new_page_number = int(page_number)
			# print("num pages: " + str(p.num_pages))
			if new_page_number <= p.num_pages:
				new_page_number = new_page_number + 1
				s = LazyRoomChatMessageEncoder()
				payload['messages'] = s.serialize(p.page(page_number).object_list)
			else:
				payload['messages'] = "None"
			payload['page_number'] = new_page_number
			return HttpResponse(json.dumps(payload), content_type="application/json")

	return HttpResponse("Something went wrong.")



