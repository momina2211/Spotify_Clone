import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { songsAPI } from '../services/api';
import { MusicalNoteIcon, PencilIcon, TrashIcon, EyeIcon, PlayIcon } from '@heroicons/react/24/outline';

export default function ManageSongs() {
  const { isArtist } = useAuth();
  const navigate = useNavigate();
  const { playSong, currentSong, isPlaying } = usePlayer();
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (!isArtist) {
      navigate('/');
      return;
    }
    loadSongs();
  }, [isArtist, navigate]);

  const loadSongs = async () => {
    try {
      const response = await songsAPI.getAll({ artist: 'me' });
      setSongs(response.data);
    } catch (error) {
      console.error('Failed to load songs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteSong = async (songId) => {
    if (!window.confirm('Are you sure you want to delete this song? This action cannot be undone.')) return;

    try {
      await songsAPI.delete(songId);
      loadSongs();
    } catch (error) {
      console.error('Failed to delete song:', error);
      alert('Failed to delete song');
    }
  };

  const filteredSongs = songs.filter(song =>
    song.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (song.album?.title && song.album.title.toLowerCase().includes(searchTerm.toLowerCase()))
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
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-4xl font-bold text-white">Manage Songs</h1>
          <button
            onClick={() => navigate('/artist/upload')}
            className="bg-green-500 hover:bg-green-400 text-black font-bold py-3 px-6 rounded-lg transition-colors flex items-center space-x-2"
          >
            <MusicalNoteIcon className="w-5 h-5" />
            <span>Upload New Song</span>
          </button>
        </div>

        {/* Search Bar */}
        <div className="mb-6">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search songs by title or album..."
            className="w-full max-w-md px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>

        {filteredSongs.length === 0 ? (
          <div className="text-center py-12">
            <MusicalNoteIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 mb-4">
              {searchTerm ? 'No songs found matching your search' : 'No songs uploaded yet'}
            </p>
            {!searchTerm && (
              <button
                onClick={() => navigate('/artist/upload')}
                className="px-6 py-2 bg-green-500 text-black rounded-full font-medium hover:scale-105 transition-transform"
              >
                Upload Your First Song
              </button>
            )}
          </div>
        ) : (
          <div className="bg-white/5 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="border-b border-white/10">
                <tr>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">#</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">Title</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">Album</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">Genres</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">Plays</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">Likes</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">Audio File</th>
                  <th className="text-left p-4 text-gray-400 text-sm font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredSongs.map((song, index) => {
                  const hasAudio = !!song.audio_file && typeof song.audio_file === 'string' && song.audio_file.trim() !== '';
                  const isCurrentSong = currentSong?.id === song.id && isPlaying;
                  
                  return (
                    <tr key={song.id} className="border-b border-white/5 hover:bg-white/5 group">
                      <td className="p-4">
                        <div className="flex items-center space-x-3">
                          <span className="text-gray-400 w-4">{index + 1}</span>
                          {hasAudio && (
                            <button
                              onClick={() => playSong(song, filteredSongs)}
                              className="opacity-0 group-hover:opacity-100 transition-opacity text-white hover:text-green-500"
                              title="Play song"
                            >
                              <PlayIcon className="w-5 h-5" />
                            </button>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <p className={`font-medium ${isCurrentSong ? 'text-green-500' : 'text-white'}`}>
                          {song.title}
                        </p>
                        <p className="text-gray-400 text-sm">
                          {new Date(song.release_date).toLocaleDateString()}
                        </p>
                      </td>
                      <td className="p-4 text-gray-400">
                        {song.album ? song.album.title : 'No album'}
                      </td>
                      <td className="p-4">
                        <div className="flex flex-wrap gap-1">
                          {song.genres && song.genres.length > 0 ? (
                            song.genres.map((genre) => (
                              <span
                                key={genre.id}
                                className="text-xs px-2 py-1 rounded-full bg-green-500/20 text-green-300"
                              >
                                {genre.title}
                              </span>
                            ))
                          ) : (
                            <span className="text-gray-500 text-sm">No genres</span>
                          )}
                        </div>
                      </td>
                      <td className="p-4 text-gray-400">{song.play_count || 0}</td>
                      <td className="p-4 text-gray-400">{song.likes || 0}</td>
                      <td className="p-4">
                        {hasAudio ? (
                          <span className="text-green-400 text-sm">✓ Available</span>
                        ) : (
                          <span className="text-yellow-400 text-sm">⚠ Missing</span>
                        )}
                      </td>
                      <td className="p-4">
                        <div className="flex items-center space-x-3">
                          {hasAudio && (
                            <button
                              onClick={() => playSong(song, filteredSongs)}
                              className={`${isCurrentSong ? 'text-green-500' : 'text-gray-400'} hover:text-green-400`}
                              title="Play song"
                            >
                              <PlayIcon className="w-5 h-5" />
                            </button>
                          )}
                          <button
                            onClick={() => navigate(`/song/${song.id}`)}
                            className="text-green-500 hover:text-green-400"
                            title="View song"
                          >
                            <EyeIcon className="w-5 h-5" />
                          </button>
                          <button
                            onClick={() => handleDeleteSong(song.id)}
                            className="text-red-400 hover:text-red-300"
                            title="Delete song"
                          >
                            <TrashIcon className="w-5 h-5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Summary Stats */}
        {songs.length > 0 && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Total Songs</p>
              <p className="text-2xl font-bold text-white">{songs.length}</p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Total Plays</p>
              <p className="text-2xl font-bold text-white">
                {songs.reduce((sum, song) => sum + (song.play_count || 0), 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Total Likes</p>
              <p className="text-2xl font-bold text-white">
                {songs.reduce((sum, song) => sum + (song.likes || 0), 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Songs with Audio</p>
              <p className="text-2xl font-bold text-white">
                {songs.filter(song => song.audio_file).length} / {songs.length}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
