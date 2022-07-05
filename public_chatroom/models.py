from django.db import models
from django.conf import settings


# Create your models here.
class PublicChatRoom(models.Model):
    """
        A room for people to chat in.
        """

    # Room title
    title = models.CharField(max_length=255, unique=True, blank=False, )

    # if not private, anyone with url can join. If private only admin or owner can add users
    private = models.BooleanField(default=False)

    # All users who have been invited to the chat. Must have at least 2 users
    users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="users")

    # Users who are currently connected to the chat socket
    connected_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="connected_users")

    # Users who have been invited but are not currently connected
    not_connected_users = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True,
                                                 related_name="not_connected_users")

    # Admin can add/remove users. Except not the owner. Must be at least one admin. B/c must be one owner.
    admins = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="admins")

    # All owners are admin, but not all admin are owners. Must always be at least one owner.
    owners = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name="owners")

    def __str__(self):
        return self.title

    def connect_user(self, user):
        """
        return true if user is added to the connected_users list
        """
        is_user_added = False
        if user in self.users.all():
            if not user in self.connected_users.all():
                self.connected_users.add(user)
                #self.not_connected_users.remove(user)
                is_user_added = True
                print('user went online')
        return is_user_added

    def disconnect_user(self, user):
        """
        return true if user is added to the not_connected_users list
        """
        is_user_removed = False
        print('hey',(user in self.users.all()))
        if user in self.users.all():
            if user in self.connected_users.all():
                #self.not_connected_users.add(user)
                self.connected_users.remove(user)
                is_user_removed = True
                print('user went offline')
        return is_user_removed

    def add_user(self,user):
        """
        return true if user is added from the users list
        """
        is_user_added = False
        if not user in self.users.all():
            self.users.add(user)
            is_user_added = True

        return is_user_added

    def remove_user(self, user):
        """
        return true if user is removed from the users list
        """
        is_user_removed = False

            # admin can't remove other admin, unless owner

        if user in self.users.all():
            self.users.remove(user)
            is_user_removed = True
            print('user_removed')
        return is_user_removed


    def add_admin(self, owner, user):
        """
        return true if user is added from the admins list
        """
        is_admin_added = False
        if self.is_owner(owner):
            if not user in self.admins.all():
                self.admins.add(user)
                is_admin_added = True
        return is_admin_added

    def remove_admin(self, owner, user):
        """
        return true if user is removed from the admins list
        """
        is_admin_removed = False
        if self.is_owner(owner):
            if user in self.admins.all():
                self.admins.remove(user)
                is_admin_removed = True
        return is_admin_removed

    def is_admin(self, account):
        if account in self.admins.all():
            return True
        return False

    def is_owner(self, account):
        if account in self.owners.all():
            return True
        return False

    @property
    def group_name(self):
        """
        Returns the Channels Group name that sockets should subscribe to to get sent
        messages as they are generated.
        """
        return "chat_%s" % self.id

class PublicRoomChatMessageManager(models.Manager):
	def by_room(self, room):
		qs = PublicChatRoomMessage.objects.filter(room=room).order_by('-timestamp')
		return qs

class PublicChatRoomMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    room = models.ForeignKey(PublicChatRoom,on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    content = models.TextField(unique=False,blank=False)

    objects = PublicRoomChatMessageManager()

    def __str__(self):
        self.content
