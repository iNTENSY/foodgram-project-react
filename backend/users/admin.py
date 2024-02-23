from django.contrib import admin

from users.models import User, Follow


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    pass
