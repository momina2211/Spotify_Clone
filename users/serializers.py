from rest_framework import serializers

from users.models import User, UserProfile
from users.role_enum import RoleEnum


class UserSerializer(serializers.ModelSerializer):
    email=serializers.EmailField()
    password=serializers.CharField(write_only=True)
    role=serializers.ChoiceField(choices=[(role.value,role.name.capitalize()) for role in RoleEnum],required=False)
    class Meta:
        model = User
        fields = ('id', 'email', 'password','role')

    def create(self, validated_data):
        validated_data['username'] = validated_data['email']
        user = User(**validated_data)
        user.set_password(validated_data['password'])
        user.save()
        return user

    def update(self, instance, validated_data):
        instance.email = validated_data.get('email', instance.email)
        instance.username = instance.email
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        if 'role' in validated_data:
            instance.role = validated_data['role']
        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    user=UserSerializer()
    class Meta:
        model = UserProfile
        fields = '__all__'


    def update(self, instance, validated_data):
        if 'profile_picture' in validated_data:
            instance.profile_picture = validated_data['profile_picture']
        instance.save()
        return instance

