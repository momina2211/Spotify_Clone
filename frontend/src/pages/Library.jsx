import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { playlistsAPI, albumsAPI, songsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { PlusIcon, MagnifyingGlassIcon, Squares2X2Icon, ListBulletIcon } from '@heroicons/react/24/outline';

export default function Library() {
  const [playlists, setPlaylists] = useState([]);
  const [favoriteAlbums, setFavoriteAlbums] = useState([]);
  const [favoriteSongs, setFavoriteSongs] = useState([]);
  const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('playlists'); // 'playlists', 'albums', 'songs'
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newPlaylistName, setNewPlaylistName] = useState('');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { user } = useAuth();

  useEffect(() => {
    if (searchParams.get('create') === 'playlist') {
      setShowCreateModal(true);
    }
    loadData();
  }, [searchParams]);

  const loadData = async () => {
    try {
      const [playlistsRes, albumsRes, songsRes] = await Promise.all([
        playlistsAPI.getAll(),
        albumsAPI.favorites(),
        songsAPI.favorites(),
      ]);
      setPlaylists(playlistsRes.data);
      setFavoriteAlbums(albumsRes.data);
      setFavoriteSongs(songsRes.data);
    } catch (error) {
      console.error('Failed to load library data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlaylist = async (e) => {
    e.preventDefault();
    if (!newPlaylistName.trim()) return;

    try {
      const response = await playlistsAPI.create({ name: newPlaylistName });
      setPlaylists([...playlists, response.data]);
      setNewPlaylistName('');
      setShowCreateModal(false);
      navigate(`/playlist/${response.data.id}`);
    } catch (error) {
      console.error('Failed to create playlist:', error);
      alert('Failed to create playlist');
    }
  };

  const handleDeletePlaylist = async (playlistId) => {
    if (!window.confirm('Are you sure you want to delete this playlist?')) return;

    try {
      await playlistsAPI.delete(playlistId);
      setPlaylists(playlists.filter(p => p.id !== playlistId));
    } catch (error) {
      console.error('Failed to delete playlist:', error);
      alert('Failed to delete playlist');
    }
  };

  const filteredPlaylists = playlists.filter(p =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredAlbums = favoriteAlbums.filter(a =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredSongs = favoriteSongs.filter(s =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-black">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="bg-black min-h-screen pb-32">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-black/80 backdrop-blur-lg border-b border-gray-800 px-4 md:px-8 py-4">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl md:text-3xl font-bold text-white">Library</h1>
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
              className="text-gray-400 hover:text-white p-2"
            >
              {viewMode === 'grid' ? (
                <ListBulletIcon className="w-6 h-6" />
              ) : (
                <Squares2X2Icon className="w-6 h-6" />
              )}
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="text-gray-400 hover:text-white p-2"
            >
              <PlusIcon className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4 border-b border-gray-800">
          {['playlists', 'albums', 'songs'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-2 px-2 font-medium transition-colors ${
                activeTab === tab
                  ? 'text-white border-b-2 border-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Search */}
        <div className="mt-4 relative">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search in Library"
            className="w-full pl-10 pr-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white"
          />
        </div>
      </div>

      {/* Content */}
      <div className="p-4 md:p-8">
        {activeTab === 'playlists' && (
          <div className={viewMode === 'grid' ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4' : 'space-y-2'}>
            {filteredPlaylists.length === 0 ? (
              <div className="col-span-full text-center py-12">
                <p className="text-gray-400 mb-4">No playlists found</p>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="px-6 py-2 bg-white text-black rounded-full font-medium hover:scale-105 transition-transform"
                >
                  Create Playlist
                </button>
              </div>
            ) : (
              filteredPlaylists.map((playlist) => (
                <div
                  key={playlist.id}
                  className="group bg-white/5 hover:bg-white/10 rounded-lg p-4 transition-all cursor-pointer"
                  onClick={() => navigate(`/playlist/${playlist.id}`)}
                >
                  {playlist.cover_image ? (
                    <img
                      src={playlist.cover_image}
                      alt={playlist.name}
                      className="w-full aspect-square rounded object-cover mb-3"
                    />
                  ) : (
                    <div className="w-full aspect-square rounded bg-gradient-to-br from-purple-500 to-blue-500 mb-3 flex items-center justify-center">
                      <span className="text-white text-4xl font-bold">
                        {playlist.name[0]?.toUpperCase()}
                      </span>
                    </div>
                  )}
                  <h3 className="text-white font-medium truncate mb-1">{playlist.name}</h3>
                  <p className="text-gray-400 text-sm">
                    {playlist.songs_count || 0} songs
                  </p>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'albums' && (
          <div className={viewMode === 'grid' ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4' : 'space-y-2'}>
            {filteredAlbums.length === 0 ? (
              <div className="col-span-full text-center py-12 text-gray-400">
                No favorite albums
              </div>
            ) : (
              filteredAlbums.map((album) => (
                <div
                  key={album.id}
                  className="group bg-white/5 hover:bg-white/10 rounded-lg p-4 transition-all cursor-pointer"
                  onClick={() => navigate(`/album/${album.id}`)}
                >
                  {album.cover_image ? (
                    <img
                      src={album.cover_image}
                      alt={album.title}
                      className="w-full aspect-square rounded object-cover mb-3"
                    />
                  ) : (
                    <div className="w-full aspect-square rounded bg-gradient-to-br from-purple-500 to-blue-500 mb-3" />
                  )}
                  <h3 className="text-white font-medium truncate mb-1">{album.title}</h3>
                  <p className="text-gray-400 text-sm truncate">{album.user}</p>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'songs' && (
          <div className="space-y-1">
            {filteredSongs.length === 0 ? (
              <div className="text-center py-12 text-gray-400">
                No favorite songs
              </div>
            ) : (
              filteredSongs.map((song, index) => (
                <div
                  key={song.id}
                  className="group flex items-center space-x-4 p-2 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
                  onClick={() => navigate(`/song/${song.id}`)}
                >
                  <div className="w-12 h-12 flex-shrink-0">
                    {song.album?.cover_image ? (
                      <img
                        src={song.album.cover_image}
                        alt={song.title}
                        className="w-full h-full rounded object-cover"
                      />
                    ) : (
                      <div className="w-full h-full rounded bg-gradient-to-br from-purple-500 to-blue-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">{song.title}</p>
                    <p className="text-gray-400 text-sm truncate">
                      {song.user || 'Unknown Artist'}
                    </p>
                  </div>
                  <div className="text-gray-400 text-sm">
                    {Math.floor(song.duration / 60)}:{(song.duration % 60).toString().padStart(2, '0')}
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Create Playlist Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-white mb-4">Create Playlist</h2>
            <form onSubmit={handleCreatePlaylist}>
              <input
                type="text"
                value={newPlaylistName}
                onChange={(e) => setNewPlaylistName(e.target.value)}
                placeholder="Playlist name"
                className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white mb-4"
                autoFocus
              />
              <div className="flex space-x-4">
                <button
                  type="submit"
                  className="flex-1 px-6 py-2 bg-white text-black rounded-full font-medium hover:scale-105 transition-transform"
                >
                  Create
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewPlaylistName('');
                  }}
                  className="flex-1 px-6 py-2 bg-white/10 text-white rounded-full font-medium hover:bg-white/20 transition-colors"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
