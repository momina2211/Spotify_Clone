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
    genres = models.ManyToManyField(Genre, related_name='songs', blank=True)
    release_date = models.DateField()
    audio_file = models.FileField(upload_to='songs/', blank=True, null=True)
    play_count = models.PositiveIntegerField(default=0)
    likes = models.PositiveIntegerField(default=0)
    visibility = models.IntegerField(choices=Visibility.choices(), default=Visibility.PUBLIC.value)
    licensing_info = models.TextField(blank=True, null=True)
    
    # Audio analysis fields (computed by Librosa)
    valence = models.FloatField(
        null=True, 
        blank=True,
        help_text="Musical positiveness (0.0 = sad, 1.0 = happy)"
    )
    energy = models.FloatField(
        null=True,
        blank=True,
        help_text="Perceptual measure of intensity and power (0.0 = calm, 1.0 = energetic)"
    )
    acousticness = models.FloatField(
        null=True,
        blank=True,
        help_text="Confidence measure of whether the track is acoustic (0.0 = not acoustic, 1.0 = acoustic)"
    )
    bpm = models.FloatField(
        null=True,
        blank=True,
        help_text="Beats per minute (tempo)"
    )
    mood_tag = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Mood classification (e.g., 'happy', 'sad', 'energetic', 'calm')"
    )
    lyrics_json = models.JSONField(
        blank=True,
        null=True,
        help_text="Timestamped lyrics in LRC-style format: [{'time': 10.5, 'text': 'lyrics...'}]"
    )

    def __str__(self):
        return self.title


class SongLike(UUIDModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='song_likes')
    song = models.ForeignKey('Song', on_delete=models.CASCADE, related_name='likes_rel')

    class Meta:
        unique_together = ('user', 'song')

    def __str__(self):
        return f"{self.user.username} likes {self.song.title}"


class RecentlyPlayed(UUIDModel):
    """Track recently played songs for users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recently_played')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='recent_plays')
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_at']
        unique_together = ('user', 'song')
        indexes = [
            models.Index(fields=['user', '-played_at']),
        ]

    def __str__(self):
        return f"{self.user.username} played {self.song.title}"


class FavoriteSong(UUIDModel):
    """User's favorite/saved songs"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'song')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} favorited {self.song.title}"


class FavoriteAlbum(UUIDModel):
    """User's favorite/saved albums"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_albums')
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='favorited_by')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'album')
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.user.username} favorited {self.album.title}"


class ArtistFollow(UUIDModel):
    """Follow relationship between users and artists"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    artist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    followed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'artist')
        ordering = ['-followed_at']
        constraints = [
            models.CheckConstraint(
                check=~models.Q(user=models.F('artist')),
                name='cannot_follow_self'
            )
        ]

    def __str__(self):
        return f"{self.user.username} follows {self.artist.username}"


class Playlist(UUIDModel):
    """User-created playlists"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    cover_image = models.ImageField(upload_to='playlist_covers/', blank=True, null=True)
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username}'s {self.name}"


class PlaylistSong(UUIDModel):
    """Songs in a playlist with order"""
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE, related_name='playlist_songs')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='in_playlists')
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'added_at']
        unique_together = ('playlist', 'song')

    def __str__(self):
        return f"{self.playlist.name} - {self.song.title}"


class ListeningRoom(UUIDModel):
    """Real-time synchronized playback room for multiple users"""
    host = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='hosted_rooms',
        help_text="User who created and controls the room"
    )
    name = models.CharField(
        max_length=100,
        help_text="Room name/description"
    )
    current_song = models.ForeignKey(
        Song,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='playing_in_rooms',
        help_text="Currently playing song"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the room is currently active"
    )
    current_position = models.FloatField(
        default=0.0,
        help_text="Current playback position in seconds"
    )
    is_playing = models.BooleanField(
        default=False,
        help_text="Whether playback is currently active"
    )
    max_listeners = models.PositiveIntegerField(
        default=50,
        help_text="Maximum number of listeners allowed"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['host', '-created_at']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name} (Host: {self.host.username})"


class RoomListener(UUIDModel):
    """Track users currently in a listening room"""
    room = models.ForeignKey(
        ListeningRoom,
        on_delete=models.CASCADE,
        related_name='listeners'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='room_participations'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.room.name}"


class SongAnalytics(UUIDModel):
    """Analytics data for songs and artists"""
    artist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='song_analytics',
        help_text="Artist who owns the song"
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name='analytics',
        help_text="Song being analyzed"
    )
    date = models.DateField(
        help_text="Date of the analytics record"
    )
    daily_plays = models.PositiveIntegerField(
        default=0,
        help_text="Number of plays on this date"
    )
    location_city = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="City where plays occurred (if available)"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('song', 'date', 'location_city')
        ordering = ['-date', '-daily_plays']
        indexes = [
            models.Index(fields=['artist', '-date']),
            models.Index(fields=['song', '-date']),
            models.Index(fields=['date', '-daily_plays']),
        ]

    def __str__(self):
        return f"{self.song.title} - {self.date} ({self.daily_plays} plays)"