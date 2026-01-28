import { useState, useEffect } from 'react';
import { songsAPI } from '../services/api';
import SongCard from '../components/SongCard';
import { MusicalNoteIcon } from '@heroicons/react/24/solid';

export default function Trending() {
  const [songs, setSongs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('all');

  useEffect(() => {
    loadTrending();
  }, [timeRange]);

  const loadTrending = async () => {
    setLoading(true);
    try {
      const response = await songsAPI.trending({ limit: 50, time_range: timeRange });
      setSongs(response.data);
    } catch (error) {
      console.error('Failed to load trending:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 pb-32">
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center space-x-2">
          <MusicalNoteIcon className="w-8 h-8 text-green-500" />
          <h1 className="text-4xl font-bold text-white">Trending</h1>
        </div>
        <div className="flex space-x-2">
          {['all', 'week', 'month'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                timeRange === range
                  ? 'bg-green-500 text-white'
                  : 'bg-white/10 text-gray-400 hover:text-white'
              }`}
            >
              {range.charAt(0).toUpperCase() + range.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div className="text-white text-center py-8">Loading...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {songs.map((song) => (
            <SongCard key={song.id} song={song} />
          ))}
        </div>
      )}
    </div>
  );
}
