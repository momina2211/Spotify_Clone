"""
WebSocket consumers for live listening rooms
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from music.models import ListeningRoom, RoomListener, Song

User = get_user_model()


class ListeningRoomConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time synchronized playback in listening rooms"""
    
    async def connect(self):
        """Handle WebSocket connection"""
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'room_{self.room_id}'
        self.user = self.scope['user']
        
        # Check if room exists and user is authenticated
        room = await self.get_room(self.room_id)
        if not room:
            await self.close()
            return
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Check room capacity
        listener_count = await self.get_listener_count(self.room_id)
        if listener_count >= room.max_listeners:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Add user to room listeners
        await self.add_listener(self.room_id, self.user.id)
        
        # Send current room state to new user
        room_state = await self.get_room_state(self.room_id)
        await self.send(text_data=json.dumps({
            'type': 'room_state',
            'data': room_state
        }))
        
        # Notify others that user joined
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user': self.user.username,
                'user_id': str(self.user.id)
            }
        )
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Remove user from room listeners
        await self.remove_listener(self.room_id, self.user.id)
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        
        # Notify others that user left
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_left',
                'user': self.user.username,
                'user_id': str(self.user.id)
            }
        )
    
    async def receive(self, text_data):
        """Handle messages from WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'play':
                await self.handle_play(data)
            elif message_type == 'pause':
                await self.handle_pause(data)
            elif message_type == 'seek':
                await self.handle_seek(data)
            elif message_type == 'change_song':
                await self.handle_change_song(data)
            elif message_type == 'sync_request':
                await self.handle_sync_request()
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def handle_play(self, data):
        """Handle play action from host"""
        room = await self.get_room(self.room_id)
        if room.host.id != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Only the host can control playback'
            }))
            return
        
        position = data.get('position', room.current_position)
        
        # Update room state
        await self.update_room_state(
            self.room_id,
            is_playing=True,
            current_position=position
        )
        
        # Broadcast to all listeners
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'playback_event',
                'event': 'play',
                'position': position,
                'timestamp': data.get('timestamp')
            }
        )
    
    async def handle_pause(self, data):
        """Handle pause action from host"""
        room = await self.get_room(self.room_id)
        if room.host.id != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Only the host can control playback'
            }))
            return
        
        position = data.get('position', room.current_position)
        
        # Update room state
        await self.update_room_state(
            self.room_id,
            is_playing=False,
            current_position=position
        )
        
        # Broadcast to all listeners
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'playback_event',
                'event': 'pause',
                'position': position,
                'timestamp': data.get('timestamp')
            }
        )
    
    async def handle_seek(self, data):
        """Handle seek action from host"""
        room = await self.get_room(self.room_id)
        if room.host.id != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Only the host can control playback'
            }))
            return
        
        position = data.get('position', 0)
        
        # Update room state
        await self.update_room_state(
            self.room_id,
            current_position=position
        )
        
        # Broadcast to all listeners
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'playback_event',
                'event': 'seek',
                'position': position,
                'timestamp': data.get('timestamp')
            }
        )
    
    async def handle_change_song(self, data):
        """Handle song change from host"""
        room = await self.get_room(self.room_id)
        if room.host.id != self.user.id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Only the host can change songs'
            }))
            return
        
        song_id = data.get('song_id')
        song = await self.get_song(song_id)
        
        if not song:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Song not found'
            }))
            return
        
        # Update room state
        await self.update_room_state(
            self.room_id,
            current_song_id=song_id,
            current_position=0.0,
            is_playing=False
        )
        
        # Broadcast to all listeners
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'song_changed',
                'song_id': str(song_id),
                'song_title': song.title,
                'song_duration': song.duration
            }
        )
    
    async def handle_sync_request(self):
        """Handle sync request from listener"""
        room_state = await self.get_room_state(self.room_id)
        await self.send(text_data=json.dumps({
            'type': 'room_state',
            'data': room_state
        }))
    
    # Event handlers for group messages
    async def playback_event(self, event):
        """Send playback event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'playback_event',
            'event': event['event'],
            'position': event['position'],
            'timestamp': event.get('timestamp')
        }))
    
    async def song_changed(self, event):
        """Send song change event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'song_changed',
            'song_id': event['song_id'],
            'song_title': event['song_title'],
            'song_duration': event['song_duration']
        }))
    
    async def user_joined(self, event):
        """Send user joined event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_joined',
            'user': event['user'],
            'user_id': event['user_id']
        }))
    
    async def user_left(self, event):
        """Send user left event to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'user': event['user'],
            'user_id': event['user_id']
        }))
    
    # Database operations
    @database_sync_to_async
    def get_room(self, room_id):
        """Get room from database"""
        try:
            return ListeningRoom.objects.get(id=room_id, is_active=True)
        except ListeningRoom.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_song(self, song_id):
        """Get song from database"""
        try:
            return Song.objects.get(id=song_id)
        except Song.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_listener_count(self, room_id):
        """Get number of listeners in room"""
        return RoomListener.objects.filter(room_id=room_id).count()
    
    @database_sync_to_async
    def add_listener(self, room_id, user_id):
        """Add user to room listeners"""
        room = ListeningRoom.objects.get(id=room_id)
        user = User.objects.get(id=user_id)
        RoomListener.objects.get_or_create(room=room, user=user)
    
    @database_sync_to_async
    def remove_listener(self, room_id, user_id):
        """Remove user from room listeners"""
        RoomListener.objects.filter(room_id=room_id, user_id=user_id).delete()
    
    @database_sync_to_async
    def get_room_state(self, room_id):
        """Get current room state"""
        room = ListeningRoom.objects.get(id=room_id)
        listeners = RoomListener.objects.filter(room=room).select_related('user')
        
        return {
            'room_id': str(room.id),
            'room_name': room.name,
            'host': room.host.username,
            'host_id': str(room.host.id),
            'current_song': {
                'id': str(room.current_song.id) if room.current_song else None,
                'title': room.current_song.title if room.current_song else None,
                'duration': room.current_song.duration if room.current_song else None,
            } if room.current_song else None,
            'current_position': room.current_position,
            'is_playing': room.is_playing,
            'listeners': [
                {
                    'id': str(l.user.id),
                    'username': l.user.username
                }
                for l in listeners
            ],
            'listener_count': listeners.count()
        }
    
    @database_sync_to_async
    def update_room_state(self, room_id, **kwargs):
        """Update room state in database"""
        ListeningRoom.objects.filter(id=room_id).update(**kwargs)
