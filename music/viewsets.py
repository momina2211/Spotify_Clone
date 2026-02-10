from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q, F, Count, Max as MaxFunc, Sum, Avg
from django.utils import timezone
from datetime import timedelta
from music.models import (
    Song, Genre, Album, SongLike, RecentlyPlayed, 
    FavoriteSong, FavoriteAlbum, ArtistFollow, Playlist, PlaylistSong,
    SongAnalytics
)
from music.serializers import (
    SongSerializer, GenreSerializer, AlbumSerializer, PlaylistSerializer, 
    PlaylistSongSerializer, SongAnalyticsSerializer
)
from music.utils import (
    get_or_create_genre, validate_audio_file, validate_image_file,
    is_artist, increment_song_likes, decrement_song_likes, increment_song_play_count,
    get_or_create_liked_songs_playlist, sync_favorites_to_playlist
)
from rest_framework.authentication import TokenAuthentication
from music.permissions import IsArtistOrReadOnly
from music.music_enum import Visibility
from users.role_enum import RoleEnum

class SongViewSet(viewsets.ModelViewSet):
    """Viewset for managing song uploads"""

    queryset = Song.objects.all()
    serializer_class = SongSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsArtistOrReadOnly]
    authentication_classes = [TokenAuthentication]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'genres__title', 'album__title', 'user__username']
    ordering_fields = ['play_count', 'likes', 'release_date', 'created_at', 'bpm', 'energy']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        queryset = Song.objects.all()
        
        # Filter by visibility
        public_filter = Q(visibility=Visibility.PUBLIC.value)
        if user.is_authenticated and is_artist(user):
            queryset = queryset.filter(public_filter | Q(user=user))
        else:
            queryset = queryset.filter(public_filter)
        
        # Filter by genre
        genre = self.request.query_params.get('genre', None)
        if genre:
            queryset = queryset.filter(genres__title__icontains=genre).distinct()
        
        # Filter by artist
        artist = self.request.query_params.get('artist', None)
        if artist:
            if artist == 'me' and user.is_authenticated:
                # Special case: 'me' means current user's songs
                queryset = queryset.filter(user=user)
            else:
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
        
        return queryset.select_related('user', 'album').prefetch_related('genres')

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get("audio_file")
        if not file_obj:
            return Response({"error": "No audio file provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate audio file
        validation_error = validate_audio_file(file_obj)
        if validation_error:
            return Response({"error": validation_error}, status=status.HTTP_400_BAD_REQUEST)

        # Save file locally - the file will be handled by Django's FileField
        # We'll pass the file directly to the serializer

        # Handle genres - FormData sends multiple values, use getlist to get all
        # QueryDict.getlist() returns a list of all values for the key
        if hasattr(request.data, 'getlist'):
            genres_data = request.data.getlist("genres")
        else:
            genres_data = request.data.get("genres", [])
            if not isinstance(genres_data, list):
                genres_data = [genres_data] if genres_data else []
        
        # Filter out empty strings and ensure we have valid genres
        genres_data = [g for g in genres_data if g and isinstance(g, str) and g.strip()]
        
        if not genres_data or len(genres_data) == 0:
            return Response({"error": "At least one genre is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a mutable copy of request.data and update genres
        # DRF's MultiPartParser automatically merges request.FILES with request.data
        # We need to work with the data properly to include files
        from django.http import QueryDict
        
        # Create a mutable QueryDict - don't copy request.data directly as it may contain file objects
        # Instead, manually copy only the non-file data
        data = QueryDict(mutable=True)
        for key, value in request.data.items():
            # Skip file fields - they're in request.FILES, not request.data
            if key == 'audio_file':
                continue
            # Copy all other fields
            if hasattr(request.data, 'getlist'):
                for v in request.data.getlist(key):
                    data.appendlist(key, v)
            else:
                data[key] = value
        
        # Update genres to be a proper list
        # Remove old genres entries and add new ones
        if 'genres' in data:
            data.pop('genres')
        for genre in genres_data:
            data.appendlist('genres', genre)
        
        # The audio file is in request.FILES, and DRF's MultiPartParser will automatically
        # merge request.FILES with the data when we pass both to the serializer
        serializer = self.get_serializer(data=data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # The file should be in validated_data now, but let's verify
        song_instance = serializer.save(user=request.user)
        
        # Verify the file was saved
        if not song_instance.audio_file:
            return Response(
                {"error": "Failed to save audio file. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Trigger background tasks for audio analysis and metadata enrichment
        from music.tasks import analyze_audio_features, enrich_song_metadata
        analyze_audio_features.delay(str(song_instance.id))
        enrich_song_metadata.delay(str(song_instance.id))

        return Response(SongSerializer(song_instance).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        if is_artist(request.user):
            return Response(
                {"error": "Artists cannot like songs. Only regular users can like songs."},
                status=status.HTTP_403_FORBIDDEN
            )
        song = self.get_object()
        like, created = SongLike.objects.get_or_create(user=request.user, song=song)
        if created:
            increment_song_likes(song)
        return Response({"likes": song.likes})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        if is_artist(request.user):
            return Response(
                {"error": "Artists cannot unlike songs. Only regular users can unlike songs."},
                status=status.HTTP_403_FORBIDDEN
            )
        song = self.get_object()
        deleted, _ = SongLike.objects.filter(user=request.user, song=song).delete()
        if deleted:
            decrement_song_likes(song)
        return Response({"likes": song.likes})

    @action(detail=True, methods=['post', 'patch'], permission_classes=[IsAuthenticated])
    def upload_audio(self, request, pk=None):
        """Upload or update audio file for an existing song"""
        song = self.get_object()
        
        # Check if user owns the song or is admin
        if song.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "You don't have permission to update this song."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        file_obj = request.FILES.get("audio_file")
        if not file_obj:
            return Response(
                {"error": "No audio file provided."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate audio file
        validation_error = validate_audio_file(file_obj)
        if validation_error:
            return Response(
                {"error": validation_error},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update the song's audio file
        song.audio_file = file_obj
        song.save(update_fields=['audio_file'])
        
        # Trigger audio analysis if audio file was added
        if song.audio_file:
            from music.tasks import analyze_audio_features
            analyze_audio_features.delay(str(song.id))
        
        return Response(
            {
                "message": "Audio file uploaded successfully",
                "song": SongSerializer(song, context={'request': request}).data
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def play(self, request, pk=None):
        """Play a song and track analytics"""
        song = self.get_object()
        increment_song_play_count(song)
        
        if request.user.is_authenticated:
            RecentlyPlayed.objects.update_or_create(
                user=request.user,
                song=song,
                defaults={'played_at': timezone.now()}
            )
            
            # Track analytics for artist
            if song.user and is_artist(song.user):
                # Get user's location if available (from request headers or IP)
                location_city = request.META.get('HTTP_X_CITY') or None
                
                # Use update_or_create with F() expression for atomic increment
                analytics, created = SongAnalytics.objects.get_or_create(
                    artist=song.user,
                    song=song,
                    date=timezone.now().date(),
                    location_city=location_city,
                    defaults={'daily_plays': 1}
                )
                
                if not created:
                    # Increment existing record atomically
                    SongAnalytics.objects.filter(id=analytics.id).update(
                        daily_plays=F('daily_plays') + 1
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
                Q(genres__title__icontains=query) |
                Q(album__title__icontains=query) |
                Q(user__username__icontains=query)
            ).distinct()[:20]
            results['songs'] = SongSerializer(songs, many=True, context={'request': request}).data
        
        if search_type in ['all', 'album']:
            # Apply visibility filter for albums (similar to songs)
            album_queryset = Album.objects.all()
            public_filter = Q()  # Albums don't have visibility field, show all public albums
            albums = album_queryset.filter(
                (Q(title__icontains=query) |
                Q(user__username__icontains=query))
            ).distinct()[:20]
            results['albums'] = AlbumSerializer(albums, many=True, context={'request': request}).data
        
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
        """Add or remove song from favorites and sync with Liked Songs playlist"""
        song = self.get_object()
        
        if request.method == 'POST':
            favorite, created = FavoriteSong.objects.get_or_create(
                user=request.user,
                song=song
            )
            
            # Sync with Liked Songs playlist
            liked_songs_playlist = get_or_create_liked_songs_playlist(request.user)
            playlist_song, ps_created = PlaylistSong.objects.get_or_create(
                playlist=liked_songs_playlist,
                song=song,
                defaults={'order': PlaylistSong.objects.filter(playlist=liked_songs_playlist).count()}
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
                # Remove song from all "Liked Songs" playlists for this user
                liked_songs_playlists = Playlist.objects.filter(
                    user=request.user,
                    name="Liked Songs"
                )
                for playlist in liked_songs_playlists:
                    PlaylistSong.objects.filter(
                        playlist=playlist,
                        song=song
                    ).delete()
                
                return Response({"message": "Song removed from favorites"})
            return Response({"error": "Song not in favorites"}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def favorites(self, request):
        """Get user's favorite songs and ensure Liked Songs playlist exists"""
        favorites = FavoriteSong.objects.filter(user=request.user).select_related('song')
        songs = [fav.song for fav in favorites]
        
        # Sync favorites to playlist
        sync_favorites_to_playlist(request.user)
        
        serializer = self.get_serializer(songs, many=True, context={'request': request})
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
        ).values_list('song__genres__id', flat=True).distinct()

        # Get songs from favorite genres
        if favorite_genres:
            recommended = self.get_queryset().filter(
                genres__id__in=favorite_genres
            ).distinct().exclude(
                id__in=FavoriteSong.objects.filter(user=request.user).values_list('song__id', flat=True)
            ).order_by('-play_count', '-likes')[:limit]
        else:
            # Fallback to trending
            recommended = self.get_queryset().order_by('-play_count', '-likes')[:limit]
        
        serializer = self.get_serializer(recommended, many=True)
        return Response(serializer.data)

    # New endpoints for audio features
    @action(detail=False, methods=['get'])
    def by_mood(self, request):
        """Get songs filtered by mood tag"""
        mood = request.query_params.get('mood', None)
        if not mood:
            return Response(
                {"error": "Mood parameter is required (e.g., 'happy', 'sad', 'energetic', 'calm')"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(mood_tag__iexact=mood)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_energy(self, request):
        """Get songs filtered by energy level"""
        try:
            min_energy = float(request.query_params.get('min', 0.0))
            max_energy = float(request.query_params.get('max', 1.0))
        except ValueError:
            return Response(
                {"error": "min and max must be valid numbers between 0.0 and 1.0"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            energy__gte=min_energy,
            energy__lte=max_energy
        ).order_by('-energy')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_bpm(self, request):
        """Get songs filtered by BPM range"""
        try:
            min_bpm = float(request.query_params.get('min', 0.0))
            max_bpm = float(request.query_params.get('max', 200.0))
        except ValueError:
            return Response(
                {"error": "min and max must be valid numbers"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(
            bpm__gte=min_bpm,
            bpm__lte=max_bpm
        ).order_by('bpm')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def lyrics(self, request, pk=None):
        """Get lyrics for a song"""
        song = self.get_object()
        if not song.lyrics_json:
            return Response(
                {"error": "Lyrics not available for this song"},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response({"lyrics": song.lyrics_json})

    # New endpoints for related names
    @action(detail=True, methods=['get'])
    def recently_played_by(self, request, pk=None):
        """Get users who recently played this song"""
        song = self.get_object()
        recent_plays = song.recent_plays.select_related('user').order_by('-played_at')[:20]
        
        return Response({
            'song': song.title,
            'recent_players': [
                {
                    'username': play.user.username,
                    'played_at': play.played_at
                }
                for play in recent_plays
            ]
        })

    @action(detail=True, methods=['get'])
    def favorited_by(self, request, pk=None):
        """Get users who favorited this song"""
        song = self.get_object()
        favorites = song.favorited_by.select_related('user').order_by('-added_at')[:20]
        
        return Response({
            'song': song.title,
            'favorited_by': [
                {
                    'username': fav.user.username,
                    'added_at': fav.added_at
                }
                for fav in favorites
            ],
            'total_favorites': song.favorited_by.count()
        })

    @action(detail=True, methods=['get'])
    def in_playlists(self, request, pk=None):
        """Get playlists containing this song"""
        song = self.get_object()
        playlists = song.in_playlists.select_related('playlist', 'playlist__user').order_by('-added_at')
        
        return Response({
            'song': song.title,
            'playlists': [
                {
                    'playlist_id': str(ps.playlist.id),
                    'playlist_name': ps.playlist.name,
                    'playlist_owner': ps.playlist.user.username,
                    'added_at': ps.added_at
                }
                for ps in playlists
            ],
            'total_playlists': playlists.count()
        })

    @action(detail=True, methods=['get'])
    def playing_in_rooms(self, request, pk=None):
        """Get listening rooms where this song is currently playing"""
        song = self.get_object()
        rooms = song.playing_in_rooms.filter(is_active=True, is_playing=True)
        
        return Response({
            'song': song.title,
            'active_rooms': [
                {
                    'room_id': str(room.id),
                    'room_name': room.name,
                    'host': room.host.username,
                    'listeners': room.listeners.count()
                }
                for room in rooms
            ]
        })


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
        user = self.request.user
        queryset = Album.objects.all()
        
        # If user is authenticated, filter albums by user (artists only see their own albums)
        if user.is_authenticated:
            # Check if user is an artist
            if is_artist(user):
                # Artists can only see their own albums
                queryset = queryset.filter(user=user)
            # Regular users can see all albums (for browsing)
            # But if they want to see a specific artist's albums, they can use the artist filter
        
        # Filter by artist (for public browsing or specific artist lookup)
        artist = self.request.query_params.get('artist', None)
        if artist:
            if artist == 'me' and user.is_authenticated:
                # Special case: 'me' means current user's albums
                queryset = queryset.filter(user=user)
            else:
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
    
    def get_object(self):
        """Override to check permissions for individual album access"""
        obj = super().get_object()
        user = self.request.user
        
        # If user is an artist, they can only access their own albums
        if user.is_authenticated:
            if is_artist(user) and obj.user != user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("You don't have permission to access this album.")
        
        return obj

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
        
        # Check if user has permission to view this album's songs
        user = request.user
        if user.is_authenticated:
            # If user is an artist and doesn't own this album, deny access
            if is_artist(user) and album.user != user:
                return Response(
                    {"error": "You don't have permission to view this album's songs."},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        songs = album.songs.all()
        serializer = SongSerializer(songs, many=True)
        return Response(serializer.data)


class PlaylistViewSet(viewsets.ModelViewSet):
    """Viewset for managing playlists"""
    queryset = Playlist.objects.all()
    serializer_class = PlaylistSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-updated_at']

    def get_queryset(self):
        user = self.request.user
        # Users can see their own playlists and public playlists
        return Playlist.objects.filter(
            Q(user=user) | Q(is_public=True)
        ).select_related('user').prefetch_related('playlist_songs__song')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def songs(self, request, pk=None):
        """Add or remove songs from playlist"""
        playlist = self.get_object()
        
        # Check permission
        if playlist.user != request.user:
            return Response({"error": "You don't have permission to modify this playlist"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'POST':
            song_id = request.data.get('song_id')
            if not song_id:
                return Response({"error": "song_id is required"}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            try:
                song = Song.objects.get(id=song_id)
            except Song.DoesNotExist:
                return Response({"error": "Song not found"}, 
                              status=status.HTTP_404_NOT_FOUND)
            
            # Get max order for this playlist
            max_order = PlaylistSong.objects.filter(playlist=playlist).aggregate(
                max_order=MaxFunc('order')
            )['max_order'] or 0
            
            playlist_song, created = PlaylistSong.objects.get_or_create(
                playlist=playlist,
                song=song,
                defaults={'order': max_order + 1}
            )
            
            if created:
                return Response(PlaylistSongSerializer(playlist_song).data, 
                              status=status.HTTP_201_CREATED)
            return Response({"message": "Song already in playlist"})
        
        elif request.method == 'DELETE':
            song_id = request.data.get('song_id')
            if not song_id:
                return Response({"error": "song_id is required"}, 
                              status=status.HTTP_400_BAD_REQUEST)
            
            deleted = PlaylistSong.objects.filter(
                playlist=playlist,
                song_id=song_id
            ).delete()
            
            if deleted[0]:
                return Response({"message": "Song removed from playlist"})
            return Response({"error": "Song not in playlist"}, 
                          status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reorder(self, request, pk=None):
        """Reorder songs in playlist"""
        playlist = self.get_object()
        
        if playlist.user != request.user:
            return Response({"error": "You don't have permission to modify this playlist"}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        song_orders = request.data.get('song_orders', [])  # List of {song_id: order}
        if not song_orders:
            return Response({"error": "song_orders is required"}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        for item in song_orders:
            PlaylistSong.objects.filter(
                playlist=playlist,
                song_id=item['song_id']
            ).update(order=item['order'])
        
        return Response({"message": "Playlist reordered"})


class SongAnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for song analytics (read-only for artists)"""
    serializer_class = SongAnalyticsSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]
    
    def get_queryset(self):
        user = self.request.user
        # Artists can only see their own analytics
        if is_artist(user):
            return SongAnalytics.objects.filter(artist=user).select_related('song')
        return SongAnalytics.objects.none()
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get analytics summary for artist"""
        user = request.user
        if not is_artist(user):
            return Response(
                {"error": "Only artists can view analytics"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Last 30 days
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        analytics = SongAnalytics.objects.filter(
            artist=user,
            date__gte=thirty_days_ago
        )
        
        total_plays = analytics.aggregate(Sum('daily_plays'))['daily_plays__sum'] or 0
        avg_daily_plays = analytics.aggregate(Avg('daily_plays'))['daily_plays__avg'] or 0
        
        # Top songs
        top_songs = analytics.values('song__title', 'song__id').annotate(
            total_plays=Sum('daily_plays')
        ).order_by('-total_plays')[:10]
        
        # Plays by location
        plays_by_location = analytics.values('location_city').annotate(
            total_plays=Sum('daily_plays')
        ).order_by('-total_plays')[:10]
        
        return Response({
            'total_plays_30_days': total_plays,
            'average_daily_plays': round(avg_daily_plays, 2),
            'top_songs': list(top_songs),
            'plays_by_location': list(plays_by_location)
        })
    
    @action(detail=False, methods=['get'])
    def by_song(self, request):
        """Get analytics for a specific song"""
        song_id = request.query_params.get('song_id')
        if not song_id:
            return Response(
                {"error": "song_id parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        if not is_artist(user):
            return Response(
                {"error": "Only artists can view analytics"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        analytics = SongAnalytics.objects.filter(
            song_id=song_id,
            artist=user
        ).order_by('-date')
        
        serializer = self.get_serializer(analytics, many=True)
        return Response(serializer.data)