"""
Views for listening rooms
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.db import models
from django.db.models import Count, Q
from music.models import ListeningRoom, RoomListener, Song
from music.serializers import ListeningRoomSerializer


class ListeningRoomViewSet(viewsets.ModelViewSet):
    """ViewSet for managing listening rooms"""
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    queryset = ListeningRoom.objects.filter(is_active=True)
    
    serializer_class = ListeningRoomSerializer
    
    def get_queryset(self):
        """Filter rooms by user"""
        user = self.request.user
        # Users can see rooms they host or are part of
        return ListeningRoom.objects.filter(
            is_active=True
        ).filter(
            models.Q(host=user) | models.Q(listeners__user=user)
        ).distinct().annotate(
            listener_count=Count('listeners')
        )
    
    def perform_create(self, serializer):
        """Create room with current user as host"""
        serializer.save(host=self.request.user)
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Join a listening room"""
        room = self.get_object()
        
        # Check capacity
        listener_count = RoomListener.objects.filter(room=room).count()
        if listener_count >= room.max_listeners:
            return Response(
                {'error': 'Room is at full capacity'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Add user to listeners
        RoomListener.objects.get_or_create(room=room, user=request.user)
        
        return Response({
            'message': 'Joined room successfully',
            'room_id': str(room.id)
        })
    
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave a listening room"""
        room = self.get_object()
        RoomListener.objects.filter(room=room, user=request.user).delete()
        
        return Response({'message': 'Left room successfully'})
    
    @action(detail=True, methods=['get'])
    def listeners(self, request, pk=None):
        """Get list of listeners in room"""
        room = self.get_object()
        listeners = RoomListener.objects.filter(room=room).select_related('user')
        
        return Response({
            'listeners': [
                {
                    'id': str(l.user.id),
                    'username': l.user.username,
                    'joined_at': l.joined_at
                }
                for l in listeners
            ],
            'count': listeners.count()
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def set_song(self, request, pk=None):
        """Set current song (host only)"""
        room = self.get_object()
        
        if room.host != request.user:
            return Response(
                {'error': 'Only the host can change the song'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        song_id = request.data.get('song_id')
        try:
            song = Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            return Response(
                {'error': 'Song not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        room.current_song = song
        room.current_position = 0.0
        room.is_playing = False
        room.save()
        
        return Response({
            'message': 'Song changed successfully',
            'song': {
                'id': str(song.id),
                'title': song.title,
                'duration': song.duration
            }
        })
