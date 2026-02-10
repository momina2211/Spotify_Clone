import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { songsAPI } from '../services/api';
import { usePlayer } from '../context/PlayerContext';
import { PlayIcon, PauseIcon, HeartIcon } from '@heroicons/react/24/solid';
import { HeartIcon as HeartOutlineIcon } from '@heroicons/react/24/outline';

function SongRow({ song, index, isPlaying, currentSong, onPlay, onPause }) {
  const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;
  // More robust check for audio file
  const hasAudio = song.audio_file && 
                  typeof song.audio_file === 'string' && 
                  song.audio_file.trim() !== '' &&
                  song.audio_file !== 'null' &&
                  song.audio_file !== 'undefined';
  
  return (
    <div
      className={`group flex items-center space-x-4 p-2 rounded-lg transition-colors ${
        hasAudio 
          ? 'hover:bg-white/10 cursor-pointer' 
          : 'opacity-60 cursor-not-allowed'
      }`}
      onClick={hasAudio ? (() => isCurrentlyPlaying ? onPause() : onPlay()) : undefined}
    >
      <div className="w-8 text-center text-gray-400 group-hover:hidden">
        {index + 1}
      </div>
      <div className="w-8 hidden group-hover:block">
        {isCurrentlyPlaying ? (
          <PauseIcon className="w-5 h-5 text-white" />
        ) : (
          <PlayIcon className="w-5 h-5 text-white" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className={`text-sm truncate ${isCurrentlyPlaying ? 'text-green-500' : 'text-white'}`}>
            {song.title}
          </p>
          {!hasAudio && (
            <span className="text-xs text-yellow-400 bg-yellow-500/20 px-1.5 py-0.5 rounded" title="No audio file available">
              Metadata Only
            </span>
          )}
        </div>
        <p className="text-gray-400 text-xs truncate">
          {song.user || 'Unknown Artist'}
        </p>
      </div>
      <div className="text-gray-400 text-xs">
        {Math.floor(song.duration / 60)}:{(song.duration % 60).toString().padStart(2, '0')}
      </div>
    </div>
  );
}

function SectionCard({ title, songs, onPlayAll }) {
  const navigate = useNavigate();
  const { playSong, currentSong, isPlaying } = usePlayer();

  if (!songs || songs.length === 0) return null;

  return (
    <section className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-white hover:underline cursor-pointer">{title}</h2>
        <button className="text-gray-400 hover:text-white text-sm font-medium">
          Show all
        </button>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
        {songs.slice(0, 5).map((song) => {
          // More robust check for audio file
          const hasAudio = song.audio_file && 
                          typeof song.audio_file === 'string' && 
                          song.audio_file.trim() !== '' &&
                          song.audio_file !== 'null' &&
                          song.audio_file !== 'undefined';
          return (
          <div
            key={song.id}
            className={`group bg-white/5 rounded-lg p-4 transition-all ${
              hasAudio 
                ? 'hover:bg-white/10 cursor-pointer' 
                : 'opacity-60 cursor-not-allowed'
            }`}
            onClick={hasAudio ? () => playSong(song, songs) : undefined}
          >
            <div className="relative mb-4">
              {song.album?.cover_image ? (
                <img
                  src={song.album.cover_image}
                  alt={song.title}
                  className="w-full aspect-square rounded object-cover"
                />
              ) : (
                <div className="w-full aspect-square rounded bg-gradient-to-br from-purple-500 to-blue-500" />
              )}
              {hasAudio ? (
                <div className="absolute bottom-2 right-2 bg-green-500 rounded-full p-3 opacity-0 group-hover:opacity-100 transition-opacity shadow-lg">
                  {currentSong?.id === song.id && isPlaying ? (
                    <PauseIcon className="w-5 h-5 text-black" />
                  ) : (
                    <PlayIcon className="w-5 h-5 text-black ml-0.5" />
                  )}
                </div>
              ) : (
                <div className="absolute bottom-2 right-2 bg-yellow-500/80 rounded-full p-2 opacity-100">
                  <span className="text-xs text-black font-medium">No Audio</span>
                </div>
              )}
            </div>
            <div className="flex items-center gap-2">
              <h3 className="text-white font-medium truncate mb-1">{song.title}</h3>
              {!hasAudio && (
                <span className="text-xs text-yellow-400 bg-yellow-500/20 px-1.5 py-0.5 rounded">Metadata</span>
              )}
            </div>
            <p className="text-gray-400 text-sm truncate">
              {song.user || 'Unknown Artist'}
            </p>
          </div>
          );
        })}
      </div>
    </section>
  );
}

export default function Home() {
  const [trending, setTrending] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [recentlyPlayed, setRecentlyPlayed] = useState([]);
  const [topMixes, setTopMixes] = useState([]);
  const [loading, setLoading] = useState(true);
  const { playSong, currentSong, isPlaying, togglePlayPause } = usePlayer();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [trendingRes, recommendationsRes, recentRes, randomRes] = await Promise.all([
        songsAPI.trending({ limit: 20 }),
        songsAPI.recommendations({ limit: 20 }),
        songsAPI.recentlyPlayed({ limit: 20 }),
        songsAPI.random({ limit: 20 }),
      ]);
      setTrending(trendingRes.data);
      setRecommendations(recommendationsRes.data);
      setRecentlyPlayed(recentRes.data);
      setTopMixes(randomRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-b from-gray-900 to-black">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  const handlePlayAll = (songs) => {
    if (songs.length > 0) {
      playSong(songs[0], songs);
    }
  };

  return (
    <div className="bg-gradient-to-b from-gray-900 via-black to-black min-h-screen pb-32">
      {/* Hero Section */}
      <div className="relative pt-8 pb-12 px-4 md:px-8">
        <div className="flex flex-col md:flex-row items-start md:items-end space-y-4 md:space-y-0 md:space-x-6">
          {recentlyPlayed[0]?.album?.cover_image && (
            <img
              src={recentlyPlayed[0].album.cover_image}
              alt="Recently played"
              className="w-32 h-32 md:w-64 md:h-64 rounded-lg shadow-2xl object-cover"
            />
          )}
          <div className="flex-1">
            <p className="text-sm text-white mb-2">Good evening</p>
            <h1 className="text-3xl md:text-6xl font-bold text-white mb-6">Made for You</h1>
            <div className="flex flex-wrap gap-2">
              {recentlyPlayed.slice(0, 6).map((song) => (
                <button
                  key={song.id}
                  onClick={() => playSong(song, recentlyPlayed)}
                  className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-full text-white text-sm font-medium transition-colors"
                >
                  {song.title}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Content Sections */}
      <div className="px-4 md:px-8">
        {/* Recently Played Section */}
        {recentlyPlayed.length > 0 && (
          <section className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-4">Recently Played</h2>
            <div className="bg-white/5 rounded-lg p-4">
              {recentlyPlayed.slice(0, 10).map((song, index) => (
                <SongRow
                  key={song.id}
                  song={song}
                  index={index}
                  isPlaying={isPlaying}
                  currentSong={currentSong}
                  onPlay={() => playSong(song, recentlyPlayed)}
                  onPause={togglePlayPause}
                />
              ))}
            </div>
          </section>
        )}

        {/* Made for You */}
        {recommendations.length > 0 && (
          <SectionCard title="Made for You" songs={recommendations} onPlayAll={handlePlayAll} />
        )}

        {/* Trending Now */}
        {trending.length > 0 && (
          <SectionCard title="Trending Now" songs={trending} onPlayAll={handlePlayAll} />
        )}

        {/* Your Top Mixes */}
        {topMixes.length > 0 && (
          <SectionCard title="Your Top Mixes" songs={topMixes} onPlayAll={handlePlayAll} />
        )}

        {/* Jump Back In */}
        {recentlyPlayed.length > 0 && (
          <SectionCard title="Jump Back In" songs={recentlyPlayed} onPlayAll={handlePlayAll} />
        )}
      </div>
    </div>
  );
}
