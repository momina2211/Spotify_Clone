import { useState, useEffect } from 'react';
import { usePlayer } from '../context/PlayerContext';
import { useAuth } from '../context/AuthContext';
import { songsAPI } from '../services/api';
import { HeartIcon, PlayIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutlineIcon } from '@heroicons/react/24/outline';

export default function SongCard({ song, onFavoriteChange, showFavorite = true }) {
  const { playSong, currentSong, isPlaying } = usePlayer();
  const { isArtist } = useAuth();
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(false);

  // Check if song is favorited on mount and when song changes
  useEffect(() => {
    if (showFavorite && !isArtist && song?.id) {
      checkFavoriteStatus();
    }
  }, [song?.id, showFavorite, isArtist]);

  const checkFavoriteStatus = async () => {
    try {
      const response = await songsAPI.favorites();
      const favoriteSongs = response.data || [];
      const isFavorited = favoriteSongs.some(favSong => favSong.id === song.id);
      setIsFavorite(isFavorited);
    } catch (error) {
      console.error('Failed to check favorite status:', error);
    }
  };

  const handlePlay = (e) => {
    e?.stopPropagation();
    // Check if song has a valid audio file - handle null, undefined, empty string, etc.
    const hasAudioFile = song.audio_file && 
                        typeof song.audio_file === 'string' && 
                        song.audio_file.trim() !== '' &&
                        song.audio_file !== 'null' &&
                        song.audio_file !== 'undefined';
    if (!hasAudioFile) {
      console.warn('Cannot play song - no valid audio file:', song.title);
      return; // Don't play if no audio file
    }
    playSong(song);
  };

  const handleFavorite = async (e) => {
    e.stopPropagation();
    if (loading) return;

    setLoading(true);
    try {
      if (isFavorite) {
        await songsAPI.removeFavorite(song.id);
        setIsFavorite(false);
      } else {
        await songsAPI.addFavorite(song.id);
        setIsFavorite(true);
      }
      if (onFavoriteChange) onFavoriteChange();
      // Notify that favorites changed (for Liked Songs playlist to refresh)
      window.dispatchEvent(new Event('favoriteChanged'));
    } catch (error) {
      console.error('Failed to update favorite:', error);
    } finally {
      setLoading(false);
    }
  };

  const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;
  // More robust check for audio file
  const hasAudio = song.audio_file && 
                  typeof song.audio_file === 'string' && 
                  song.audio_file.trim() !== '' &&
                  song.audio_file !== 'null' &&
                  song.audio_file !== 'undefined';

  return (
    <div
      className={`group bg-white/5 hover:bg-white/10 rounded-lg p-4 transition-all ${
        hasAudio ? 'cursor-pointer' : 'cursor-not-allowed opacity-75'
      }`}
      onClick={hasAudio ? handlePlay : undefined}
    >
      <div className="flex items-center space-x-4">
        <div className="relative flex-shrink-0">
          {song.album?.cover_image ? (
            <img
              src={song.album.cover_image}
              alt={song.title}
              className="w-16 h-16 rounded object-cover"
            />
          ) : (
            <div className="w-16 h-16 rounded bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
              <PlayIcon className="w-8 h-8 text-white" />
            </div>
          )}
          {hasAudio ? (
            <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded flex items-center justify-center">
              <PlayIcon className="w-8 h-8 text-white" />
            </div>
          ) : (
            <div className="absolute inset-0 bg-black/70 rounded flex items-center justify-center">
              <span className="text-xs text-white font-medium bg-yellow-500/80 px-2 py-1 rounded">No Audio</span>
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className={`font-medium truncate ${isCurrentlyPlaying ? 'text-green-500' : 'text-white'}`}>
              {song.title}
            </h3>
            {!hasAudio && (
              <span className="text-xs text-yellow-400 bg-yellow-500/20 px-1.5 py-0.5 rounded" title="No audio file available">
                Metadata Only
              </span>
            )}
          </div>
          <p className="text-gray-400 text-sm truncate">
            {song.user || 'Unknown Artist'}
          </p>
          {song.genres && song.genres.length > 0 && (
            <p className="text-gray-500 text-xs mt-1">
              {song.genres.map(g => g.title).join(', ')}
            </p>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {showFavorite && !isArtist && (
            <button
              onClick={handleFavorite}
              disabled={loading}
              className="text-gray-400 hover:text-red-500 transition-colors"
            >
              {isFavorite ? (
                <HeartIcon className="w-5 h-5 text-red-500" />
              ) : (
                <HeartOutlineIcon className="w-5 h-5" />
              )}
            </button>
          )}
          <span className="text-gray-500 text-sm">
            {Math.floor(song.duration / 60)}:{(song.duration % 60).toString().padStart(2, '0')}
          </span>
        </div>
      </div>
    </div>
  );
}
