# music/serializers.py
from rest_framework import serializers
from music.models import Song, Genre
from music.utils import get_or_create_genre


class GenreSerializer(serializers.ModelSerializer):
    """Serializer for handling Genre model data"""
    user = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Genre
        fields = ['id', 'title', 'user']  # Include the user field if needed


class SongSerializer(serializers.ModelSerializer):
    """Serializer for handling Song model data"""
    user = serializers.CharField(source='user.username', read_only=True)
    genre = serializers.CharField(required=True)  # Accept genre as a string

    class Meta:
        model = Song
        fields = ['id','user', 'title', 'album', 'genre', 'release_date', 'duration', 'audio_file', 'visibility']
        read_only_fields = ['id', 'user', 'audio_file']

    def create(self, validated_data):
        """Set the song owner automatically and handle genre creation"""
        request = self.context.get('request')
        validated_data['user'] = request.user  # Set the user to the currently authenticated user

        # Handle genre creation or retrieval
        genre_title = validated_data.pop('genre')  # Get the genre title
        genre, created = get_or_create_genre(genre_title, request.user)  # Pass the user to the function
        validated_data['genre'] = genre  # Set the genre object

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
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        """Customize the output representation"""
        representation = super().to_representation(instance)
        representation['genre'] = GenreSerializer(instance.genre).data  # Use the GenreSerializer for nested output
        representation['audio_file'] = instance.audio_file
        return representation