"""
Celery tasks for music-related background jobs
"""
from celery import shared_task
from django.conf import settings
from django.db.models import Q
from music.models import Song, Playlist, PlaylistSong
from users.models import User
import openai
import json


@shared_task
def generate_ai_playlist(user_id, prompt, playlist_name=None):
    """
    Generate a playlist from a natural language prompt using AI.
    
    Args:
        user_id: UUID of the user requesting the playlist
        prompt: Natural language description (e.g., "Songs for a rainy drive in Bahawalpur")
        playlist_name: Optional custom name for the playlist
    
    Returns:
        dict: Playlist data with songs
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Get user preferences (favorite genres, recently played, etc.)
        from music.models import FavoriteSong, RecentlyPlayed
        favorite_genres = FavoriteSong.objects.filter(user=user).values_list(
            'song__genres__title', flat=True
        ).distinct()[:5]
        
        recently_played_genres = RecentlyPlayed.objects.filter(user=user).values_list(
            'song__genres__title', flat=True
        ).distinct()[:5]
        
        user_preferences = {
            'favorite_genres': list(favorite_genres),
            'recent_genres': list(recently_played_genres),
        }
        
        # Call LLM to get acoustic and mood parameters
        llm_response = get_playlist_parameters_from_llm(prompt, user_preferences)
        
        if not llm_response:
            return {'error': 'Failed to generate playlist parameters'}
        
        # Extract parameters from LLM response
        target_valence = llm_response.get('valence', 0.5)
        target_energy = llm_response.get('energy', 0.5)
        target_acousticness = llm_response.get('acousticness', 0.5)
        target_genres = llm_response.get('genres', [])
        target_mood = llm_response.get('mood', None)
        num_songs = llm_response.get('num_songs', 20)
        
        # Filter songs based on parameters
        queryset = Song.objects.filter(visibility=1)  # Only public songs
        
        # Filter by genres if specified
        if target_genres:
            queryset = queryset.filter(genres__title__in=target_genres).distinct()
        
        # Filter by mood if specified
        if target_mood:
            queryset = queryset.filter(mood_tag__icontains=target_mood)
        
        # Filter by audio features (with tolerance)
        tolerance = 0.2  # Allow 20% deviation
        if target_valence is not None:
            queryset = queryset.filter(
                valence__gte=target_valence - tolerance,
                valence__lte=target_valence + tolerance
            )
        
        if target_energy is not None:
            queryset = queryset.filter(
                energy__gte=target_energy - tolerance,
                energy__lte=target_energy + tolerance
            )
        
        if target_acousticness is not None:
            queryset = queryset.filter(
                acousticness__gte=target_acousticness - tolerance,
                acousticness__lte=target_acousticness + tolerance
            )
        
        # Order by relevance (play count, likes, recency)
        songs = queryset.order_by('-play_count', '-likes', '-created_at')[:num_songs]
        
        if not songs.exists():
            # Fallback: use broader criteria if no exact matches
            songs = Song.objects.filter(visibility=1).order_by(
                '-play_count', '-likes', '-created_at'
            )[:num_songs]
        
        # Create playlist
        playlist_name = playlist_name or f"AI Playlist: {prompt[:50]}"
        playlist = Playlist.objects.create(
            user=user,
            name=playlist_name,
            description=f"Generated from prompt: {prompt}",
            is_public=False
        )
        
        # Add songs to playlist
        for idx, song in enumerate(songs):
            PlaylistSong.objects.create(
                playlist=playlist,
                song=song,
                order=idx
            )
        
        return {
            'playlist_id': str(playlist.id),
            'playlist_name': playlist.name,
            'num_songs': songs.count(),
            'songs': [{'id': str(s.id), 'title': s.title} for s in songs]
        }
        
    except User.DoesNotExist:
        return {'error': 'User not found'}
    except Exception as e:
        return {'error': str(e)}


def get_playlist_parameters_from_llm(prompt, user_preferences):
    """
    Use OpenAI GPT-4 or Gemini to extract playlist parameters from prompt.
    
    Returns:
        dict: {
            'valence': float (0.0-1.0),
            'energy': float (0.0-1.0),
            'acousticness': float (0.0-1.0),
            'genres': list of genre names,
            'mood': str,
            'num_songs': int
        }
    """
    try:
        openai_api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not openai_api_key:
            # Fallback to default values
            return {
                'valence': 0.5,
                'energy': 0.5,
                'acousticness': 0.5,
                'genres': [],
                'mood': None,
                'num_songs': 20
            }
        
        client = openai.OpenAI(api_key=openai_api_key)
        
        system_prompt = """You are a music playlist generator. Analyze the user's prompt and extract:
1. Valence (0.0 = sad/negative, 1.0 = happy/positive)
2. Energy (0.0 = calm/relaxed, 1.0 = energetic/intense)
3. Acousticness (0.0 = electronic, 1.0 = acoustic)
4. Relevant genres (list of music genres)
5. Mood tag (e.g., "happy", "sad", "energetic", "calm", "romantic")
6. Number of songs (typically 15-30)

Return ONLY a JSON object with these keys: valence, energy, acousticness, genres (array), mood, num_songs."""

        user_prompt = f"""
User prompt: "{prompt}"

