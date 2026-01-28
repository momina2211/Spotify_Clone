from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q, F, Count
from django.utils import timezone
from datetime import timedelta
from music.models import (
    Song, Genre, Album, SongLike, RecentlyPlayed, 
    FavoriteSong, FavoriteAlbum, ArtistFollow
)
from music.serializers import SongSerializer, GenreSerializer, AlbumSerializer
from music.utils import upload_to_s3, get_or_create_genre, validate_audio_file
from rest_framework.authentication import TokenAuthentication
from music.permissions import IsArtistOrReadOnly
from music.music_enum import Visibility

class SongViewSet(viewsets.ModelViewSet):
    """Viewset for managing song uploads"""

    queryset = Song.objects.all()
    serializer_class = SongSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsArtistOrReadOnly]
    authentication_classes = [TokenAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'genre__title', 'album__title', 'user__username']
    ordering_fields = ['play_count', 'likes', 'release_date', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Song.objects.all()
        
        # Filter by visibility
        public_filter = Q(visibility=Visibility.PUBLIC.value)
        if user.is_authenticated and getattr(user, 'role', None) == 2:
            queryset = queryset.filter(public_filter | Q(user=user))
        else:
            queryset = queryset.filter(public_filter)
        
        # Filter by genre
        genre = self.request.query_params.get('genre', None)
        if genre:
            queryset = queryset.filter(genre__title__icontains=genre)
        
        # Filter by artist
        artist = self.request.query_params.get('artist', None)
        if artist:
            queryset = queryset.filter(user__username__icontains=artist)
        
        # Filter by album
        album = self.request.query_params.get('album', None)
        if album:
            queryset = queryset.filter(album__title__icontains=album)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(release_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(release_date__lte=date_to)
        
        return queryset.select_related('user', 'album', 'genre')

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get("audio_file")
        if not file_obj:
            return Response({"error": "No audio file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate audio file
        validation_error = validate_audio_file(file_obj)
        if validation_error:
            return Response({"error": validation_error}, status=status.HTTP_400_BAD_REQUEST)

        file_url = upload_to_s3(file_obj)
        if not file_url:
            return Response({"error": "S3 upload failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Prepare the request data
        request.data["audio_file"] = file_url

        # Use the genre as a string
        genre_title = request.data.get("genre")
        if not genre_title:
            return Response({"error": "Genre is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Create or get the genre
        genre, created = get_or_create_genre(genre_title,request.user)
        request.data["genre"] = genre.title  # Set the genre title

        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        song_instance = serializer.save(user=request.user)

        return Response(SongSerializer(song_instance).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        song = self.get_object()
        like, created = SongLike.objects.get_or_create(user=request.user, song=song)
        if created:
            song.likes = F('likes') + 1
            song.save(update_fields=['likes'])
            song.refresh_from_db(fields=['likes'])
        return Response({"likes": song.likes})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        song = self.get_object()
        deleted, _ = SongLike.objects.filter(user=request.user, song=song).delete()
        if deleted:
            song.likes = F('likes') - 1
            song.save(update_fields=['likes'])
            song.refresh_from_db(fields=['likes'])
        return Response({"likes": song.likes})

    @action(detail=True, methods=['post'])
    def play(self, request, pk=None):
        song = self.get_object()
        song.play_count = F('play_count') + 1
        song.save(update_fields=['play_count'])
        song.refresh_from_db(fields=['play_count'])
        
        # Track recently played for authenticated users
        if request.user.is_authenticated:
            RecentlyPlayed.objects.update_or_create(
                user=request.user,
                song=song,
                defaults={'played_at': timezone.now()}
            )
        
        return Response({"play_count": song.play_count})

    @action(detail=False, methods=['get'])
    def trending(self, request):
        limit = int(request.query_params.get('limit', 20))
        time_range = request.query_params.get('time_range', 'all')  # all, week, month
        
        queryset = self.get_queryset()
        
        # Filter by time range
        if time_range == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            queryset = queryset.filter(created_at__gte=week_ago)
        elif time_range == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            queryset = queryset.filter(created_at__gte=month_ago)
        
        queryset = queryset.order_by('-play_count', '-likes')[:limit]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def search(self, request):
        """Advanced search endpoint"""
        query = request.query_params.get('q', '')
        search_type = request.query_params.get('type', 'all')  # all, song, album, artist
        
        if not query:
            return Response({"error": "Query parameter 'q' is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        results = {}
        
        if search_type in ['all', 'song']:
            songs = self.get_queryset().filter(
                Q(title__icontains=query) |
                Q(genre__title__icontains=query) |
                Q(album__title__icontains=query) |
                Q(user__username__icontains=query)
            )[:20]
            results['songs'] = SongSerializer(songs, many=True).data
        
        if search_type in ['all', 'album']:
            albums = Album.objects.filter(
                Q(title__icontains=query) |
                Q(user__username__icontains=query)
            )[:20]
            results['albums'] = AlbumSerializer(albums, many=True).data
        
        if search_type in ['all', 'artist']:
            from users.models import User
            from users.role_enum import RoleEnum
            artists = User.objects.filter(
                role=RoleEnum.ARTIST.value,
                username__icontains=query
            )[:20]
            results['artists'] = [
                {
                    'id': str(artist.id),
                    'username': artist.username,
                    'email': artist.email,
                    'song_count': artist.songs.count()
                }
                for artist in artists
            ]
        
        return Response(results)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Add or remove song from favorites"""
        song = self.get_object()
        
        if request.method == 'POST':
            favorite, created = FavoriteSong.objects.get_or_create(
                user=request.user,
                song=song
            )
            if created:
                return Response({"message": "Song added to favorites"}, 
                              status=status.HTTP_201_CREATED)
            return Response({"message": "Song already in favorites"})
        
        elif request.method == 'DELETE':
            deleted = FavoriteSong.objects.filter(
                user=request.user,
                song=song
            ).delete()
            if deleted[0]:
                return Response({"message": "Song removed from favorites"})
            return Response({"error": "Song not in favorites"}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def favorites(self, request):
        """Get user's favorite songs"""
        favorites = FavoriteSong.objects.filter(user=request.user).select_related('song')
        songs = [fav.song for fav in favorites]
        serializer = self.get_serializer(songs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def recently_played(self, request):
        """Get user's recently played songs"""
        limit = int(request.query_params.get('limit', 50))
        recent = RecentlyPlayed.objects.filter(
            user=request.user
        ).select_related('song').order_by('-played_at')[:limit]
        songs = [r.song for r in recent]
        serializer = self.get_serializer(songs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def random(self, request):
        """Get random songs"""
        limit = int(request.query_params.get('limit', 10))
        queryset = self.get_queryset().order_by('?')[:limit]
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recommendations(self, request):
        """Get song recommendations based on user's listening history"""
        if not request.user.is_authenticated:
            # Return trending songs for non-authenticated users
            return self.trending(request)
        
        limit = int(request.query_params.get('limit', 20))
        
        # Get user's favorite genres
        favorite_genres = FavoriteSong.objects.filter(
            user=request.user
        ).values_list('song__genre__id', flat=True).distinct()
        
        # Get songs from favorite genres
        if favorite_genres:
            recommended = self.get_queryset().filter(
                genre__id__in=favorite_genres
            ).exclude(
                id__in=FavoriteSong.objects.filter(user=request.user).values_list('song__id', flat=True)
            ).order_by('-play_count', '-likes')[:limit]
        else:
            # Fallback to trending
            recommended = self.get_queryset().order_by('-play_count', '-likes')[:limit]
        
        serializer = self.get_serializer(recommended, many=True)
        return Response(serializer.data)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsArtistOrReadOnly]
    authentication_classes = [TokenAuthentication]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [IsArtistOrReadOnly]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'user__username']
    ordering_fields = ['release_date', 'created_at']
    ordering = ['-release_date']

    def get_queryset(self):
        queryset = Album.objects.all()
        
        # Filter by artist
        artist = self.request.query_params.get('artist', None)
        if artist:
            queryset = queryset.filter(user__username__icontains=artist)
        
        # Filter by date range
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(release_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(release_date__lte=date_to)
        
        return queryset.select_related('user').prefetch_related('songs')

    def create(self, request, *args, **kwargs):
        # Validate cover image if provided
        cover_image = request.FILES.get('cover_image')
        if cover_image:
            from music.utils import validate_image_file
            validation_error = validate_image_file(cover_image)
            if validation_error:
                return Response({"error": validation_error}, 
                              status=status.HTTP_400_BAD_REQUEST)
        
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Add or remove album from favorites"""
        album = self.get_object()
        
        if request.method == 'POST':
            favorite, created = FavoriteAlbum.objects.get_or_create(
                user=request.user,
                album=album
            )
            if created:
                return Response({"message": "Album added to favorites"}, 
                              status=status.HTTP_201_CREATED)
            return Response({"message": "Album already in favorites"})
        
        elif request.method == 'DELETE':
            deleted = FavoriteAlbum.objects.filter(
                user=request.user,
                album=album
            ).delete()
            if deleted[0]:
                return Response({"message": "Album removed from favorites"})
            return Response({"error": "Album not in favorites"}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def favorites(self, request):
        """Get user's favorite albums"""
        favorites = FavoriteAlbum.objects.filter(user=request.user).select_related('album')
        albums = [fav.album for fav in favorites]
        serializer = self.get_serializer(albums, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def songs(self, request, pk=None):
        """Get all songs in an album"""
        album = self.get_object()
        songs = album.songs.all()
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)