from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q, F
from music.models import Song, Genre, Album, SongLike
from music.serializers import SongSerializer, GenreSerializer, AlbumSerializer
from music.utils import upload_to_s3, get_or_create_genre
from rest_framework.authentication import TokenAuthentication
from music.permissions import IsArtistOrReadOnly
from music.music_enum import Visibility

class SongViewSet(viewsets.ModelViewSet):
    """Viewset for managing song uploads"""

    queryset = Song.objects.all()
    serializer_class = SongSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsArtistOrReadOnly]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        user = self.request.user
        public_filter = Q(visibility=Visibility.PUBLIC.value)
        if user.is_authenticated and getattr(user, 'role', None) == 2:
            return Song.objects.filter(public_filter | Q(user=user))
        return Song.objects.filter(public_filter)

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get("audio_file")
        if not file_obj:
            return Response({"error": "No audio file provided."}, status=status.HTTP_400_BAD_REQUEST)

        file_url = upload_to_s3(file_obj)
        if not file_url:
            return Response({"error": "S3 upload failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Prepare the request data
        request.data["audio_file"] = file_url

        # Use the genre as a string
        genre_title = request.data.get("genre")
        if not genre_title:
            return Response({"error": "Genre is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Create or get the genre
        genre, created = get_or_create_genre(genre_title,request.user)
        request.data["genre"] = genre.title  # Set the genre title

        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        song_instance = serializer.save(user=request.user)

        return Response(SongSerializer(song_instance).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        song = self.get_object()
        like, created = SongLike.objects.get_or_create(user=request.user, song=song)
        if created:
            song.likes = F('likes') + 1
            song.save(update_fields=['likes'])
            song.refresh_from_db(fields=['likes'])
        return Response({"likes": song.likes})

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def unlike(self, request, pk=None):
        song = self.get_object()
        deleted, _ = SongLike.objects.filter(user=request.user, song=song).delete()
        if deleted:
            song.likes = F('likes') - 1
            song.save(update_fields=['likes'])
            song.refresh_from_db(fields=['likes'])
        return Response({"likes": song.likes})

    @action(detail=True, methods=['post'])
    def play(self, request, pk=None):
        song = self.get_object()
        song.play_count = F('play_count') + 1
        song.save(update_fields=['play_count'])
        song.refresh_from_db(fields=['play_count'])
        return Response({"play_count": song.play_count})

    @action(detail=False, methods=['get'])
    def trending(self, request):
        limit = int(request.query_params.get('limit', 20))
        queryset = self.get_queryset().order_by('-play_count', '-likes')[:limit]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsArtistOrReadOnly]
    authentication_classes = [TokenAuthentication]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class AlbumViewSet(viewsets.ModelViewSet):
    queryset = Album.objects.all()
    serializer_class = AlbumSerializer
    permission_classes = [IsArtistOrReadOnly]
    authentication_classes = [TokenAuthentication]
    parser_classes = [MultiPartParser, FormParser]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)