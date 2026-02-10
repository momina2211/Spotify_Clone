import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { songsAPI, albumsAPI, artistsAPI } from '../services/api';
import { usePlayer } from '../context/PlayerContext';
import { MagnifyingGlassIcon, PlayIcon, PauseIcon } from '@heroicons/react/24/solid';
import { MusicalNoteIcon, UserGroupIcon, RectangleStackIcon } from '@heroicons/react/24/outline';

const categories = [
  { id: 'all', name: 'All', icon: MagnifyingGlassIcon },
  { id: 'songs', name: 'Songs', icon: MusicalNoteIcon },
  { id: 'albums', name: 'Albums', icon: RectangleStackIcon },
  { id: 'artists', name: 'Artists', icon: UserGroupIcon },
];

export default function Search() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState({ songs: [], albums: [], artists: [] });
  const [loading, setLoading] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');
  const navigate = useNavigate();
  const { playSong, currentSong, isPlaying, togglePlayPause } = usePlayer();

  useEffect(() => {
    if (query.trim()) {
      const timeoutId = setTimeout(() => {
        handleSearch();
      }, 300);
      return () => clearTimeout(timeoutId);
    } else {
      setResults({ songs: [], albums: [], artists: [] });
    }
  }, [query, activeCategory]);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      // Map frontend category to backend type
      const typeMap = {
        'all': 'all',
        'songs': 'song',  // Backend expects 'song' not 'songs'
        'albums': 'album',
        'artists': 'artist'
      };
      const backendType = typeMap[activeCategory] || 'all';
      const response = await songsAPI.search({ q: query, type: backendType });
      setResults(response.data || { songs: [], albums: [], artists: [] });
    } catch (error) {
      console.error('Search failed:', error);
      setResults({ songs: [], albums: [], artists: [] });
    } finally {
      setLoading(false);
    }
  };

  const handlePlaySong = (song) => {
    if (currentSong?.id === song.id && isPlaying) {
      togglePlayPause();
    } else {
      playSong(song, results.songs || []);
    }
  };

  return (
    <div className="bg-black min-h-screen pb-32">
      {/* Search Header */}
      <div className="sticky top-0 z-10 bg-black/80 backdrop-blur-lg px-4 md:px-8 py-4 md:py-6">
        <div className="relative mb-6">
          <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-6 h-6 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="What do you want to listen to?"
            className="w-full pl-12 pr-4 py-4 bg-white/10 border border-white/20 rounded-lg text-white text-lg placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-white"
            autoFocus
          />
        </div>

        {/* Categories */}
        <div className="flex space-x-2 overflow-x-auto">
          {categories.map((category) => {
            const Icon = category.icon;
            const isActive = activeCategory === category.id;
            return (
              <button
                key={category.id}
                onClick={() => setActiveCategory(category.id)}
                className={`flex items-center space-x-2 px-4 py-2 rounded-full font-medium whitespace-nowrap transition-colors ${
                  isActive
                    ? 'bg-white text-black'
                    : 'bg-white/10 text-white hover:bg-white/20'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{category.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Results */}
      <div className="px-4 md:px-8">
        {loading && (
          <div className="text-white text-center py-12">Searching...</div>
        )}

        {!loading && query && (
          <>
            {/* Songs */}
            {(activeCategory === 'all' || activeCategory === 'songs') && results.songs && results.songs.length > 0 && (
              <section className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-4">Songs</h2>
                <div className="space-y-1">
                  {results.songs.map((song) => {
                    const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;
                    return (
                      <div
                        key={song.id}
                        className="group flex items-center space-x-4 p-2 rounded-lg hover:bg-white/10 transition-colors cursor-pointer"
                        onClick={() => handlePlaySong(song)}
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
                          <p className={`text-sm truncate ${isCurrentlyPlaying ? 'text-green-500' : 'text-white'}`}>
                            {song.title}
                          </p>
                          <p className="text-gray-400 text-xs truncate">
                            {song.user || 'Unknown Artist'}
                          </p>
                        </div>
                        <div className="text-gray-400 text-xs">
                          {Math.floor(song.duration / 60)}:{(song.duration % 60).toString().padStart(2, '0')}
                        </div>
                        <div className="opacity-0 group-hover:opacity-100">
                          {isCurrentlyPlaying ? (
                            <PauseIcon className="w-5 h-5 text-white" />
                          ) : (
                            <PlayIcon className="w-5 h-5 text-white" />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* Albums */}
            {(activeCategory === 'all' || activeCategory === 'albums') && results.albums && results.albums.length > 0 && (
              <section className="mb-8">
                <h2 className="text-2xl font-bold text-white mb-4">Albums</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                  {results.albums.map((album) => (
                    <div
                      key={album.id}
                      className="group bg-white/5 hover:bg-white/10 rounded-lg p-4 transition-all cursor-pointer"
                      onClick={() => navigate(`/album/${album.id}`)}
                    >
                      <div className="relative mb-3">
                        {album.cover_image ? (
                          <img
                            src={album.cover_image}
                            alt={album.title}
                            className="w-full aspect-square rounded object-cover"
                          />
                        ) : (
                          <div className="w-full aspect-square rounded bg-gradient-to-br from-purple-500 to-blue-500" />
                        )}
                        <div className="absolute bottom-2 right-2 bg-green-500 rounded-full p-3 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg">
                          <PlayIcon className="w-5 h-5 text-black" />
                        </div>
                      </div>
                      <h3 className="text-white font-medium truncate mb-1">{album.title}</h3>
                      <p className="text-gray-400 text-sm truncate">{album.user}</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Artists */}
            {(activeCategory === 'all' || activeCategory === 'artists') && results.artists && results.artists.length > 0 && (
              <section>
                <h2 className="text-2xl font-bold text-white mb-4">Artists</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                  {results.artists.map((artist) => (
                    <div
                      key={artist.id}
                      className="group bg-white/5 hover:bg-white/10 rounded-lg p-4 transition-all cursor-pointer text-center"
                      onClick={() => navigate(`/artist/${artist.id}`)}
                    >
                      <div className="w-full aspect-square rounded-full bg-gradient-to-br from-purple-500 to-blue-500 mb-3 mx-auto flex items-center justify-center">
                        <UserGroupIcon className="w-16 h-16 text-white" />
                      </div>
                      <h3 className="text-white font-medium truncate">{artist.username}</h3>
                      <p className="text-gray-400 text-sm">Artist</p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* No Results */}
            {Object.values(results).every(arr => !arr || arr.length === 0) && (
              <div className="text-center py-12">
                <p className="text-gray-400 text-lg">No results found for "{query}"</p>
              </div>
            )}
          </>
        )}

        {/* Browse Categories (when no search) */}
        {!query && (
          <div>
            <h2 className="text-2xl font-bold text-white mb-6">Browse All</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {['Pop', 'Rock', 'Hip-Hop', 'Jazz', 'Classical', 'Electronic', 'Country', 'R&B'].map((genre) => (
                <div
                  key={genre}
                  className="group bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg p-6 cursor-pointer hover:scale-105 transition-transform"
                  onClick={() => setQuery(genre)}
                >
                  <h3 className="text-white font-bold text-xl">{genre}</h3>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
