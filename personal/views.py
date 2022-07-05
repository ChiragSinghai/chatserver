from django.shortcuts import render,redirect
from public_chatroom.models import PublicChatRoom
from public_chatroom.utils import create_new_room

# Create your views here.

def home_screen_view(request):
	context = {}
	user = request.user
	if user.is_authenticated:
		rooms = PublicChatRoom.objects.all()
		print("rooms: " + str(rooms))
		context['rooms'] = rooms


	if user.is_authenticated and user.is_staff:
		if request.method == "POST":
			title = request.POST.get("new_room_title")
			private = False
			if request.POST.get("authorization_private"):
				private = True
			room = create_new_room(title, private, user)
			return redirect("home")

	return render(request, "personal/home.html", context)
