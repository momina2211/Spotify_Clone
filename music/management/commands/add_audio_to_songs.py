"""
Django management command to add audible audio files to existing songs without audio
"""
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from music.models import Song
import io
import wave
import struct
import math


class Command(BaseCommand):
    help = 'Add audible audio files to songs that don\'t have audio'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=180,
            help='Duration of audio in seconds (default: 180)'
        )
        parser.add_argument(
            '--song-id',
            type=str,
            default=None,
            help='Specific song ID to fix (optional)'
        )
        parser.add_argument(
            '--replace-all',
            action='store_true',
            help='Replace audio files for ALL songs, even if they already have audio'
        )

    def handle(self, *args, **options):
        duration = options['duration']
        song_id = options.get('song_id')
        replace_all = options.get('replace_all', False)
        
        # Get songs to fix
        if song_id:
            if replace_all:
                songs = Song.objects.filter(id=song_id)
            else:
                songs = Song.objects.filter(id=song_id, audio_file__isnull=True) | Song.objects.filter(id=song_id, audio_file='')
        else:
            if replace_all:
                songs = Song.objects.all()
            else:
                songs = Song.objects.filter(audio_file__isnull=True) | Song.objects.filter(audio_file='')
        
        total = songs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING('No songs found without audio files.'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found {total} songs without audio. Adding audio files...'))
        
        fixed_count = 0
        for i, song in enumerate(songs, 1):
            try:
                # Generate audible audio
                audio_file = self.generate_audible_audio(duration)
                audio_content = audio_file.getvalue()
                
                if len(audio_content) == 0:
                    self.stdout.write(self.style.ERROR(f'  ✗ {song.title}: Failed to generate audio'))
                    continue
                
                # Add audio file
                song.audio_file = ContentFile(
                    audio_content,
                    name=f'song_{song.id}.wav'
                )
                song.save(update_fields=['audio_file'])
                
                # Verify
                song.refresh_from_db()
                if song.audio_file:
                    fixed_count += 1
                    file_size = len(audio_content) / 1024
                    self.stdout.write(f'  [{i}/{total}] ✓ {song.title} ({file_size:.1f}KB)')
                else:
                    self.stdout.write(self.style.ERROR(f'  ✗ {song.title}: File not saved'))
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ {song.title}: {str(e)}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Fixed {fixed_count} songs with audible audio!'))

    def generate_audible_audio(self, duration_seconds=180):
        """
        Generate a WAV audio file with audible tones (melody)
        """
        sample_rate = 44100
        num_frames = sample_rate * duration_seconds
        
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Create a simple melody
            frames_per_tone = sample_rate * 2  # 2 seconds per tone
            # A minor scale: A, B, C, D, E, F, G, A
            tones = [440, 494, 523, 587, 659, 698, 784, 880]
            
            # Use bytearray for better performance
            audio_data = bytearray()
            
            for frame in range(num_frames):
                # Cycle through tones
                tone_index = (frame // frames_per_tone) % len(tones)
                frequency = tones[tone_index]
                
                # Generate sine wave
                t = frame / sample_rate
                amplitude = 0.3  # 30% volume
                sample_value = amplitude * 32767 * math.sin(2 * math.pi * frequency * t)
                
                # Clamp to 16-bit range and convert to int
                sample_value = int(max(-32768, min(32767, sample_value)))
                
                # Pack as stereo (same value for both channels)
                audio_data.extend(struct.pack('<hh', sample_value, sample_value))
            
            wav_file.writeframes(bytes(audio_data))
        
        # Verify the WAV file
        wav_buffer.seek(0)
        try:
            with wave.open(wav_buffer, 'rb') as test_wav:
                frames = test_wav.getnframes()
                if frames == 0:
                    raise ValueError("Generated WAV file has no frames")
            wav_buffer.seek(0)
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Warning: Generated WAV might be invalid: {e}'))
            wav_buffer.seek(0)
        
        return wav_buffer
