from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from account.models import Account
# from django.core.exceptions import ValidationError
from account.forms import RegistrationForm
from django.contrib.auth.models import Group


# from django.contrib.auth.forms import UserCreationForm
from django import forms


# Register your models here.


class AccountAdmin(UserAdmin):
	list_display = ('email','username','date_joined', 'last_login', 'is_admin','is_staff')
	search_fields = ('email','username',)
	readonly_fields = ('id', 'date_joined', 'last_login')

	filter_horizontal = ()
	list_filter = ()
	fieldsets = (
		(None,{'fields':('email','password')}),
		('Permissions',{'fields':('is_admin',)}),
	)
	'''
	add_fieldsets = (
		(None,{
			'classes':('wide',),
			'fields':('email','username','password1','password2'),
		}),
	)
	'''


admin.site.register(Account, AccountAdmin)
