import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { artistsAPI } from '../services/api';
import { usePlayer } from '../context/PlayerContext';
import { PlayIcon, PauseIcon, UserGroupIcon } from '@heroicons/react/24/solid';

export default function ArtistDetail() {
  const { id } = useParams();
  const [artist, setArtist] = useState(null);
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const { playSong, currentSong, isPlaying, togglePlayPause } = usePlayer();

  useEffect(() => {
    loadArtist();
  }, [id]);

  const loadArtist = async () => {
    try {
      const [profileRes, songsRes] = await Promise.all([
        artistsAPI.getProfile(id),
        artistsAPI.getSongs(id),
      ]);
      setArtist(profileRes.data);
      setSongs(songsRes.data);
    } catch (error) {
      console.error('Failed to load artist:', error);
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

  if (!artist) {
    return (
      <div className="flex items-center justify-center h-screen bg-black">
        <div className="text-white text-xl">Artist not found</div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-b from-gray-900 via-black to-black min-h-screen pb-32">
      {/* Header */}
      <div className="relative pt-8 pb-12 px-8">
        <div className="flex items-end space-x-6">
          <div className="w-64 h-64 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center shadow-2xl">
            <UserGroupIcon className="w-32 h-32 text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm text-white mb-2">Artist</p>
            <h1 className="text-6xl font-bold text-white mb-4">{artist.username}</h1>
            <div className="flex items-center space-x-2 text-sm text-gray-400">
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
        </div>
      </div>

      {/* Popular Songs */}
      <div className="px-8 mb-8">
        <h2 className="text-2xl font-bold text-white mb-4">Popular</h2>
        <div className="space-y-1">
          {songs.slice(0, 5).map((song, index) => {
            const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;
            return (
              <div
                key={song.id}
                className="group flex items-center space-x-4 p-2 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
                onClick={() => isCurrentlyPlaying ? togglePlayPause() : playSong(song, songs)}
              >
                <div className="w-8 text-center text-gray-400 group-hover:hidden">
                  {index + 1}
                </div>
                <div className="w-8 hidden group-hover:block">
                  {isCurrentlyPlaying ? (
                    <PauseIcon className="w-5 h-5 text-white" />
                  ) : (
                    <PlayIcon className="w-5 h-5 text-white" />
                  )}
                </div>
                {song.album?.cover_image && (
                  <img
                    src={song.album.cover_image}
                    alt={song.title}
                    className="w-10 h-10 rounded object-cover"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <p className={`text-sm truncate ${isCurrentlyPlaying ? 'text-green-500' : 'text-white'}`}>
                    {song.title}
                  </p>
                </div>
                <div className="text-gray-400 text-xs">
                  {Math.floor(song.duration / 60)}:{(song.duration % 60).toString().padStart(2, '0')}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* All Songs */}
      <div className="px-8">
        <h2 className="text-2xl font-bold text-white mb-4">All Songs</h2>
        <div className="space-y-1">
          {songs.map((song, index) => {
            const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;
            return (
              <div
                key={song.id}
                className="group flex items-center space-x-4 p-2 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
                onClick={() => isCurrentlyPlaying ? togglePlayPause() : playSong(song, songs)}
              >
                <div className="w-8 text-center text-gray-400 group-hover:hidden">
                  {index + 1}
                </div>
                <div className="w-8 hidden group-hover:block">
                  {isCurrentlyPlaying ? (
                    <PauseIcon className="w-5 h-5 text-white" />
                  ) : (
                    <PlayIcon className="w-5 h-5 text-white" />
                  )}
                </div>
                {song.album?.cover_image && (
                  <img
                    src={song.album.cover_image}
                    alt={song.title}
                    className="w-10 h-10 rounded object-cover"
                  />
                )}
                <div className="flex-1 min-w-0">
                  <p className={`text-sm truncate ${isCurrentlyPlaying ? 'text-green-500' : 'text-white'}`}>
                    {song.title}
                  </p>
                  {song.album && (
                    <p className="text-gray-400 text-xs truncate">{song.album.title}</p>
                  )}
                </div>
                <div className="text-gray-400 text-xs">
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
