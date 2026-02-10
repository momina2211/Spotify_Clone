"""
AI-powered playlist generation views
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from music.tasks import generate_ai_playlist
from music.models import Playlist
from music.serializers import PlaylistSerializer


class AIPlaylistViewSet(viewsets.ViewSet):
    """ViewSet for AI-powered playlist generation"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate_playlist(self, request):
        """
        Generate a playlist from a natural language prompt.
        
        POST /api/ai/generate-playlist/
        
        Body:
        {
            "prompt": "Songs for a rainy drive in Bahawalpur",
            "playlist_name": "Rainy Drive Playlist" (optional)
        }
        """
        prompt = request.data.get('prompt')
        playlist_name = request.data.get('playlist_name')
        
        if not prompt:
            return Response(
                {'error': 'Prompt is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger Celery task
        task = generate_ai_playlist.delay(
            user_id=str(request.user.id),
            prompt=prompt,
            playlist_name=playlist_name
        )
        
        # For now, wait for result (in production, return task ID and poll)
        # In async implementation, you'd return task.id and poll /api/ai/tasks/{task_id}/
        try:
            result = task.get(timeout=30)  # Wait up to 30 seconds
            
            if 'error' in result:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Fetch the created playlist
            playlist = Playlist.objects.get(id=result['playlist_id'])
            serializer = PlaylistSerializer(playlist)
            
            return Response({
                'playlist': serializer.data,
                'num_songs': result['num_songs'],
                'message': 'Playlist generated successfully'
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate playlist: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
