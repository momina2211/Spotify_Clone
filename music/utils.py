import boto3
import os
import logging
from botocore.exceptions import ClientError

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
