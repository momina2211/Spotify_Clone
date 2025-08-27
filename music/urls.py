from django.urls import path, include  # Import include
from rest_framework.routers import DefaultRouter
from music.viewsets import SongViewSet, GenreViewSet, AlbumViewSet

# Create a router and register our viewset with it.
router = DefaultRouter()
router.register('songs', SongViewSet)
router.register('genres', GenreViewSet)
router.register('albums', AlbumViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),  # Corrected syntax
]