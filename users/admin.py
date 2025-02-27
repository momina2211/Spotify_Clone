from django.contrib import admin
from users.models import UserProfile,User
# Register your models here.
admin.site.register(UserProfile)
admin.site.register(User)