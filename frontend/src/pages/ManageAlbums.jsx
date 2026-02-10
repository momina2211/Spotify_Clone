import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { albumsAPI } from '../services/api';
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline';

export default function ManageAlbums() {
  const { isArtist } = useAuth();
  const navigate = useNavigate();
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    release_date: '',
    cover_image: null,
  });

  useEffect(() => {
    if (!isArtist) {
      navigate('/');
      return;
    }
    loadAlbums();
  }, [isArtist, navigate]);

  const loadAlbums = async () => {
    try {
      const response = await albumsAPI.getAll();
      setAlbums(response.data);
    } catch (error) {
      console.error('Failed to load albums:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAlbum = async (e) => {
    e.preventDefault();
    try {
      const uploadData = new FormData();
      uploadData.append('title', formData.title);
      uploadData.append('release_date', formData.release_date || new Date().toISOString().split('T')[0]);
      if (formData.cover_image) {
        uploadData.append('cover_image', formData.cover_image);
      }

      await albumsAPI.create(uploadData);
      setShowCreateModal(false);
      setFormData({ title: '', release_date: '', cover_image: null });
      loadAlbums();
    } catch (error) {
      console.error('Failed to create album:', error);
      alert('Failed to create album');
    }
  };

  const handleDeleteAlbum = async (albumId) => {
    if (!window.confirm('Are you sure you want to delete this album?')) return;

    try {
      await albumsAPI.delete(albumId);
      loadAlbums();
    } catch (error) {
      console.error('Failed to delete album:', error);
      alert('Failed to delete album');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-black">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="bg-black min-h-screen pb-32">
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold text-white">Manage Albums</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-green-500 hover:bg-green-400 text-black font-bold py-3 px-6 rounded-lg transition-colors flex items-center space-x-2"
          >
            <PlusIcon className="w-5 h-5" />
            <span>Create Album</span>
          </button>
        </div>

        {albums.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 mb-4">No albums yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-2 bg-white text-black rounded-full font-medium hover:scale-105 transition-transform"
            >
              Create Your First Album
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {albums.map((album) => (
              <div
                key={album.id}
                className="group bg-white/5 hover:bg-white/10 rounded-lg p-4 transition-all"
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
                <p className="text-gray-400 text-sm mb-2">
                  {new Date(album.release_date).getFullYear()}
                </p>
                <div className="flex space-x-2">
                  <button
                    onClick={() => navigate(`/album/${album.id}`)}
                    className="text-green-500 hover:text-green-400 text-sm"
                  >
                    View
                  </button>
                  <button
                    onClick={() => handleDeleteAlbum(album.id)}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    <TrashIcon className="w-4 h-4 inline" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Album Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-white mb-4">Create Album</h2>
            <form onSubmit={handleCreateAlbum}>
              <div className="space-y-4">
                <div>
                  <label className="block text-white mb-2">Album Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    required
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white"
                    placeholder="Enter album title"
                  />
                </div>
                <div>
                  <label className="block text-white mb-2">Release Date</label>
                  <input
                    type="date"
                    value={formData.release_date}
                    onChange={(e) => setFormData({ ...formData, release_date: e.target.value })}
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-white"
                  />
                </div>
                <div>
                  <label className="block text-white mb-2">Cover Image</label>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={(e) => setFormData({ ...formData, cover_image: e.target.files[0] })}
                    className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg text-white"
                  />
                </div>
              </div>
              <div className="flex space-x-4 mt-6">
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
                    setFormData({ title: '', release_date: '', cover_image: null });
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