User preferences:
- Favorite genres: {', '.join(user_preferences.get('favorite_genres', []))}
- Recent genres: {', '.join(user_preferences.get('recent_genres', []))}

Extract playlist parameters from the prompt.
"""
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Parse JSON response
        if result_text.startswith('```json'):
            result_text = result_text.replace('```json', '').replace('```', '').strip()
        elif result_text.startswith('```'):
            result_text = result_text.replace('```', '').strip()
        
        result = json.loads(result_text)
        
        # Validate and set defaults
        return {
            'valence': float(result.get('valence', 0.5)),
            'energy': float(result.get('energy', 0.5)),
            'acousticness': float(result.get('acousticness', 0.5)),
            'genres': result.get('genres', []),
            'mood': result.get('mood', None),
            'num_songs': int(result.get('num_songs', 20))
        }
        
    except Exception as e:
        # Fallback to default values on error
        return {
            'valence': 0.5,
            'energy': 0.5,
            'acousticness': 0.5,
            'genres': [],
            'mood': None,
            'num_songs': 20
        }


@shared_task
def analyze_audio_features(song_id):
    """
    Analyze audio file using Librosa to extract BPM, valence, energy, acousticness.
    
    Args:
        song_id: UUID of the song to analyze
    """
    try:
        song = Song.objects.get(id=song_id)
        
        if not song.audio_file:
            return {'error': 'No audio file found'}
        
        import librosa
        import numpy as np
        
        # Load audio file
        audio_path = song.audio_file.path
        y, sr = librosa.load(audio_path, duration=60)  # Analyze first 60 seconds
        
        # Extract features
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = float(tempo)
        
        # Extract spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
        
        # Calculate energy (normalized)
        energy = float(np.mean(librosa.feature.rms(y=y)[0]))
        energy = min(1.0, max(0.0, energy * 10))  # Normalize to 0-1
        
        # Estimate valence (simplified: based on spectral centroid and tempo)
        # Higher tempo + higher centroid = more positive/happy
        valence = float(np.mean(spectral_centroids) / 5000)  # Normalize
        valence = min(1.0, max(0.0, valence))
        
        # Estimate acousticness (simplified: based on zero crossing rate)
        # Lower ZCR = more acoustic
        acousticness = 1.0 - float(np.mean(zero_crossing_rate))
        acousticness = min(1.0, max(0.0, acousticness))
        
        # Determine mood tag
        if valence > 0.6 and energy > 0.6:
            mood_tag = "happy"
        elif valence < 0.4 and energy < 0.4:
            mood_tag = "sad"
        elif energy > 0.7:
            mood_tag = "energetic"
        elif energy < 0.3:
            mood_tag = "calm"
        else:
            mood_tag = "neutral"
        
        # Update song
        song.bpm = bpm
        song.valence = valence
        song.energy = energy
        song.acousticness = acousticness
        song.mood_tag = mood_tag
        song.save(update_fields=['bpm', 'valence', 'energy', 'acousticness', 'mood_tag'])
        
        return {
            'success': True,
            'bpm': bpm,
            'valence': valence,
            'energy': energy,
            'acousticness': acousticness,
            'mood_tag': mood_tag
        }
        
    except Song.DoesNotExist:
        return {'error': 'Song not found'}
    except Exception as e:
        return {'error': str(e)}


@shared_task
def enrich_song_metadata(song_id):
    """
    Enrich song metadata using Scrapy to fetch lyrics and artist bio.
    
    Args:
        song_id: UUID of the song to enrich
    """
    try:
        song = Song.objects.get(id=song_id)
        artist = song.user
        
        if not artist:
            return {'error': 'No artist found for song'}
        
        # Fetch lyrics from Genius (placeholder - would use Scrapy in production)
        lyrics_data = fetch_lyrics_from_genius(song.title, artist.username)
        
        if lyrics_data:
            song.lyrics_json = lyrics_data
            song.save(update_fields=['lyrics_json'])
        
        # Fetch artist bio from MusicBrainz (placeholder)
        if artist.role == 2:  # Artist role
            bio = fetch_artist_bio_from_musicbrainz(artist.username)
            if bio:
                profile = artist.profile
                if profile:
                    profile.bio = bio
                    profile.save(update_fields=['bio'])
        
        return {
            'success': True,
            'lyrics_fetched': bool(lyrics_data),
            'bio_fetched': bool(bio if 'bio' in locals() else False)
        }
        
    except Song.DoesNotExist:
        return {'error': 'Song not found'}
    except Exception as e:
        return {'error': str(e)}


def fetch_lyrics_from_genius(song_title, artist_name):
    """
    Fetch lyrics from Genius API (placeholder - would use Scrapy in production).
    
    Returns:
        list: Timestamped lyrics in format [{'time': 10.5, 'text': 'lyrics...'}]
    """
    # Placeholder implementation
    # In production, this would use Scrapy to scrape Genius or use their API
    # For now, return None (would be implemented with actual scraping)
    return None


def fetch_artist_bio_from_musicbrainz(artist_name):
    """
    Fetch artist biography from MusicBrainz (placeholder - would use Scrapy).
    
    Returns:
        str: Artist biography
    """
    # Placeholder implementation
    # In production, this would use Scrapy to scrape MusicBrainz
    # For now, return None (would be implemented with actual scraping)
    return None




