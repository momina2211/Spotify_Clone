import boto3
import os
import logging
from botocore.exceptions import ClientError
from django.core.exceptions import ValidationError

from music.models import Genre, Album


def upload_to_s3(file_obj, folder="songs/"):
    """Uploads a file to AWS S3 and returns the file URL"""

    bucket_name = os.getenv("AWS_STORAGE_BUCKET_NAME", "spotify-audios")
    object_name = f"{folder}{file_obj.name}"  # Store in 'songs/' folder

    s3_client = boto3.client("s3")

    try:
        file_obj.seek(0)  # Reset file pointer
        s3_client.upload_fileobj(file_obj, bucket_name, object_name)

        file_url = f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
        return file_url
    except ClientError as e:
        logging.error(f"S3 Upload Error: {e}")
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
