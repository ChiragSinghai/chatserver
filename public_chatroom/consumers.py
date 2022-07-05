import json
from .models import PublicChatRoom,PublicChatRoomMessage
from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from account.models import Account
from .utils import get_room
from account.utils import LazyAccountEncoder
from django.core.paginator import Paginator
from .utils import LazyRoomChatMessageEncoder


DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE = 20

class ChatConsumer(AsyncWebsocketConsumer):

    room_id: object

    async def connected(self,message):
        print('user connected')
        room = await get_room(self.room_id)
        user = self.scope['user']

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        if await self.UserConnected(room, user):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat.message',
                    'message': '',
                    'username': user.username,
                    'messageType': 'connect',
                    'user_id': user.id,
                }
            )

    async def leave(self,message):
        user = self.scope['user']
        room = await get_room(self.room_id)
        await self.userDisconnected(room, self.scope['user'])
        await self.remove_user(room,user)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'sendMessage',
                'message': 'has left the chat',
                'username': user.username,
                'messageType': 'left',
                'user_id': user.id,
                'profile_image':user.profile_image.url
            }
        )


    async def new_message(self,message):
        if message:
            user = self.scope['user']
            #await self.connected(message)
            room = await get_room(self.room_id)
            await self.channel_layer.group_send(
                room.group_name,
                {
                    "type": "sendMessage",
                    "profile_image": self.scope["user"].profile_image.url,
                    "username": self.scope["user"].username,
                    "user_id": self.scope["user"].id,
                    "message": message,
                    "messageType":"new"
                }
            )

            await self.createMessagedb(user,room,message)


    async def fetch_messages(self,page_number):
        await self.displaySpinner(True)
        room = await get_room(self.room_id)
        payload = await get_room_chat_messages(room,page_number)
        if payload:
            payload = json.loads(payload)
            try:
                await self.send(json.dumps(
                {
                    "messageType": "messages_payload",
                    "messages": payload['messages'],
                    "new_page_number": payload['new_page_number']
                },
                ))
            except Exception as e:
                print(e)
        await self.displaySpinner(False)


    async def join(self,message):
        user = self.scope['user']
        #await self.connected(message)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'sendMessage',
                'message': message,
                'username': user.username,
                'messageType':'joined',
                'user_id':user.id,
                'profile_image':user.profile_image.url
            }
        )

        room = await get_room(self.room_id)
        await self.connect_user(room,user)
        await self.UserConnected(room, user)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': '',
                'username': user.username,
                'messageType': 'connect',
                'user_id': user.id,
            }
        )

        #print('user added')

    async def getUsers(self,roomid):
        await self.displaySpinner(True)
        payload = await get_joined_users(roomid)

        payload = json.loads(payload)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'sendUsers',
                'messageType':'connectedUser',
                'connected_users':payload['connected_users'],
                'active_user':payload['active_user'],
            }
        )
        await self.displaySpinner(False)

    async def sendUsers(self,event):

        messageType = event['messageType']
        connected_users = event['connected_users']
        active_users = event['active_user']
        await self.send(text_data=json.dumps({
            'messageType':messageType,
            'connected_users':connected_users,
            'active_user':active_users,
        }))


    commands = {'fetch_messages': fetch_messages,
                'new_message': new_message,
                'join':join,
                'connect':connected,
                'left':leave,
                'getUsers':getUsers}

    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']

        self.room_group_name = 'chat_%s' % self.room_id




        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        print('user chat socket disconnected')
        user = self.scope['user']
        room = await get_room(self.room_id)
        await self.userDisconnected(room, self.scope['user'])
        #await self.leave(close_code)

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': '',
                'username': user.username,
                'messageType': 'connect',
                'user_id': user.id,
            }
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        command = text_data_json['command']
        print('command',command)
        await ChatConsumer.commands[command](self,message)

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username':username,
            'messageType':event["messageType"],
            'user_id':event['user_id'],

        }))

    async def sendMessage(self, event):
        print('here')
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'messageType': event['messageType'],
            'user_id': event['user_id'],
            'profile_image':event['profile_image'],
        }))


    async def displaySpinner(self,isDisplayed):
        await self.send(text_data=json.dumps({
            'messageType':'displaySpinner',
            'display':isDisplayed,
        }))

    @database_sync_to_async
    def connect_user(self, room, user):
        # add user to room list to show as "connected"
        account = Account.objects.get(pk=user.id)
        return room.add_user(account)

    @database_sync_to_async
    def UserConnected(self,room,user):
        account = Account.objects.get(pk=user.id)
        return room.connect_user(account)

    @database_sync_to_async
    def userDisconnected(self,room,user):
        account = Account.objects.get(pk=user.id)
        return room.disconnect_user(user)

    @database_sync_to_async
    def remove_user(self, room, user):
        # add user to room list to show as "connected"
        account = Account.objects.get(pk=user.id)
        return room.remove_user(account)

    @database_sync_to_async
    def createMessagedb(self,user,room,message):
        return PublicChatRoomMessage.objects.create(user=user, room=room, content=message)

@database_sync_to_async
def get_joined_users(room_id):
	try:
		publicRoom = PublicChatRoom.objects.get(pk=room_id)
		connected_users = publicRoom.users.all()

		active_users = publicRoom.connected_users.all()
		payload = {}
		s = LazyAccountEncoder()
		payload['active_user'] = s.serialize(active_users)
		payload['connected_users'] = s.serialize(connected_users)
		return json.dumps(payload)

	except Exception as e:
		print(e)
	return 'Nothing'



@database_sync_to_async
def get_room_chat_messages(room, page_number):
	try:
		qs = PublicChatRoomMessage.objects.by_room(room)
		p = Paginator(qs, DEFAULT_ROOM_CHAT_MESSAGE_PAGE_SIZE)

		payload = {}
		messages_data = None
		new_page_number = int(page_number)
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