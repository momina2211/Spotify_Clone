from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from music.models import Song
from music.serializers import SongSerializer
from music.utils import upload_to_s3, get_or_create_genre
from rest_framework.authentication import TokenAuthentication

class SongViewSet(viewsets.ModelViewSet):
    """Viewset for managing song uploads"""

    queryset = Song.objects.all()
    serializer_class = SongSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

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