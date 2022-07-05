from channels.generic.websocket import AsyncWebsocketConsumer
import json
from .constants import *
from channels.db import database_sync_to_async
from django.contrib.contenttypes.models import ContentType
from friend.models import FriendList,FriendRequest
from .models import Notify
from django.core.paginator import Paginator
from .utils import LazyNotificationEncoder
from datetime import datetime
from privatechat.models import UnreadChatRoomMessages

class NotifyConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print('connect notification')
        await self.accept()

    async def sendCount(self):
        user = self.scope['user']
        count = await get_unread_message_count(user)
        await self.send(json.dumps(
            {
                'msg_type':UNREAD_MESSAGE_COUNT,
                "count": count
            },
        ))

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        command = text_data_json['command']
        print('user called', command)
        if command =="get_unread_notification_count":
            count = await get_unread_notification_count(self.scope['user'])
            if count != None:
                await self.send_unread_notification_count(count)
        if command == "get_all_notifications":
            payload = await get_all_notifications(self.scope['user'],text_data_json['page_number'])
            if not payload:
                await self.send_pagination_exhausted()
            else:
                await self.send_all_notifications(payload)

        if command == "accept_friend_request":
            payload = await accept_friend_request(self.scope['user'],text_data_json['notificationId'])
            if payload:
                await self.send_updated_request_status(payload['notification'])

        if command == "decline_friend_request":
            payload = await decline_friend_request(self.scope['user'],text_data_json['notificationId'])
            if payload:
                await self.send_updated_request_status(payload['notification'])

        if command == "new_notifications":
            payload = await get_new_notifications(self.scope["user"], text_data_json.get("newest_timestamp", None))
            if payload:
                await self.send_new_notifications(payload['notifications'])

        if command == "refresh_notification":
            print(text_data_json['oldest_timestamp'],text_data_json['newest_timestamp'])
            payload = await refresh_notification(self.scope['user'],text_data_json['oldest_timestamp'],
                                                 text_data_json['newest_timestamp'])
            if payload:
                await self.send_refresh_notification(payload['notifications'])

        if command == 'mark_notification_read':
            await mark_notifications_read(self.scope['user'])

        if command == "unreadMessageCount":
            await self.sendCount()

    async def disconnect(self, close_code):
        print('disconnected')


    async def send_unread_notification_count(self,count):
        await self.send(json.dumps(
            {
                "count": count,
                "msg_type":UNREAD_NOTIFICATION_COUNT,
            },
        ))

    async def send_pagination_exhausted(self):
        await self.send(json.dumps(
            {
                "msg_type":NOTIFICATION_EXHAUSTED,
            }
        ))

    async def send_all_notifications(self,payload):
        await self.send(json.dumps(
            {
                "msg_type":ALL_NOTIFICATION,
                "new_page_number":payload['new_page_number'],
                "notifications":payload['notifications'],
            }
        ))

    async def send_updated_request_status(self,notification):
        await self.send(json.dumps({
            'msg_type':UPDATED_STATUS,
            'notification':notification,
        }))

    async def send_new_notifications(self,notification):
        await self.send(json.dumps({
            'msg_type':NEW_MESSAGES,
            'notification':notification,
        }))

    async def send_refresh_notification(self,notification):
        await self.send(json.dumps({
            'msg_type': REFRESH_MESSAGE,
            'notification':notification,
        }))



@database_sync_to_async
def get_all_notifications(user,page_number):
    if user.is_authenticated:
        friendRequest_ct = ContentType.objects.get_for_model(FriendRequest)
        friendList_ct = ContentType.objects.get_for_model(FriendList)
        notifications = Notify.objects.filter(target=user,content_type__in=[friendRequest_ct,friendList_ct]).order_by('-timestamp')
        p = Paginator(notifications,DEFAULT_PAGE_SIZE)
        payload = {}
        if len(notifications)>0:
            if p.num_pages >= int(page_number):
                s = LazyNotificationEncoder()
                serialized_object = s.serialize(p.page(page_number).object_list)
                payload['notifications'] = serialized_object
                new_page_number = int(page_number) + 1
                payload['new_page_number'] = new_page_number
                return payload


