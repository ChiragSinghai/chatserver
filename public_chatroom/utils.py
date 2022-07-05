from .models import PublicChatRoom
from channels.db import database_sync_to_async
from django.core.serializers.python import Serializer
from django.utils.encoding import smart_str as smart_text

def create_new_room(title, private, owner, users=None):
    room = PublicChatRoom(title=title, private=private)
    room.save()
    room.owners.add(owner)
    room.admins.add(owner)
    if not users:
        room.users.add(owner)
    else:
        users.add(owner)
        room.users.add(users)
    room.save()
    return room


@database_sync_to_async
def get_room(room_id):
    room = PublicChatRoom.objects.get(pk=room_id)
    return room

class LazyRoomChatMessageEncoder(Serializer):
	def get_dump_object(self, obj):
		dump_object = {}
		dump_object.update({'msg_id': str(obj.id)})
		dump_object.update({'user_id': str(obj.user.id)})
		dump_object.update({'username': str(obj.user.username)})
		dump_object.update({'message': str(obj.content)})
		dump_object.update({'profile_image': str(obj.user.profile_image.url)})
		return dump_object