from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework import generics, viewsets
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.contrib.auth import authenticate
from django.db.models import Count, Q
from users.models import *
from users.serializers import *
from users.role_enum import RoleEnum
from rest_framework.permissions import IsAuthenticated
from music.models import ArtistFollow, Song, Album


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


class ArtistViewSet(viewsets.ViewSet):
    """ViewSet for artist-related operations"""
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    @action(detail=False, methods=['get'])
    def list_artists(self, request):
        """List all artists"""
        artists = User.objects.filter(role=RoleEnum.ARTIST.value).annotate(
            song_count=Count('songs'),
            follower_count=Count('followers')
        )
        
        # Search filter
        search = request.query_params.get('search', None)
        if search:
            artists = artists.filter(username__icontains=search)
        
        results = [{
            'id': str(artist.id),
            'username': artist.username,
            'email': artist.email,
            'song_count': artist.song_count,
            'follower_count': artist.follower_count,
            'is_following': ArtistFollow.objects.filter(
                user=request.user,
                artist=artist
            ).exists() if request.user.is_authenticated else False
        } for artist in artists[:50]]
        
        return Response(results)

    @action(detail=True, methods=['post', 'delete'])
    def follow(self, request, pk=None):
        """Follow or unfollow an artist"""
        try:
            artist = User.objects.get(id=pk, role=RoleEnum.ARTIST.value)
        except User.DoesNotExist:
            return Response({"error": "Artist not found"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        if artist == request.user:
            return Response({"error": "Cannot follow yourself"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        if request.method == 'POST':
            follow, created = ArtistFollow.objects.get_or_create(
                user=request.user,
                artist=artist
            )
            if created:
                return Response({"message": f"Now following {artist.username}"}, 
                              status=status.HTTP_201_CREATED)
            return Response({"message": "Already following this artist"})
        
        elif request.method == 'DELETE':
            deleted = ArtistFollow.objects.filter(
                user=request.user,
                artist=artist
            ).delete()
            if deleted[0]:
                return Response({"message": f"Unfollowed {artist.username}"})
            return Response({"error": "Not following this artist"}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def following(self, request):
        """Get artists the user is following"""
        following = ArtistFollow.objects.filter(user=request.user).select_related('artist')
        artists = [f.artist for f in following]
        results = [{
            'id': str(artist.id),
            'username': artist.username,
            'email': artist.email,
            'song_count': artist.songs.count(),
            'followed_at': f.followed_at.isoformat()
        } for f, artist in zip(following, artists)]
        return Response(results)

    @action(detail=False, methods=['get'])
    def followers(self, request):
        """Get user's followers (if user is an artist)"""
        if request.user.role != RoleEnum.ARTIST.value:
            return Response({"error": "Only artists have followers"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        followers = ArtistFollow.objects.filter(artist=request.user).select_related('user')
        results = [{
            'id': str(f.user.id),
            'username': f.user.username,
            'email': f.user.email,
            'followed_at': f.followed_at.isoformat()
        } for f in followers]
        return Response(results)

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """Get artist profile with stats"""
        try:
            artist = User.objects.get(id=pk, role=RoleEnum.ARTIST.value)
        except User.DoesNotExist:
            return Response({"error": "Artist not found"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        profile_data = {
            'id': str(artist.id),
            'username': artist.username,
            'email': artist.email,
            'song_count': artist.songs.count(),
            'album_count': Album.objects.filter(user=artist).count(),
            'follower_count': ArtistFollow.objects.filter(artist=artist).count(),
            'total_plays': artist.songs.aggregate(total=Count('play_count'))['total'] or 0,
            'total_likes': artist.songs.aggregate(total=Count('likes'))['total'] or 0,
            'is_following': ArtistFollow.objects.filter(
                user=request.user,
                artist=artist
            ).exists() if request.user.is_authenticated else False
        }
        
        return Response(profile_data)

    @action(detail=True, methods=['get'])
    def songs(self, request, pk=None):
        """Get all songs by an artist"""
        try:
            artist = User.objects.get(id=pk, role=RoleEnum.ARTIST.value)
        except User.DoesNotExist:
            return Response({"error": "Artist not found"}, 
                          status=status.HTTP_404_NOT_FOUND)
        
        from music.serializers import SongSerializer
        songs = artist.songs.filter(visibility=1)  # Public songs only
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)