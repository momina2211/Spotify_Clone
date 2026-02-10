"""
Django management command to create test songs with audio files
Creates silent audio files for testing purposes
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from users.models import UserProfile
from users.role_enum import RoleEnum
from music.models import Song, Album, Genre
from datetime import datetime, timedelta
import io
import wave
import struct
import math

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test songs with audio files for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of songs to create (default: 10)'
        )
        parser.add_argument(
            '--duration',
            type=int,
            default=180,
            help='Duration of each song in seconds (default: 180)'
        )

    def handle(self, *args, **options):
        count = options['count']
        duration = options['duration']
        
        self.stdout.write(self.style.SUCCESS(f'Creating {count} test songs with audio files...'))
        
        # Get or create an artist user
        artist = User.objects.filter(role=RoleEnum.ARTIST.value).first()
        if not artist:
            self.stdout.write('Creating artist user...')
            artist = User.objects.create_user(
                username='test_artist',
                email='test_artist@example.com',
                password='password123',
                role=RoleEnum.ARTIST.value
            )
            UserProfile.objects.get_or_create(
                user=artist,
                defaults={'profile_type': RoleEnum.ARTIST.value}
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Created artist: {artist.username}'))
        
        # Get or create a test album
        album, _ = Album.objects.get_or_create(
            title='Test Album',
            user=artist,
            defaults={
                'release_date': datetime.now().date(),
            }
        )
        
        # Get or create genres
        genres = []
        genre_names = ['Pop', 'Rock', 'Electronic', 'Hip Hop', 'Jazz']
        for genre_name in genre_names:
            genre, _ = Genre.objects.get_or_create(
                title=genre_name,
                defaults={'user': artist}
            )
            genres.append(genre)
        
        # Create songs with audio files
        created_count = 0
        for i in range(1, count + 1):
            try:
                # Generate a silent WAV file
                audio_file = self.generate_silent_audio(duration)
                
                # Create the audio file content
                audio_content = audio_file.getvalue()
                
                # Verify audio file has content
                if len(audio_content) == 0:
                    raise ValueError("Generated audio file is empty")
                
                # Create song with audio file
                song = Song.objects.create(
                    user=artist,
                    album=album,
                    title=f'Test Song {i}',
                    duration=duration,
                    release_date=(datetime.now() - timedelta(days=i)).date(),
                    audio_file=ContentFile(
                        audio_content,
                        name=f'test_song_{i}.wav'
                    ),
                    visibility=1  # Public
                )
                
                # Verify the file was saved
                song.refresh_from_db()
                if not song.audio_file:
                    raise ValueError("Audio file was not saved to song")
                
                # Add random genres
                import random
                selected_genres = random.sample(genres, min(2, len(genres)))
                song.genres.set(selected_genres)
                
                created_count += 1
                file_size = len(audio_content) / 1024  # Size in KB
                self.stdout.write(f'  ✓ Created: {song.title} ({duration}s, {file_size:.1f}KB)')
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Failed to create song {i}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Created {created_count} songs with audio files!'))
        self.stdout.write(self.style.SUCCESS(f'\nYou can now play these songs in your app.'))
        self.stdout.write(self.style.SUCCESS(f'Artist login: test_artist / password123'))

    def generate_silent_audio(self, duration_seconds=180):
        """
        Generate a WAV audio file with audible tones (not silent)
        Creates a simple melody with different frequencies
        """
        sample_rate = 44100
        num_frames = sample_rate * duration_seconds
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            # Set WAV parameters - must be set before writing frames
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit (2 bytes per sample)
            wav_file.setframerate(sample_rate)
            
            # Generate audio with tones (not silent)
            # Create a simple melody with different frequencies
            frames_per_tone = sample_rate * 2  # 2 seconds per tone
            tones = [440, 523, 659, 784, 880, 659, 523, 440]  # A, C, E, G, A, E, C, A (A minor chord progression)
            
            # Pre-allocate audio data list for better performance
            audio_data = bytearray()
            
            for frame in range(num_frames):
                # Cycle through tones
                tone_index = (frame // frames_per_tone) % len(tones)
                frequency = tones[tone_index]
                
                # Generate sine wave
                t = frame / sample_rate
                amplitude = 0.3  # 30% volume to avoid clipping
                sample_value = amplitude * 32767 * math.sin(2 * math.pi * frequency * t)
                
                # Clamp to 16-bit range and convert to int
                sample_value = int(max(-32768, min(32767, sample_value)))
                
                # Pack as 16-bit signed integer (little-endian) for stereo
                # Left and right channels have the same value
                audio_data.extend(struct.pack('<hh', sample_value, sample_value))
            
            # Write all frames at once
            wav_file.writeframes(bytes(audio_data))
        
        # Verify the WAV file is valid
        wav_buffer.seek(0)
        try:
            # Try to read it back to verify it's valid
            with wave.open(wav_buffer, 'rb') as test_wav:
                frames = test_wav.getnframes()
                if frames == 0:
                    raise ValueError("Generated WAV file has no frames")
            wav_buffer.seek(0)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Warning: Generated WAV might be invalid: {e}'))
            wav_buffer.seek(0)
        
        return wav_buffer
