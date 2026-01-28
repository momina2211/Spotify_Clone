import { useState, useEffect } from 'react';
import { songsAPI } from '../services/api';
import SongCard from '../components/SongCard';
import { ClockIcon } from '@heroicons/react/24/outline';

export default function RecentlyPlayed() {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRecentlyPlayed();
  }, []);

  const loadRecentlyPlayed = async () => {
    try {
      const response = await songsAPI.recentlyPlayed({ limit: 50 });
      setSongs(response.data);
    } catch (error) {
      console.error('Failed to load recently played:', error);
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
        <ClockIcon className="w-8 h-8 text-green-500" />
        <h1 className="text-4xl font-bold text-white">Recently Played</h1>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {songs.length > 0 ? (
          songs.map((song) => (
            <SongCard key={song.id} song={song} />
          ))
        ) : (
          <div className="text-gray-400 col-span-full text-center py-8">
            No recently played songs yet
          </div>
        )}
      </div>
    </div>
  );
}
