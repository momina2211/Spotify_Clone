from rest_framework import serializers
from music.models import Song, Genre, Album, Playlist, PlaylistSong, ListeningRoom, SongAnalytics
from music.utils import get_or_create_genre, get_or_create_album
import logging

logger = logging.getLogger(__name__)


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for handling Genre model data"""
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Genre
        fields = ['id', 'title', 'user']  # Include the user field if needed


class AlbumSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Album
        fields = ['id', 'title', 'release_date', 'cover_image', 'user']


class SongSerializer(serializers.ModelSerializer):
    """Serializer for handling Song model data"""
    user = serializers.CharField(source='user.username', read_only=True)
    genres = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        write_only=True,
        help_text="List of genre titles"
    )
    genres_data = GenreSerializer(source='genres', many=True, read_only=True)
    album_title = serializers.CharField(required=False, allow_blank=True, write_only=True)
    album_id = serializers.UUIDField(required=False, allow_null=True, write_only=True, help_text="ID of existing album")
    
    # Audio analysis fields (read-only, computed by tasks)
    valence = serializers.FloatField(read_only=True, help_text="Musical positiveness (0.0 = sad, 1.0 = happy)")
    energy = serializers.FloatField(read_only=True, help_text="Perceptual measure of intensity and power (0.0 = calm, 1.0 = energetic)")
    acousticness = serializers.FloatField(read_only=True, help_text="Confidence measure of whether the track is acoustic (0.0 = not acoustic, 1.0 = acoustic)")
    bpm = serializers.FloatField(read_only=True, help_text="Beats per minute (tempo)")
    mood_tag = serializers.CharField(read_only=True, help_text="Mood classification (e.g., 'happy', 'sad', 'energetic', 'calm')")
    lyrics_json = serializers.JSONField(read_only=True, help_text="Timestamped lyrics in LRC-style format")
    licensing_info = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text="Licensing information for the song")

    class Meta:
        model = Song
        fields = [
            'id','user', 'title', 'album', 'album_title', 'album_id', 
            'genres', 'genres_data', 'release_date', 'duration', 
            'audio_file', 'visibility', 'licensing_info',
            # Audio analysis fields
            'valence', 'energy', 'acousticness', 'bpm', 'mood_tag',
            # Lyrics
            'lyrics_json',
            # Stats (added in to_representation)
            'likes', 'play_count'
        ]
        read_only_fields = [
            'id', 'user', 'genres_data', 'valence', 'energy', 
            'acousticness', 'bpm', 'mood_tag', 'lyrics_json',
            'likes', 'play_count'
        ]

    def create(self, validated_data):
        """Set the song owner automatically and handle genre creation"""
        request = self.context.get('request')
        validated_data['user'] = request.user  # Set the user to the currently authenticated user

        # Ensure audio_file is in validated_data (it should come from request.FILES)
        # If it's not there, try to get it from request.FILES
        if 'audio_file' not in validated_data and request and hasattr(request, 'FILES'):
            audio_file = request.FILES.get('audio_file')
            if audio_file:
                validated_data['audio_file'] = audio_file

        # Handle multiple genres creation or retrieval
        genre_titles = validated_data.pop('genres', [])  # Get list of genre titles
        
        # Ensure genre_titles is a list
        if not isinstance(genre_titles, list):
            if isinstance(genre_titles, str):
                genre_titles = [genre_titles]
            else:
                genre_titles = list(genre_titles) if genre_titles else []
        
        # Filter out empty strings and ensure all are strings
        genre_titles = [str(g).strip() for g in genre_titles if g and str(g).strip()]
        
        # Optional: handle album - either by ID or by title
        album_id = validated_data.pop('album_id', None)
        album_title = validated_data.pop('album_title', None)
        
        if album_id:
            # Use existing album by ID
            try:
                from music.models import Album
                album = Album.objects.get(id=album_id, user=request.user)
                validated_data['album'] = album
            except Album.DoesNotExist:
                pass  # If album doesn't exist or doesn't belong to user, ignore
        elif album_title:
            # Create or get album by title
            album, _ = get_or_create_album(album_title, request.user)
            validated_data['album'] = album

        # Create the song instance first (without genres)
        song = super().create(validated_data)
        
        # Add genres to the song
        for genre_title in genre_titles:
            if genre_title:  # Skip empty strings
                genre, created = get_or_create_genre(genre_title.strip(), request.user)
                song.genres.add(genre)
        
        return song

    def update(self, instance, validated_data):
        """Handle updates to the song instance"""
        request = self.context.get('request')
        validated_data['user'] = request.user  # Set the user to the currently authenticated user
        
        # Handle multiple genres
        genre_titles = validated_data.pop('genres', None)  # Get list of genre titles if provided
        if genre_titles is not None:
            if isinstance(genre_titles, str):
                # Handle case where single genre is passed as string
                genre_titles = [genre_titles]
            # Clear existing genres and add new ones
            instance.genres.clear()
            for genre_title in genre_titles:
                if genre_title:  # Skip empty strings
                    genre, created = get_or_create_genre(genre_title.strip(), request.user)
                    instance.genres.add(genre)
        
        # Handle album - either by ID or by title
        album_id = validated_data.pop('album_id', None)
        album_title = validated_data.pop('album_title', None)
        
        if album_id:
            # Use existing album by ID
            try:
                from music.models import Album
                album = Album.objects.get(id=album_id, user=request.user)
                validated_data['album'] = album
            except Album.DoesNotExist:
                pass  # If album doesn't exist or doesn't belong to user, ignore
        elif album_title:
            # Create or get album by title
            album, _ = get_or_create_album(album_title, request.user)
            validated_data['album'] = album
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Customize the output representation"""
        representation = super().to_representation(instance)
        # Include genres_data in the representation
        representation['genres'] = GenreSerializer(instance.genres.all(), many=True).data
        if instance.album:
            representation['album'] = AlbumSerializer(instance.album).data
        # Return the full URL for the audio file (FileField)
        if instance.audio_file:
            request = self.context.get('request')
            try:
                # Check if the file actually exists before generating URL
                from django.core.files.storage import default_storage
                if default_storage.exists(instance.audio_file.name):
                    file_url = instance.audio_file.url
                    if request:
                        # Build absolute URI - Django's build_absolute_uri handles URL encoding properly
                        absolute_url = request.build_absolute_uri(file_url)
                        # Ensure the URL is properly formatted (no double slashes, proper encoding)
                        representation['audio_file'] = absolute_url
                    else:
                        # Fallback to relative URL - ensure it starts with /
                        if not file_url.startswith('/'):
                            file_url = '/' + file_url
                        representation['audio_file'] = file_url
                else:
                    logger.warning(f"Audio file for song {instance.id} ({instance.title}) does not exist: {instance.audio_file.name}")
                    representation['audio_file'] = None
            except Exception as e:
                logger.error(f"Error generating audio file URL for song {instance.id}: {e}", exc_info=True)
                representation['audio_file'] = None
        else:
            representation['audio_file'] = None
        representation['likes'] = instance.likes
        representation['play_count'] = instance.play_count
        return representation


