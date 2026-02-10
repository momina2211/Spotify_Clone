from django.urls import path, include  # Import include
from rest_framework.routers import DefaultRouter
from music.viewsets import SongViewSet, GenreViewSet, AlbumViewSet, PlaylistViewSet, SongAnalyticsViewSet
from music.ai_views import AIPlaylistViewSet
from music.room_views import ListeningRoomViewSet

# Create a router and register our viewset with it.
router = DefaultRouter()
router.register('songs', SongViewSet)
router.register('genres', GenreViewSet)
router.register('albums', AlbumViewSet)
router.register('playlists', PlaylistViewSet)
router.register('analytics', SongAnalyticsViewSet, basename='analytics')
router.register('ai', AIPlaylistViewSet, basename='ai')
router.register('rooms', ListeningRoomViewSet, basename='rooms')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),  # Corrected syntax
]