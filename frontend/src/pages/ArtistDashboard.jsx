import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { usePlayer } from '../context/PlayerContext';
import { songsAPI, albumsAPI, artistsAPI } from '../services/api';
import { MusicalNoteIcon, RectangleStackIcon, EyeIcon, HeartIcon, PlayIcon } from '@heroicons/react/24/outline';

export default function ArtistDashboard() {
  const { isArtist } = useAuth();
  const navigate = useNavigate();
  const { playSong, currentSong, isPlaying } = usePlayer();
  const [stats, setStats] = useState({
    totalSongs: 0,
    totalAlbums: 0,
    totalPlays: 0,
    totalLikes: 0,
    followers: 0,
  });
  const [recentSongs, setRecentSongs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!isArtist) {
      navigate('/');
      return;
    }
    loadDashboardData();
  }, [isArtist, navigate]);

  const loadDashboardData = async () => {
    try {
      // Get user's songs
      const songsRes = await songsAPI.getAll({ artist: 'me' });
      const songs = songsRes.data;
      
      // Get user's albums
      const albumsRes = await albumsAPI.getAll({ artist: 'me' });
      const albums = albumsRes.data;
      
      // Get followers
      const followersRes = await artistsAPI.followers();
      const followers = followersRes.data || [];
      
      // Calculate stats
      const totalPlays = songs.reduce((sum, song) => sum + (song.play_count || 0), 0);
      const totalLikes = songs.reduce((sum, song) => sum + (song.likes || 0), 0);
      
      setStats({
        totalSongs: songs.length,
        totalAlbums: albums.length,
        totalPlays,
        totalLikes,
        followers: followers.length,
      });
      
      setRecentSongs(songs.slice(0, 5));
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
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
        <h1 className="text-4xl font-bold text-white mb-8">Artist Dashboard</h1>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
          <div className="bg-white/5 rounded-lg p-6 hover:bg-white/10 transition-colors">
            <div className="flex items-center space-x-3 mb-2">
              <MusicalNoteIcon className="w-8 h-8 text-green-500" />
              <h3 className="text-gray-400 text-sm">Total Songs</h3>
            </div>
            <p className="text-3xl font-bold text-white">{stats.totalSongs}</p>
          </div>

          <div className="bg-white/5 rounded-lg p-6 hover:bg-white/10 transition-colors">
            <div className="flex items-center space-x-3 mb-2">
              <RectangleStackIcon className="w-8 h-8 text-green-500" />
              <h3 className="text-gray-400 text-sm">Total Albums</h3>
            </div>
            <p className="text-3xl font-bold text-white">{stats.totalAlbums}</p>
          </div>

          <div className="bg-white/5 rounded-lg p-6 hover:bg-white/10 transition-colors">
            <div className="flex items-center space-x-3 mb-2">
              <EyeIcon className="w-8 h-8 text-green-500" />
              <h3 className="text-gray-400 text-sm">Total Plays</h3>
            </div>
            <p className="text-3xl font-bold text-white">{stats.totalPlays.toLocaleString()}</p>
          </div>

          <div className="bg-white/5 rounded-lg p-6 hover:bg-white/10 transition-colors">
            <div className="flex items-center space-x-3 mb-2">
              <HeartIcon className="w-8 h-8 text-green-500" />
              <h3 className="text-gray-400 text-sm">Total Likes</h3>
            </div>
            <p className="text-3xl font-bold text-white">{stats.totalLikes.toLocaleString()}</p>
          </div>

          <div className="bg-white/5 rounded-lg p-6 hover:bg-white/10 transition-colors">
            <div className="flex items-center space-x-3 mb-2">
              <svg className="w-8 h-8 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z" />
              </svg>
              <h3 className="text-gray-400 text-sm">Followers</h3>
            </div>
            <p className="text-3xl font-bold text-white">{stats.followers}</p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-white mb-4">Quick Actions</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button
              onClick={() => navigate('/artist/upload')}
              className="bg-green-500 hover:bg-green-400 text-black font-bold py-4 px-6 rounded-lg transition-colors text-left"
            >
              <MusicalNoteIcon className="w-8 h-8 mb-2" />
              <h3 className="text-xl font-bold">Upload New Song</h3>
              <p className="text-sm opacity-80">Share your music with the world</p>
            </button>

            <button
              onClick={() => navigate('/artist/albums')}
              className="bg-white/10 hover:bg-white/20 text-white font-bold py-4 px-6 rounded-lg transition-colors text-left"
            >
              <RectangleStackIcon className="w-8 h-8 mb-2" />
              <h3 className="text-xl font-bold">Manage Albums</h3>
              <p className="text-sm opacity-80">Create and organize your albums</p>
            </button>

            <button
              onClick={() => navigate('/artist/genres')}
              className="bg-white/10 hover:bg-white/20 text-white font-bold py-4 px-6 rounded-lg transition-colors text-left"
            >
              <svg className="w-8 h-8 mb-2" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5a.997.997 0 01.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clipRule="evenodd" />
              </svg>
              <h3 className="text-xl font-bold">Manage Genres</h3>
              <p className="text-sm opacity-80">Organize your music by genre</p>
            </button>
          </div>
        </div>

        {/* Recent Songs */}
        {recentSongs.length > 0 && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-4">Your Recent Songs</h2>
            <div className="bg-white/5 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="border-b border-white/10">
                  <tr>
                    <th className="text-left p-4 text-gray-400 text-sm font-medium">#</th>
                    <th className="text-left p-4 text-gray-400 text-sm font-medium">Title</th>
                    <th className="text-left p-4 text-gray-400 text-sm font-medium">Plays</th>
                    <th className="text-left p-4 text-gray-400 text-sm font-medium">Likes</th>
                    <th className="text-left p-4 text-gray-400 text-sm font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {recentSongs.map((song, index) => {
                    const hasAudio = !!song.audio_file && typeof song.audio_file === 'string' && song.audio_file.trim() !== '';
                    const isCurrentSong = currentSong?.id === song.id && isPlaying;
                    
                    return (
                      <tr key={song.id} className="border-b border-white/5 hover:bg-white/5 group">
                        <td className="p-4">
                          <div className="flex items-center space-x-3">
                            <span className="text-gray-400 w-4">{index + 1}</span>
                            {hasAudio && (
                              <button
                                onClick={() => playSong(song, recentSongs)}
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
                            {song.genres && song.genres.length > 0 
                              ? song.genres.map(g => g.title).join(', ')
                              : 'No genre'}
                          </p>
                        </td>
                        <td className="p-4 text-gray-400">{song.play_count || 0}</td>
                        <td className="p-4 text-gray-400">{song.likes || 0}</td>
                        <td className="p-4">
                          <button
                            onClick={() => navigate(`/song/${song.id}`)}
                            className="text-green-500 hover:text-green-400 text-sm"
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
