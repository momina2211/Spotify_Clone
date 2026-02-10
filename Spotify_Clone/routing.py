"""
WebSocket URL routing for Django Channels
"""
from django.urls import re_path
from music import consumers

websocket_urlpatterns = [
    re_path(r'ws/rooms/(?P<room_id>[0-9a-f-]+)/$', consumers.ListeningRoomConsumer.as_asgi()),
]