@database_sync_to_async
def get_new_notifications(user, newest_timestamp):
    payload = {}
    if user.is_authenticated:
        timestamp = newest_timestamp[0:newest_timestamp.find("+")] # remove timezone because who cares
        timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
        friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
        friend_list_ct = ContentType.objects.get_for_model(FriendList)
        notifications = Notify.objects.filter(target=user, content_type__in=[friend_request_ct, friend_list_ct], timestamp__gt=timestamp, read=False).order_by('-timestamp')
        s = LazyNotificationEncoder()
        payload['notifications'] = s.serialize(notifications)
    return payload



@database_sync_to_async
def get_unread_notification_count(user):
    if user.is_authenticated:
        friendRequest_ct = ContentType.objects.get_for_model(FriendRequest)
        friendList_ct = ContentType.objects.get_for_model(FriendList)
        notifications = Notify.objects.filter(target=user,content_type__in=[friendRequest_ct,friendList_ct])
        count=0
        if notifications:
            for notification in notifications.all():
                if not notification.read:
                    count+=1
        return count

@database_sync_to_async
def decline_friend_request(user,notificationId):
    payload={}
    if user.is_authenticated:

        notification = Notify.objects.get(pk=notificationId)
        friend_request = notification.content_object
        # confirm this is the correct user
        if friend_request.receiver == user:
            # accept the request and get the updated notification
            updated_notification = friend_request.decline()

            # return the notification associated with this FriendRequest
            s = LazyNotificationEncoder()
            payload['notification'] = s.serialize([updated_notification])[0]
        return payload



@database_sync_to_async
def accept_friend_request(user, notificationId):
    payload = {}
    if user.is_authenticated:

        notification = Notify.objects.get(pk=notificationId)
        friend_request = notification.content_object
        # confirm this is the correct user
        if friend_request.receiver == user:
            # accept the request and get the updated notification
            updated_notification = friend_request.accept()
            # return the notification associated with this FriendRequest
            s = LazyNotificationEncoder()
            payload['notification'] = s.serialize([updated_notification])[0]
        return payload


@database_sync_to_async
def refresh_notification(user, oldest_timestamp, newest_timestamp):
    payload = {}
    if user.is_authenticated:
        oldest_ts = oldest_timestamp[0:oldest_timestamp.find("+")]  # remove timezone because who cares
        oldest_ts = datetime.strptime(oldest_ts, '%Y-%m-%d %H:%M:%S.%f')
        newest_ts = newest_timestamp[0:newest_timestamp.find("+")]  # remove timezone because who cares
        newest_ts = datetime.strptime(newest_ts, '%Y-%m-%d %H:%M:%S.%f')
        friend_request_ct = ContentType.objects.get_for_model(FriendRequest)
        friend_list_ct = ContentType.objects.get_for_model(FriendList)
        notifications = Notify.objects.filter(target=user, content_type__in=[friend_request_ct, friend_list_ct],
                                                    timestamp__gte=oldest_ts, timestamp__lte=newest_ts).order_by(
            '-timestamp')

        s = LazyNotificationEncoder()
        payload['notifications'] = s.serialize(notifications)
    return payload


@database_sync_to_async
def mark_notifications_read(user):
	if user.is_authenticated:
		notifications = Notify.objects.filter(target=user)
		if notifications:
			for notification in notifications.all():
				notification.read = True
				notification.save()
	return

@database_sync_to_async
def get_unread_message_count(user):
    if user.is_authenticated:
        count = 0
        messages = UnreadChatRoomMessages.objects.filter(user=user)
        if messages:
            for message in messages.all():
                if message.count:
                    count += 1
            print(count)
            return count
