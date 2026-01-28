import { useState } from 'react';
import { songsAPI, albumsAPI, artistsAPI } from '../services/api';
import SongCard from '../components/SongCard';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';

export default function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState({ songs: [], albums: [], artists: [] });
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('all');

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await songsAPI.search({ q: query, type: activeTab });
      setResults(response.data);
    } catch (error) {
      console.error('Search failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 pb-32">
      <h1 className="text-4xl font-bold text-white mb-8">Search</h1>

      <form onSubmit={handleSearch} className="mb-8">
        <div className="relative">
          <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-6 h-6 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for songs, albums, or artists..."
            className="w-full pl-12 pr-4 py-4 bg-white/10 border border-white/20 rounded-lg text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
          />
        </div>
      </form>

      {loading && (
        <div className="text-white text-center py-8">Searching...</div>
      )}

      {!loading && query && (
        <>
          <div className="flex space-x-4 mb-6">
            {['all', 'song', 'album', 'artist'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  activeTab === tab
                    ? 'bg-green-500 text-white'
                    : 'bg-white/10 text-gray-400 hover:text-white'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          {(activeTab === 'all' || activeTab === 'song') && results.songs && (
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">Songs</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {results.songs.map((song) => (
                  <SongCard key={song.id} song={song} />
                ))}
              </div>
            </section>
          )}

          {(activeTab === 'all' || activeTab === 'album') && results.albums && (
            <section className="mb-8">
              <h2 className="text-2xl font-bold text-white mb-4">Albums</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {results.albums.map((album) => (
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
                ))}
              </div>
            </section>
          )}

          {(activeTab === 'all' || activeTab === 'artist') && results.artists && (
            <section>
              <h2 className="text-2xl font-bold text-white mb-4">Artists</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {results.artists.map((artist) => (
                  <div
                    key={artist.id}
                    className="bg-white/5 hover:bg-white/10 rounded-lg p-4 cursor-pointer transition-all text-center"
                  >
                    <div className="w-full aspect-square rounded-full bg-gradient-to-br from-purple-500 to-blue-500 mb-2 mx-auto" />
                    <h3 className="text-white font-medium truncate">{artist.username}</h3>
                    <p className="text-gray-400 text-sm">{artist.song_count} songs</p>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
