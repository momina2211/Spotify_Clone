from rest_framework import serializers
from music.models import Song, Genre, Album
from music.utils import get_or_create_genre, get_or_create_album


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
    genre = serializers.CharField(required=True)  # Accept genre as a string
    album_title = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Song
        fields = ['id','user', 'title', 'album', 'album_title', 'genre', 'release_date', 'duration', 'audio_file', 'visibility']
        read_only_fields = ['id', 'user', 'audio_file']

    def create(self, validated_data):
        """Set the song owner automatically and handle genre creation"""
        request = self.context.get('request')
        validated_data['user'] = request.user  # Set the user to the currently authenticated user

        # Handle genre creation or retrieval
        genre_title = validated_data.pop('genre')  # Get the genre title
        genre, created = get_or_create_genre(genre_title, request.user)  # Pass the user to the function
        validated_data['genre'] = genre  # Set the genre object

        # Optional: handle album creation by title
        album_title = validated_data.pop('album_title', None)
        if album_title:
            album, _ = get_or_create_album(album_title, request.user)
            validated_data['album'] = album

        # Create the song instance
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Handle updates to the song instance"""
        request = self.context.get('request')
        validated_data['user'] = request.user  # Set the user to the currently authenticated user
        genre_title = validated_data.pop('genre', None)  # Get the genre title if provided
        if genre_title:
            genre, created = get_or_create_genre(genre_title, request.user)  # Create or get the genre
            validated_data['genre'] = genre  # Set the genre object (Genre instance)
        album_title = validated_data.pop('album_title', None)
        if album_title:
            album, _ = get_or_create_album(album_title, request.user)
            validated_data['album'] = album
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Customize the output representation"""
        representation = super().to_representation(instance)
        representation['genre'] = GenreSerializer(instance.genre).data
        if instance.album:
            representation['album'] = AlbumSerializer(instance.album).data
        representation['audio_file'] = instance.audio_file
        return representation