from django.contrib import admin
from friend.models import FriendList,FriendRequest
# Register your models here.

class FriendListAdmin(admin.ModelAdmin):
    list_filter = ['user']
    list_display = ['user']
    search_fields = ['user']
    readonly_fields = ['user']

    class Meta:
        model = FriendList

    def has_add_permission(request,obj=None):
        return False

    def has_change_permission(request, obj=None):
        return False

admin.site.register(FriendList,FriendListAdmin)


class FriendRequestAdmin(admin.ModelAdmin):
    list_filter = ['sender','receiver']
    list_display = ['sender','receiver']
    search_fields = ['sender__username','sender__email','receiver__username','receiver__email']

    def has_add_permission(request,obj=None):
        return False

    def has_change_permission(request, obj=None):
        return False

    class Meta:
        model = FriendRequest

admin.site.register(FriendRequest,FriendRequestAdmin)