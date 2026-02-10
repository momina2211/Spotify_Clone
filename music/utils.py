import os
import logging
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.db.models import F

from music.models import Genre, Album, Song, Playlist, PlaylistSong, FavoriteSong
from users.role_enum import RoleEnum

logger = logging.getLogger(__name__)


def save_file_locally(file_obj, folder="songs/"):
    """Saves a file locally and returns the file URL"""
    try:
        # Reset file pointer
        file_obj.seek(0)
        
        # Generate a unique filename to avoid conflicts
        import uuid
        file_extension = os.path.splitext(file_obj.name)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(folder, unique_filename)
        
        # Save the file using Django's default storage
        saved_path = default_storage.save(file_path, ContentFile(file_obj.read()))
        
        # Return the URL
        if hasattr(settings, 'MEDIA_URL'):
            file_url = f"{settings.MEDIA_URL}{saved_path}"
        else:
            file_url = f"/media/{saved_path}"
        
        return file_url
    except Exception as e:
        logging.error(f"Local File Upload Error: {e}")
        return None


def get_or_create_genre(genre_title, user):
    """Gets an existing genre or creates a new one."""
    if genre_title:
        genre, created = Genre.objects.get_or_create(
            title=genre_title,
            defaults={'user': user}  # Set the user when creating a new genre
        )
        return genre, created  # Return both the genre and the created status
    return None, False

def get_or_create_album(album_title, user):
    """Gets an existing album or creates a new one."""
    if album_title:
        album, created = Album.objects.get_or_create(
            title=album_title,
            defaults={'user': user}
        )
        return album, created
    return None, False


def validate_audio_file(file_obj):
    """
    Validate audio file before upload.
    Returns error message if validation fails, None if valid.
    """
    # Allowed audio file extensions
    ALLOWED_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac']
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    
    # Check file extension
    file_name = file_obj.name.lower()
    if not any(file_name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check file size
    if file_obj.size > MAX_FILE_SIZE:
        return f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)} MB"
    
    if file_obj.size == 0:
        return "File is empty"
    
    return None


def validate_image_file(file_obj):
    """
    Validate image file before upload.
    Returns error message if validation fails, None if valid.
    """
    ALLOWED_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    file_name = file_obj.name.lower()
    if not any(file_name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return f"Invalid image type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
    
    if file_obj.size > MAX_FILE_SIZE:
        return f"Image size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)} MB"
    
    if file_obj.size == 0:
        return "Image file is empty"
    
    return None


def is_artist(user):
    """Check if user is an artist"""
    if not user or not user.is_authenticated:
        return False
    return getattr(user, 'role', None) == RoleEnum.ARTIST.value


def increment_song_likes(song):
    """Increment song likes counter atomically"""
    Song.objects.filter(id=song.id).update(likes=F('likes') + 1)
    song.refresh_from_db(fields=['likes'])


def decrement_song_likes(song):
    """Decrement song likes counter atomically"""
    Song.objects.filter(id=song.id).update(likes=F('likes') - 1)
    song.refresh_from_db(fields=['likes'])


def increment_song_play_count(song):
    """Increment song play count atomically"""
    Song.objects.filter(id=song.id).update(play_count=F('play_count') + 1)
    song.refresh_from_db(fields=['play_count'])


def get_or_create_liked_songs_playlist(user):
    """Get or create 'Liked Songs' playlist and ensure it's unique"""
    liked_songs_playlist = Playlist.objects.filter(
        user=user,
        name="Liked Songs"
    ).first()
    
    if not liked_songs_playlist:
        liked_songs_playlist = Playlist.objects.create(
            user=user,
            name="Liked Songs",
            is_public=False
        )
    else:
        # Handle duplicates
        duplicate_playlists = Playlist.objects.filter(
            user=user,
            name="Liked Songs"
        ).exclude(id=liked_songs_playlist.id)
        
        if duplicate_playlists.exists():
            # Merge songs from duplicates
            for dup_playlist in duplicate_playlists:
                for ps in dup_playlist.playlist_songs.all():
                    PlaylistSong.objects.get_or_create(
                        playlist=liked_songs_playlist,
                        song=ps.song,
                        defaults={'order': PlaylistSong.objects.filter(playlist=liked_songs_playlist).count()}
                    )
            duplicate_playlists.delete()
    
    return liked_songs_playlist


def sync_favorites_to_playlist(user):
    """Sync user's favorites to 'Liked Songs' playlist"""
    liked_songs_playlist = get_or_create_liked_songs_playlist(user)
    
    favorites = FavoriteSong.objects.filter(user=user).select_related('song')
    favorite_song_ids = set([fav.song.id for fav in favorites])
    
    existing_playlist_song_ids = set(
        PlaylistSong.objects.filter(playlist=liked_songs_playlist)
        .values_list('song_id', flat=True)
    )
    
    # Add missing songs
    missing_song_ids = favorite_song_ids - existing_playlist_song_ids
    if missing_song_ids:
        missing_songs = Song.objects.filter(id__in=missing_song_ids)
        current_order = PlaylistSong.objects.filter(playlist=liked_songs_playlist).count()
        for song in missing_songs:
            PlaylistSong.objects.get_or_create(
                playlist=liked_songs_playlist,
                song=song,
                defaults={'order': current_order}
            )
            current_order += 1
    
    # Remove songs no longer favorites
    songs_to_remove = existing_playlist_song_ids - favorite_song_ids
    if songs_to_remove:
        PlaylistSong.objects.filter(
            playlist=liked_songs_playlist,
            song_id__in=songs_to_remove
        ).delete()
    
    return liked_songs_playlist
