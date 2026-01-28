import { useState, useEffect } from 'react';
import { songsAPI, albumsAPI } from '../services/api';
import SongCard from '../components/SongCard';
import { HeartIcon } from '@heroicons/react/24/solid';

export default function Favorites() {
  const [favoriteSongs, setFavoriteSongs] = useState([]);
  const [favoriteAlbums, setFavoriteAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('songs');

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const [songsRes, albumsRes] = await Promise.all([
        songsAPI.favorites(),
        albumsAPI.favorites(),
      ]);
      setFavoriteSongs(songsRes.data);
      setFavoriteAlbums(albumsRes.data);
    } catch (error) {
      console.error('Failed to load favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-8 pb-32">
      <div className="flex items-center space-x-2 mb-8">
        <HeartIcon className="w-8 h-8 text-red-500" />
        <h1 className="text-4xl font-bold text-white">Your Favorites</h1>
      </div>

      <div className="flex space-x-4 mb-6">
        <button
          onClick={() => setActiveTab('songs')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'songs'
              ? 'bg-green-500 text-white'
              : 'bg-white/10 text-gray-400 hover:text-white'
          }`}
        >
          Songs ({favoriteSongs.length})
        </button>
        <button
          onClick={() => setActiveTab('albums')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'albums'
              ? 'bg-green-500 text-white'
              : 'bg-white/10 text-gray-400 hover:text-white'
          }`}
        >
          Albums ({favoriteAlbums.length})
        </button>
      </div>

      {activeTab === 'songs' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {favoriteSongs.length > 0 ? (
            favoriteSongs.map((song) => (
              <SongCard
                key={song.id}
                song={song}
                onFavoriteChange={loadFavorites}
                showFavorite={true}
              />
            ))
          ) : (
            <div className="text-gray-400 col-span-full text-center py-8">
              No favorite songs yet
            </div>
          )}
        </div>
      )}

      {activeTab === 'albums' && (
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {favoriteAlbums.length > 0 ? (
            favoriteAlbums.map((album) => (
              <div
                key={album.id}
                className="bg-white/5 hover:bg-white/10 rounded-lg p-4 cursor-pointer transition-all"
              >
                {album.cover_image ? (
                  <img
                    src={album.cover_image}
                    alt={album.title}
                    className="w-full aspect-square rounded object-cover mb-2"
                  />
                ) : (
                  <div className="w-full aspect-square rounded bg-gradient-to-br from-purple-500 to-blue-500 mb-2" />
                )}
                <h3 className="text-white font-medium truncate">{album.title}</h3>
                <p className="text-gray-400 text-sm truncate">{album.user}</p>
              </div>
            ))
          ) : (
            <div className="text-gray-400 col-span-full text-center py-8">
              No favorite albums yet
            </div>
          )}
        </div>
      )}
    </div>
  );
}
