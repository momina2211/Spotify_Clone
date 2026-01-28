import { useState } from 'react';
import { usePlayer } from '../context/PlayerContext';
import { songsAPI } from '../services/api';
import { HeartIcon, PlayIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutlineIcon } from '@heroicons/react/24/outline';

export default function SongCard({ song, onFavoriteChange, showFavorite = true }) {
  const { playSong, currentSong, isPlaying } = usePlayer();
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(false);

  const handlePlay = () => {
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
    } catch (error) {
      console.error('Failed to update favorite:', error);
    } finally {
      setLoading(false);
    }
  };

  const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;

  return (
    <div
      className="group bg-white/5 hover:bg-white/10 rounded-lg p-4 transition-all cursor-pointer"
      onClick={handlePlay}
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
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity rounded flex items-center justify-center">
            <PlayIcon className="w-8 h-8 text-white" />
          </div>
        </div>

        <div className="flex-1 min-w-0">
          <h3 className={`font-medium truncate ${isCurrentlyPlaying ? 'text-green-500' : 'text-white'}`}>
            {song.title}
          </h3>
          <p className="text-gray-400 text-sm truncate">
            {song.user || 'Unknown Artist'}
          </p>
          {song.genre && (
            <p className="text-gray-500 text-xs mt-1">{song.genre.title}</p>
          )}
        </div>

        <div className="flex items-center space-x-2">
          {showFavorite && (
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
