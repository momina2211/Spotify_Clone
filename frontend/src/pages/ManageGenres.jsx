import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { genresAPI } from '../services/api';
import { PlusIcon, TrashIcon } from '@heroicons/react/24/outline';

export default function ManageGenres() {
  const { isArtist } = useAuth();
  const navigate = useNavigate();
  const [genres, setGenres] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newGenre, setNewGenre] = useState('');

  useEffect(() => {
    if (!isArtist) {
      navigate('/');
      return;
    }
    loadGenres();
  }, [isArtist, navigate]);

  const loadGenres = async () => {
    try {
      const response = await genresAPI.getAll();
      setGenres(response.data);
    } catch (error) {
      console.error('Failed to load genres:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGenre = async (e) => {
    e.preventDefault();
    if (!newGenre.trim()) return;

    try {
      await genresAPI.create({ title: newGenre.trim() });
      setNewGenre('');
      setShowCreateModal(false);
      loadGenres();
    } catch (error) {
      console.error('Failed to create genre:', error);
      alert('Failed to create genre');
    }
  };

  const handleDeleteGenre = async (genreId) => {
    if (!window.confirm('Are you sure you want to delete this genre?')) return;

    try {
      await genresAPI.delete(genreId);
      loadGenres();
    } catch (error) {
      console.error('Failed to delete genre:', error);
      alert('Failed to delete genre');
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
          <h1 className="text-4xl font-bold text-white">Manage Genres</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-green-500 hover:bg-green-400 text-black font-bold py-3 px-6 rounded-lg transition-colors flex items-center space-x-2"
          >
            <PlusIcon className="w-5 h-5" />
            <span>Create Genre</span>
          </button>
        </div>

        {genres.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 mb-4">No genres yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-6 py-2 bg-white text-black rounded-full font-medium hover:scale-105 transition-transform"
            >
              Create Your First Genre
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
            {genres.map((genre) => (
              <div
                key={genre.id}
                className="group bg-white/5 hover:bg-white/10 rounded-lg p-4 transition-all"
              >
                <h3 className="text-white font-medium mb-2">{genre.title}</h3>
                <button
                  onClick={() => handleDeleteGenre(genre.id)}
                  className="text-red-400 hover:text-red-300 text-sm flex items-center space-x-1"
                >
                  <TrashIcon className="w-4 h-4" />
                  <span>Delete</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Genre Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/80 z-50 flex items-center justify-center">
          <div className="bg-gray-900 rounded-lg p-6 w-full max-w-md">
            <h2 className="text-2xl font-bold text-white mb-4">Create Genre</h2>
            <form onSubmit={handleCreateGenre}>
              <input
                type="text"
                value={newGenre}
                onChange={(e) => setNewGenre(e.target.value)}
                placeholder="Genre name"
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
                    setNewGenre('');
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
