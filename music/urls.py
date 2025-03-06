from django.urls import path, include  # Import include
from rest_framework.routers import DefaultRouter
from music.viewsets import SongViewSet  # Import your viewset

# Create a router and register our viewset with it.
router = DefaultRouter()
router.register('songs', SongViewSet)

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),  # Corrected syntax
]