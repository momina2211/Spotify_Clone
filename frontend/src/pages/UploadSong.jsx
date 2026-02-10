import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { songsAPI, genresAPI, albumsAPI } from '../services/api';
import { MusicalNoteIcon, XMarkIcon } from '@heroicons/react/24/outline';

export default function UploadSong() {
  const { isArtist } = useAuth();
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    title: '',
    genres: [],
    album_title: '',
    album_id: '',
    release_date: '',
    audio_file: null,
  });
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [newGenre, setNewGenre] = useState('');
  const [genreSearch, setGenreSearch] = useState('');
  const [albumMode, setAlbumMode] = useState('select'); // 'select' or 'create'
  const [genres, setGenres] = useState([]);
  const [albums, setAlbums] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (!isArtist) {
      navigate('/');
      return;
    }
    loadGenres();
    loadAlbums();
  }, [isArtist, navigate]);

  const loadGenres = async () => {
    try {
      const response = await genresAPI.getAll();
      // Sort genres alphabetically by title for better UX
      const sortedGenres = response.data.sort((a, b) => {
        const titleA = (a.title || '').toLowerCase();
        const titleB = (b.title || '').toLowerCase();
        return titleA.localeCompare(titleB);
      });
      setGenres(sortedGenres);
    } catch (error) {
      console.error('Failed to load genres:', error);
      setError('Failed to load genres. Please refresh the page.');
    }
  };

  const loadAlbums = async () => {
    try {
      const response = await albumsAPI.getAll();
      setAlbums(response.data);
    } catch (error) {
      console.error('Failed to load albums:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleFileChange = (e) => {
    setFormData(prev => ({ ...prev, audio_file: e.target.files[0] }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess(false);

    if (!formData.audio_file) {
      setError('Please select an audio file');
      return;
    }

    if (!formData.title || selectedGenres.length === 0) {
      setError('Title and at least one genre are required');
      return;
    }

    setLoading(true);
    try {
      const uploadData = new FormData();
      uploadData.append('title', formData.title);
      // Append each genre separately for FormData
      selectedGenres.forEach(genre => {
        uploadData.append('genres', genre);
      });
      uploadData.append('release_date', formData.release_date || new Date().toISOString().split('T')[0]);
      uploadData.append('duration', '0'); // Will be calculated on backend
      uploadData.append('audio_file', formData.audio_file);
      
      // Handle album - either by ID (selected) or by title (new)
      if (albumMode === 'select' && formData.album_id) {
        uploadData.append('album_id', formData.album_id);
      } else if (albumMode === 'create' && formData.album_title) {
        uploadData.append('album_title', formData.album_title);
      }

      await songsAPI.create(uploadData);
      setSuccess(true);
      setFormData({
        title: '',
        genres: [],
        album_title: '',
        album_id: '',
        release_date: '',
        audio_file: null,
      });
      setSelectedGenres([]);
      setNewGenre('');
      setAlbumMode('select');
      
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = '';
      
      setTimeout(() => {
        navigate('/artist/dashboard');
      }, 2000);
    } catch (error) {
      console.error('Upload failed:', error);
      setError(error.response?.data?.error || 'Failed to upload song');
    } finally {
      setLoading(false);
    }
  };

  if (!isArtist) {
    return null;
  }

  return (
    <div className="bg-black min-h-screen pb-32">
      <div className="max-w-2xl mx-auto p-8">
        <h1 className="text-4xl font-bold text-white mb-8">Upload Song</h1>

        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-green-500/20 border border-green-500 text-green-200 px-4 py-3 rounded mb-4">
            Song uploaded successfully! Redirecting...
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-white mb-2 font-medium">Song Title *</label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              required
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
              placeholder="Enter song title"
            />
          </div>

          <div>
            <label className="block text-white mb-2 font-medium">Genres * (Select multiple)</label>
            <div className="space-y-3">
              {/* Selected Genres Display */}
              {selectedGenres.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-2">
                  {selectedGenres.map((genre, index) => (
                    <span
                      key={index}
                      className="inline-flex items-center px-3 py-1 rounded-full bg-green-500/20 text-green-300 border border-green-500/30"
                    >
                      {genre}
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedGenres(prev => prev.filter((_, i) => i !== index));
                        }}
                        className="ml-2 text-green-300 hover:text-green-100"
                      >
                        <XMarkIcon className="w-4 h-4" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
              
              {/* Genre Selection */}
              <div className="space-y-2">
                {/* Genre Search/Filter */}
                <input
                  type="text"
                  value={genreSearch}
                  onChange={(e) => setGenreSearch(e.target.value)}
                  placeholder="Search genres..."
                  className="w-full px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
                />
                <div className="flex space-x-2">
                  <select
                    onChange={(e) => {
                      const selected = e.target.value;
                      if (selected && !selectedGenres.includes(selected)) {
                        setSelectedGenres(prev => [...prev, selected]);
                        e.target.value = '';
                        setGenreSearch(''); // Clear search after selection
                      }
                    }}
                    className="genre-select flex-1 px-4 py-3 rounded-lg bg-white border border-white/20 text-black focus:outline-none focus:ring-2 focus:ring-green-500"
                    value=""
                  >
                    <option value="">Select a genre</option>
                    {genres
                      .filter(genre => {
                        if (!genre.title) return false;
                        if (selectedGenres.includes(genre.title)) return false;
                        if (genreSearch) {
                          return genre.title.toLowerCase().includes(genreSearch.toLowerCase());
                        }
                        return true;
                      })
                      .slice(0, 100) // Limit to first 100 for performance
                      .map((genre) => (
                        <option key={genre.id} value={genre.title}>
                          {genre.title}
                        </option>
                      ))}
                  </select>
                  <div className="flex space-x-2 flex-1">
                    <input
                      type="text"
                      value={newGenre}
                      onChange={(e) => setNewGenre(e.target.value)}
                      onKeyPress={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          if (newGenre.trim() && !selectedGenres.includes(newGenre.trim())) {
                            setSelectedGenres(prev => [...prev, newGenre.trim()]);
                            setNewGenre('');
                          }
                        }
                      }}
                      placeholder="Or type new genre and press Enter"
                      className="flex-1 px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                    {newGenre.trim() && !selectedGenres.includes(newGenre.trim()) && (
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedGenres(prev => [...prev, newGenre.trim()]);
                          setNewGenre('');
                        }}
                        className="px-4 py-3 bg-green-500 hover:bg-green-400 text-black font-medium rounded-lg transition-colors"
                      >
                        Add
                      </button>
                    )}
                  </div>
                </div>
                <p className="text-gray-400 text-sm">Select multiple genres from the dropdown or create new ones</p>
              </div>
            </div>
          </div>

          <div>
            <label className="block text-white mb-2 font-medium">Album (Optional)</label>
            <div className="space-y-3">
              {/* Album Mode Toggle */}
              <div className="flex space-x-2 mb-2">
                <button
                  type="button"
                  onClick={() => {
                    setAlbumMode('select');
                    setFormData(prev => ({ ...prev, album_title: '', album_id: '' }));
                  }}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    albumMode === 'select'
                      ? 'bg-green-500 text-black'
                      : 'bg-white/10 text-white hover:bg-white/20'
                  }`}
                >
                  Select Existing
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setAlbumMode('create');
                    setFormData(prev => ({ ...prev, album_title: '', album_id: '' }));
                  }}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    albumMode === 'create'
                      ? 'bg-green-500 text-black'
                      : 'bg-white/10 text-white hover:bg-white/20'
                  }`}
                >
                  Create New
                </button>
              </div>

              {/* Album Selection or Creation */}
              {albumMode === 'select' ? (
                <select
                  name="album_id"
                  value={formData.album_id}
                  onChange={handleInputChange}
                  className="genre-select w-full px-4 py-3 rounded-lg bg-white border border-white/20 text-black focus:outline-none focus:ring-2 focus:ring-green-500"
                >
                  <option value="">No album (Single)</option>
                  {albums.map((album) => (
                    <option key={album.id} value={album.id}>
                      {album.title} {album.release_date ? `(${new Date(album.release_date).getFullYear()})` : ''}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  name="album_title"
                  value={formData.album_title}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Enter album name (will be created if doesn't exist)"
                />
              )}
            </div>
          </div>

          <div>
            <label className="block text-white mb-2 font-medium">Release Date</label>
            <input
              type="date"
              name="release_date"
              value={formData.release_date}
              onChange={handleInputChange}
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>

          <div>
            <label className="block text-white mb-2 font-medium">Audio File *</label>
            <div className="border-2 border-dashed border-white/20 rounded-lg p-8 text-center hover:border-green-500 transition-colors">
              <input
                type="file"
                accept="audio/*"
                onChange={handleFileChange}
                required
                className="hidden"
                id="audio-file"
              />
              <label htmlFor="audio-file" className="cursor-pointer">
                <MusicalNoteIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-white mb-2">
                  {formData.audio_file ? formData.audio_file.name : 'Click to select audio file'}
                </p>
                <p className="text-gray-400 text-sm">MP3, WAV, or other audio formats</p>
              </label>
            </div>
            {formData.audio_file && (
              <button
                type="button"
                onClick={() => setFormData(prev => ({ ...prev, audio_file: null }))}
                className="mt-2 text-red-400 hover:text-red-300 text-sm flex items-center space-x-1"
              >
                <XMarkIcon className="w-4 h-4" />
                <span>Remove file</span>
              </button>
            )}
          </div>

          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-green-500 hover:bg-green-400 text-black font-bold py-3 rounded-lg transition-colors disabled:opacity-50"
            >
              {loading ? 'Uploading...' : 'Upload Song'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/artist/dashboard')}
              className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white font-medium rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
