import { useState, useEffect } from 'react';
import { songsAPI } from '../services/api';
import SongCard from '../components/SongCard';
import { MusicalNoteIcon } from '@heroicons/react/24/outline';

export default function Home() {
  const [trending, setTrending] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [random, setRandom] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [trendingRes, recommendationsRes, randomRes] = await Promise.all([
        songsAPI.trending({ limit: 10 }),
        songsAPI.recommendations({ limit: 10 }),
        songsAPI.random({ limit: 10 }),
      ]);
      setTrending(trendingRes.data);
      setRecommendations(recommendationsRes.data);
      setRandom(randomRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
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
      <h1 className="text-4xl font-bold text-white mb-8">Welcome Back</h1>

      <section className="mb-12">
        <div className="flex items-center space-x-2 mb-6">
          <MusicalNoteIcon className="w-6 h-6 text-green-500" />
          <h2 className="text-2xl font-bold text-white">Trending Now</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {trending.map((song) => (
            <SongCard key={song.id} song={song} />
          ))}
        </div>
      </section>

      <section className="mb-12">
        <h2 className="text-2xl font-bold text-white mb-6">Recommended for You</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recommendations.map((song) => (
            <SongCard key={song.id} song={song} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="text-2xl font-bold text-white mb-6">Discover</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {random.map((song) => (
            <SongCard key={song.id} song={song} />
          ))}
        </div>
      </section>
    </div>
  );
}
