from django.contrib import admin

from users.models import User, Subscribe


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_filter = ('email', 'first_name')


@admin.register(Subscribe)
class SubscribeAdmin(admin.ModelAdmin):
    pass
