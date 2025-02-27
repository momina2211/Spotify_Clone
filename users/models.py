import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from users.role_enum import RoleEnum

# Create your models here

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.IntegerField(choices=RoleEnum.choices(), default=RoleEnum.USER.value)

    def __str__(self):
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,related_name="profile")
    profile_type = models.IntegerField(choices=RoleEnum.choices(), default=RoleEnum.USER.value)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username