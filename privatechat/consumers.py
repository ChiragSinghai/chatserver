import json
from .models import PrivateChatRoom,RoomChatMessage,UnreadChatRoomMessages
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from account.models import Account
from .utils import find_or_create_private_chat
from account.utils import LazyAccountEncoder
from django.core.paginator import Paginator
import asyncio
from itertools import chain
from .utils import LazyRoomChatMessageEncoder,calculate_timestamp
from datetime import datetime
import pytz

class PrivateChatConsumer(AsyncWebsocketConsumer):

    async def sendUserInfo(self,roomid):
        await self.display_progress_bar(True)
        user = self.scope['user']
        other_user = await getOtherUser(roomid,user)
        payload = {}

        s = LazyAccountEncoder()
        payload['user_info'] = s.serialize([other_user])[0]
        print(payload)
        await self.send(json.dumps(payload))
        await self.display_progress_bar(False)

    async def getMessages(self,roomid,page_number):
        print('getting')
        await self.display_progress_bar(True)
        try:
            room = await getRoom(roomid)
            payload = await get_room_chat_messages(room,page_number)
            if payload:
                payload = json.loads(payload)
                await self.send(json.dumps(
                    {
                        "messages_payload": "messages_payload",
                        "messages": payload['messages'],
                        "new_page_number": payload['new_page_number']
                    },
                ))
        except Exception as e:
            print(e)

        await self.display_progress_bar(False)

    async def join(self,room_id):
        user = self.scope['user']
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        room = await getRoom(room_id)
        await connect_user(room,self.scope['user'])
        await self.send(json.dumps({'join':room_id}))
        await onUserConnected(room,user)

    async def newMessage(self,message,roomid):
        if str(roomid) == self.room_id:
            room = await getRoom(roomid)
            await create_room_chat_message(room,self.scope['user'],message)
            connected_users = room.connected_users.all()
            await appendUnreadMessage(room,room.user1_id,message,connected_users)
            await appendUnreadMessage(room, room.user2_id, message,connected_users)

            await self.channel_layer.group_send(
                room.group_name,
                {
                    "type": "chatMessage",
                    "profile_image": self.scope["user"].profile_image.url,
                    "username": self.scope["user"].username,
                    "user_id": self.scope["user"].id,
                    "message": message,
                }
            )

    async def fetchMessage(self):
        user = self.scope['user']
        friend = await getAllRooms(user)
        payload = {}
        payload['friends'] = friend
        await self.send(json.dumps(
            {
                'type':'details',
                "friends": payload['friends']
            },
        ))



    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        if self.room_id != '0':
            self.room_group_name = 'privatechat_%s' % self.room_id
            print('here')
        await self.accept()

    async def disconnect(self, close_code):
        print('disconnected')
        if self.room_id != '0':
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            room = await getRoom(self.room_id)
            await disconnect_user(room,self.scope['user'])

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        command = text_data_json['command']
        print('user called', command)
        if command == 'get_user_info':
            await self.sendUserInfo(text_data_json['room_id'])
        elif command == 'join':
            await self.join(text_data_json['room'])
            print('connected')
        elif command == 'send':
            if text_data_json['message']:
                await self.newMessage(text_data_json['message'],text_data_json['room'])
        elif command == "get_old_messages":
            await self.getMessages(text_data_json["room_id"],text_data_json["page_number"])

        elif command == "fetchNewMessage":
            await self.fetchMessage()




    async def chatMessage(self, event):
        timestamp = calculate_timestamp(timezone.now())

        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'newMessage': 'newMessage',
            'user_id': event['user_id'],
            'profile_image':event['profile_image'],
            "natural_timestamp": timestamp,
        }))

    async def display_progress_bar(self, is_displayed):
        await self.send(text_data=json.dumps(
            {
                "display_progress_bar": is_displayed
            }
        )
        )



