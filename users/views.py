from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework import  generics
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from users.models import *
from users.serializers import *
from rest_framework.permissions import IsAuthenticated


class UserViewSet(generics.ListCreateAPIView, generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        role = request.data.get('role', RoleEnum.USER.value)
        UserProfile.objects.create(user=user, profile_type=role)
        token,created = Token.objects.get_or_create(user=user)
        response_data={
            'token': token.key,
            'user':serializer.data
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        role = request.data.get('role')
        if role is not None:
            user.profile.profile_type = role
            user.profile.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class LoginView(generics.GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            token= Token.objects.get(user=user)
            response_data = {
                'token': token.key,
                'user': {
                    'id': user.id,
                    'email': user.email,
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid email or password'}, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user.profile

    def get(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, *args, **kwargs):
        profile = self.get_object()
        serializer = self.get_serializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)