class PlaylistSongSerializer(serializers.ModelSerializer):
    """Serializer for songs in a playlist"""
    song = SongSerializer(read_only=True)
    song_id = serializers.UUIDField(write_only=True)

    class Meta:
        model = PlaylistSong
        fields = ['id', 'song', 'song_id', 'order', 'added_at']
        read_only_fields = ['id', 'added_at']


class PlaylistSerializer(serializers.ModelSerializer):
    """Serializer for playlists"""
    user = serializers.CharField(source='user.username', read_only=True)
    songs_count = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    playlist_songs = PlaylistSongSerializer(many=True, read_only=True)

    class Meta:
        model = Playlist
        fields = ['id', 'user', 'name', 'description', 'cover_image', 'is_public', 
                  'created_at', 'updated_at', 'songs_count', 'total_duration', 'playlist_songs']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def get_songs_count(self, obj):
        return obj.playlist_songs.count()

    def get_total_duration(self, obj):
        total = sum(ps.song.duration for ps in obj.playlist_songs.all())
        return total


class ListeningRoomSerializer(serializers.ModelSerializer):
    """Serializer for listening rooms"""
    host = serializers.CharField(source='host.username', read_only=True)
    host_id = serializers.UUIDField(source='host.id', read_only=True)
    current_song = SongSerializer(read_only=True)
    listener_count = serializers.SerializerMethodField()

    class Meta:
        model = ListeningRoom
        fields = [
            'id', 'host', 'host_id', 'name', 'current_song', 'is_active',
            'current_position', 'is_playing', 'max_listeners', 'listener_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'host', 'created_at', 'updated_at']

    def get_listener_count(self, obj):
        return obj.listeners.count()


class SongAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for SongAnalytics"""
    artist = serializers.CharField(source='artist.username', read_only=True)
    song_title = serializers.CharField(source='song.title', read_only=True)
    
    class Meta:
        model = SongAnalytics
        fields = [
            'id', 'artist', 'song', 'song_title', 'date', 
            'daily_plays', 'location_city', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']