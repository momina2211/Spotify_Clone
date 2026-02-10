import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { playlistsAPI, songsAPI } from '../services/api';
import { usePlayer } from '../context/PlayerContext';
import { PlayIcon, PauseIcon, HeartIcon, EllipsisHorizontalIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutlineIcon } from '@heroicons/react/24/outline';

export default function PlaylistDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [playlist, setPlaylist] = useState(null);
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const { playSong, currentSong, isPlaying, togglePlayPause } = usePlayer();

  useEffect(() => {
    loadPlaylist();
  }, [id]);

  // Refresh songs if this is "Liked Songs" playlist when favorites change
  useEffect(() => {
    if (playlist && playlist.name === 'Liked Songs') {
      // Listen for favorite changes and refresh
      const handleFavoriteChange = () => {
        // Reload favorites for Liked Songs playlist
        songsAPI.favorites()
          .then(response => {
            setSongs(response.data || []);
          })
          .catch(error => {
            console.error('Failed to refresh favorites:', error);
          });
      };
      window.addEventListener('favoriteChanged', handleFavoriteChange);
      return () => {
        window.removeEventListener('favoriteChanged', handleFavoriteChange);
      };
    }
  }, [playlist]);

  const loadPlaylist = async () => {
    try {
      const response = await playlistsAPI.getById(id);
      setPlaylist(response.data);
      
      // If this is "Liked Songs" playlist, always load from favorites API to show all liked songs
      if (response.data.name === 'Liked Songs') {
        try {
          const favoritesResponse = await songsAPI.favorites();
          setSongs(favoritesResponse.data || []);
        } catch (error) {
          console.error('Failed to load favorites:', error);
          // Fallback to playlist songs if favorites API fails
          setSongs(response.data.playlist_songs?.map(ps => ps.song) || []);
        }
      } else {
        // For regular playlists, use playlist songs
        setSongs(response.data.playlist_songs?.map(ps => ps.song) || []);
      }
    } catch (error) {
      console.error('Failed to load playlist:', error);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayAll = () => {
    if (songs.length > 0) {
      playSong(songs[0], songs);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-black">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  if (!playlist) {
    return (
      <div className="flex items-center justify-center h-screen bg-black">
        <div className="text-white text-xl">Playlist not found</div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-b from-gray-900 via-black to-black min-h-screen pb-32">
      {/* Header */}
      <div className="relative pt-8 pb-12 px-8">
        <div className="flex items-end space-x-6">
          {playlist.cover_image ? (
            <img
              src={playlist.cover_image}
              alt={playlist.name}
              className="w-64 h-64 rounded-lg shadow-2xl object-cover"
            />
          ) : (
            <div className="w-64 h-64 rounded-lg shadow-2xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
              <span className="text-white text-6xl font-bold">
                {playlist.name[0]?.toUpperCase()}
              </span>
            </div>
          )}
          <div className="flex-1">
            <p className="text-sm text-white mb-2">Playlist</p>
            <h1 className="text-6xl font-bold text-white mb-4">{playlist.name}</h1>
            {playlist.description && (
              <p className="text-gray-400 mb-4">{playlist.description}</p>
            )}
            <div className="flex items-center space-x-2 text-sm text-gray-400">
              <span>{playlist.user}</span>
              <span>•</span>
              <span>{songs.length} songs</span>
            </div>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="px-8 mb-4">
        <div className="flex items-center space-x-4">
          <button
            onClick={handlePlayAll}
            className="bg-green-500 hover:bg-green-400 rounded-full p-4 transition-colors"
          >
            {currentSong && songs.some(s => s.id === currentSong.id) && isPlaying ? (
              <PauseIcon className="w-6 h-6 text-black" />
            ) : (
              <PlayIcon className="w-6 h-6 text-black ml-0.5" />
            )}
          </button>
          <button className="text-gray-400 hover:text-white">
            <HeartOutlineIcon className="w-6 h-6" />
          </button>
          <button className="text-gray-400 hover:text-white">
            <EllipsisHorizontalIcon className="w-6 h-6" />
          </button>
        </div>
      </div>

      {/* Songs List */}
      <div className="px-8">
        <div className="border-b border-gray-800 pb-2 mb-4">
          <div className="grid grid-cols-12 gap-4 text-gray-400 text-sm">
            <div className="col-span-1 text-center">#</div>
            <div className="col-span-5">Title</div>
            <div className="col-span-3">Album</div>
            <div className="col-span-2">Date Added</div>
            <div className="col-span-1 text-right">Duration</div>
          </div>
        </div>
        <div className="space-y-1">
          {songs.map((song, index) => {
            const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;
            return (
              <div
                key={song.id}
                className="group grid grid-cols-12 gap-4 items-center p-2 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
                onClick={() => isCurrentlyPlaying ? togglePlayPause() : playSong(song, songs)}
              >
                <div className="col-span-1 text-center text-gray-400 group-hover:hidden">
                  {index + 1}
                </div>
                <div className="col-span-1 hidden group-hover:block">
                  {isCurrentlyPlaying ? (
                    <PauseIcon className="w-5 h-5 text-white mx-auto" />
                  ) : (
                    <PlayIcon className="w-5 h-5 text-white mx-auto" />
                  )}
                </div>
                <div className="col-span-5 flex items-center space-x-3">
                  {song.album?.cover_image && (
                    <img
                      src={song.album.cover_image}
                      alt={song.title}
                      className="w-10 h-10 rounded object-cover"
                    />
                  )}
                  <div className="min-w-0">
                    <p className={`text-sm truncate ${isCurrentlyPlaying ? 'text-green-500' : 'text-white'}`}>
                      {song.title}
                    </p>
                    <p className="text-gray-400 text-xs truncate">
                      {song.user || 'Unknown Artist'}
                    </p>
                  </div>
                </div>
                <div className="col-span-3 text-gray-400 text-sm truncate">
                  {song.album?.title || '-'}
                </div>
                <div className="col-span-2 text-gray-400 text-sm">
                  {new Date(playlist.created_at).toLocaleDateString()}
                </div>
                <div className="col-span-1 text-gray-400 text-sm text-right">
                  {Math.floor(song.duration / 60)}:{(song.duration % 60).toString().padStart(2, '0')}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