@database_sync_to_async
def getOtherUser(roomId,user):
    room = PrivateChatRoom.objects.get(pk=roomId)
    other_user = room.user1
    print(room.user1,room.user2)

    if other_user == user:
        other_user = room.user2

    return other_user


@database_sync_to_async
def getRoom(roomId):
    room = PrivateChatRoom.objects.get(pk=roomId)
    return room

@database_sync_to_async
def get_room_chat_messages(room, page_number):
    try:
        qs = RoomChatMessage.objects.by_room(room)
        p = Paginator(qs, 20)

        payload = {}
        messages_data = None
        new_page_number = int(page_number)
        print(new_page_number,p.num_pages)
        print(new_page_number <= p.num_pages)
        if new_page_number <= p.num_pages:
            new_page_number = new_page_number + 1
            s = LazyRoomChatMessageEncoder()
            payload['messages'] = s.serialize(p.page(page_number).object_list)
        else:
            payload['messages'] = "None"
        payload['new_page_number'] = new_page_number
        return json.dumps(payload)
    except Exception as e:
        print("EXCEPTION: " + str(e))
    return None


@database_sync_to_async
def onUserConnected(room,user):
    connected_users = room.connected_users.all()
    if user in connected_users:
        try:
            unread_msgs = UnreadChatRoomMessages.objects.get(room=room, user=user)
            unread_msgs.count = 0
            unread_msgs.save()
        except UnreadChatRoomMessages.DoesNotExist:
            UnreadChatRoomMessages(room=room, user=user).save()
    return


@database_sync_to_async
def connect_user(room, user):
    # add user to connected_users list
    account = Account.objects.get(pk=user.id)
    return room.connect_user(account)


@database_sync_to_async
def disconnect_user(room, user):
    # remove from connected_users list
    account = Account.objects.get(pk=user.id)
    return room.disconnect_user(account)


@database_sync_to_async
def create_room_chat_message(room, user, message):
    return RoomChatMessage.objects.create(user=user, room=room, content=message)


@database_sync_to_async
def getChatCount(room,user):
    #user = Account.objects.get(pk=user)
    try:
        chats = UnreadChatRoomMessages.objects.filter(user=user)
    except:
        pass


@database_sync_to_async
def appendUnreadMessage(room,user,message,connected_user):
    user = Account.objects.get(pk=user)
    if not user in connected_user:
        print('the other user is offline')
        try:
            chat = UnreadChatRoomMessages.objects.get(user=user,room=room)
            chat.most_recent_message = message
            chat.count += 1
            chat.save()
        except:
            print('here in except')
            chat = UnreadChatRoomMessages(room=room,user=user)
            chat.count = 1
            chat.most_recent_message = message
            chat.save()
        return

@database_sync_to_async
def getAllRooms(user):
    rooms1 = PrivateChatRoom.objects.filter(user1=user, is_active=False)
    rooms2 = PrivateChatRoom.objects.filter(user2=user, is_active=False)
    rooms = list(chain(rooms1, rooms2))
    for room in rooms:
        print(room.user1)
    friendsMessage = []

    for room in rooms:

        if room.user1 == user:
            friend = room.user2
        else:
            friend = room.user1
        #print(friend)
        # friend_list = FriendList.objects.get(user=user)

        '''
        if not friend_list.is_mutual_friend(friend):
            chat = find_or_create_private_chat(user, friend)
            chat.is_active = False
            chat.save()
        else:
        '''
        if True:
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
            friendsMessage.append({'message': message, 'friend': friend, 'count': count})
    for f in friendsMessage:
        print('hey', f['message'].timestamp)
    content = sorted(friendsMessage, key=lambda x: x['message'].timestamp, reverse=True)

    s = LazyRoomChatMessageEncoder()
    A = LazyAccountEncoder()

    friend = []
    for element in content:
        context = A.serialize([element['friend']])[0]
        message = s.serialize([element['message']])[0]
        context.update({'message':message['message']})
        context.update({'count': element['count']})
        friend.append(context)
    return friend

