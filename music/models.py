from django.db import models
from users.models import UUIDModel, User
from music.music_enum import Visibility

class Album(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    title = models.CharField(max_length=100)
    release_date = models.DateField()
    cover_image = models.ImageField(upload_to='album_covers/', blank=True, null=True)

    def __str__(self):
        return self.title

class Genre(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE,null=True,blank=True)
    title = models.CharField(max_length=100)
    def __str__(self):
        return self.title

class Song(UUIDModel):
    TITLE_MAX_LENGTH = 100

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='songs',null=True,blank=True)
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='songs',null=True,blank=True)
    title = models.CharField(max_length=TITLE_MAX_LENGTH)
    duration = models.PositiveIntegerField(help_text="Duration in seconds")
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE, related_name='songs',null=True,blank=True)
    release_date = models.DateField()
    audio_file = models.URLField()
    play_count = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    visibility = models.IntegerField(choices=Visibility.choices(), default=Visibility.PUBLIC.value)
    licensing_info = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class SongLike(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='song_likes')
    song = models.ForeignKey('Song', on_delete=models.CASCADE, related_name='likes_rel')

    class Meta:
        unique_together = ('user', 'song')

    def __str__(self):
        return f"{self.user.username} likes {self.song.title}"