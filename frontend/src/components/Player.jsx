import { useState, useEffect, useRef } from 'react';
import { usePlayer } from '../context/PlayerContext';
import {
  PlayIcon,
  PauseIcon,
  ForwardIcon,
  BackwardIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
  ArrowsRightLeftIcon,
  ArrowPathIcon,
  QueueListIcon,
  XMarkIcon,
  AdjustmentsHorizontalIcon,
  HeartIcon,
} from '@heroicons/react/24/solid';
import { ArrowsRightLeftIcon as ArrowsRightLeftIconOutline } from '@heroicons/react/24/outline';
import { HeartIcon as HeartOutlineIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../context/AuthContext';
import { songsAPI } from '../services/api';

export default function Player() {
  const {
    currentSong,
    isPlaying,
    currentTime,
    duration,
    volume,
    queue,
    currentIndex,
    shuffle,
    repeat,
    showQueue,
    togglePlayPause,
    playNext,
    playPrevious,
    seek,
    setVolume,
    formatTime,
    toggleShuffle,
    toggleRepeat,
    setShowQueue,
    audioQuality,
    setAudioQuality,
    equalizer,
    updateEqualizer,
    resetEqualizer,
    showEqualizer,
    setShowEqualizer,
  } = usePlayer();
  const [showQualityMenu, setShowQualityMenu] = useState(false);
  const qualityMenuRef = useRef(null);
  const equalizerMenuRef = useRef(null);
  const { isArtist } = useAuth();
  const [isFavorite, setIsFavorite] = useState(false);
  const [favoriteLoading, setFavoriteLoading] = useState(false);

  // Check if current song is favorited when song changes
  useEffect(() => {
    if (currentSong && !isArtist) {
      checkFavoriteStatus();
    } else {
      setIsFavorite(false);
    }
  }, [currentSong?.id, isArtist]);

  // Close quality menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (qualityMenuRef.current && !qualityMenuRef.current.contains(event.target)) {
        setShowQualityMenu(false);
      }
      if (equalizerMenuRef.current && !equalizerMenuRef.current.contains(event.target)) {
        setShowEqualizer(false);
      }
    };

    if (showQualityMenu || showEqualizer) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showQualityMenu, showEqualizer]);

  const checkFavoriteStatus = async () => {
    if (!currentSong) return;
    try {
      const response = await songsAPI.favorites();
      const favoriteSongs = response.data || [];
      const isFavorited = favoriteSongs.some(song => song.id === currentSong.id);
      setIsFavorite(isFavorited);
    } catch (error) {
      console.error('Failed to check favorite status:', error);
    }
  };

  const handleFavorite = async (e) => {
    e.stopPropagation();
    if (favoriteLoading || !currentSong || isArtist) return;

    // Optimistic update - immediately update UI
    const previousState = isFavorite;
    setIsFavorite(!isFavorite);
    setFavoriteLoading(true);

    try {
      if (previousState) {
        await songsAPI.removeFavorite(currentSong.id);
      } else {
        await songsAPI.addFavorite(currentSong.id);
      }
      // Refresh playlists in sidebar if needed
      if (window.refreshPlaylists) {
        window.refreshPlaylists();
      }
      // Notify that favorites changed (for Liked Songs playlist to refresh)
      window.dispatchEvent(new Event('favoriteChanged'));
    } catch (error) {
      console.error('Failed to update favorite:', error);
      // Revert on error
      setIsFavorite(previousState);
      if (window.showToast) {
        window.showToast('Failed to update favorite. Please try again.', 'error');
      }
    } finally {
      setFavoriteLoading(false);
    }
  };

  if (!currentSong) return null;

  const handleSeek = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = x / rect.width;
    seek(percentage * duration);
  };

  const handleVolumeChange = (e) => {
    setVolume(parseFloat(e.target.value));
  };

  const getRepeatIcon = () => {
    if (repeat === 'one') {
      return <span className="text-xs">1</span>;
    }
    return <ArrowPathIcon className="w-5 h-5" />;
  };

  const getRepeatColor = () => {
    return repeat !== 'off' ? 'text-green-500' : 'text-gray-400';
  };

  return (
    <>
      {/* Queue Sidebar */}
      {showQueue && (
        <div className="fixed right-0 top-0 bottom-24 w-96 bg-black border-l border-gray-800 z-40 overflow-y-auto">
          <div className="p-6 border-b border-gray-800 flex items-center justify-between">
            <h2 className="text-white font-bold text-lg">Queue</h2>
            <button
              onClick={() => setShowQueue(false)}
              className="text-gray-400 hover:text-white"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>
          <div className="p-4">
            <div className="text-gray-400 text-sm mb-4">Now Playing</div>
            {currentSong && (
              <div className="bg-white/10 rounded-lg p-3 mb-4">
                <div className="flex items-center space-x-3">
                  {currentSong.album?.cover_image && (
                    <img
                      src={currentSong.album.cover_image}
                      alt={currentSong.title}
                      className="w-12 h-12 rounded object-cover"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-white font-medium truncate">{currentSong.title}</p>
                    <p className="text-gray-400 text-sm truncate">
                      {currentSong.user || 'Unknown Artist'}
                    </p>
                  </div>
                </div>
              </div>
            )}
            <div className="text-gray-400 text-sm mb-4">Next in Queue</div>
            <div className="space-y-2">
              {queue.slice(currentIndex + 1).map((song, idx) => (
                <div
                  key={song.id}
                  className="flex items-center space-x-3 p-2 rounded-lg hover:bg-white/5 cursor-pointer"
                >
                  {song.album?.cover_image ? (
                    <img
                      src={song.album.cover_image}
                      alt={song.title}
                      className="w-10 h-10 rounded object-cover"
                    />
                  ) : (
                    <div className="w-10 h-10 rounded bg-gradient-to-br from-purple-500 to-blue-500" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm truncate">{song.title}</p>
                    <p className="text-gray-400 text-xs truncate">
                      {song.user || 'Unknown Artist'}
                    </p>
                  </div>
                  <span className="text-gray-500 text-xs">
                    {formatTime(song.duration || 0)}
                  </span>
                </div>
              ))}
              {queue.length === currentIndex + 1 && (
                <div className="text-gray-500 text-sm text-center py-4">
                  No more songs in queue
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Main Player */}
      <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-black via-gray-900 to-gray-800 border-t border-gray-700 h-20 md:h-24 z-50">
        <div className="flex items-center justify-between h-full px-3 md:px-6">
          {/* Song Info */}
          <div className="flex items-center space-x-2 md:space-x-4 flex-1 min-w-0 max-w-[30%] md:max-w-[30%]">
            {currentSong.album?.cover_image && (
              <img
                src={currentSong.album.cover_image}
                alt={currentSong.title}
                className="w-12 h-12 md:w-14 md:h-14 rounded object-cover flex-shrink-0"
              />
            )}
            <div className="min-w-0 flex-1 hidden sm:block">
              <p className="text-white font-medium text-xs md:text-sm truncate hover:underline cursor-pointer">
                {currentSong.title}
              </p>
              <p className="text-gray-400 text-xs truncate hover:underline cursor-pointer">
                {currentSong.user || 'Unknown Artist'}
              </p>
            </div>
            {!isArtist && (
              <button
                onClick={handleFavorite}
                disabled={favoriteLoading}
                className={`hidden md:block transition-colors ${
                  isFavorite
                    ? 'text-white hover:text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
                title={isFavorite ? 'Remove from Liked Songs' : 'Add to Liked Songs'}
              >
                {isFavorite ? (
                  <HeartIcon className="w-5 h-5 text-white" />
                ) : (
                  <HeartOutlineIcon className="w-5 h-5" />
                )}
              </button>
            )}
          </div>

          {/* Player Controls */}
          <div className="flex flex-col items-center flex-1 max-w-2xl px-2">
            <div className="flex items-center space-x-2 md:space-x-4 mb-1 md:mb-2">
              <button
                onClick={toggleShuffle}
                className={`hidden sm:block transition-colors ${shuffle ? 'text-green-500' : 'text-gray-400 hover:text-white'}`}
                title="Shuffle"
              >
                <ArrowsRightLeftIcon className="w-4 h-4 md:w-5 md:h-5" />
              </button>
              <button
                onClick={playPrevious}
                className="text-white hover:scale-110 transition-transform"
                title="Previous"
              >
                <BackwardIcon className="w-5 h-5 md:w-6 md:h-6" />
              </button>
              <button
                onClick={togglePlayPause}
                className="bg-white text-black rounded-full p-1.5 md:p-2 hover:scale-110 transition-transform"
                title={isPlaying ? 'Pause' : 'Play'}
              >
                {isPlaying ? (
                  <PauseIcon className="w-5 h-5 md:w-6 md:h-6" />
                ) : (
                  <PlayIcon className="w-5 h-5 md:w-6 md:h-6 ml-0.5" />
                )}
              </button>
              <button
                onClick={playNext}
                className="text-white hover:scale-110 transition-transform"
                title="Next"
              >
                <ForwardIcon className="w-5 h-5 md:w-6 md:h-6" />
              </button>
              <button
                onClick={toggleRepeat}
                className={`hidden sm:block transition-colors ${getRepeatColor()} hover:text-white`}
                title={`Repeat: ${repeat}`}
              >
                <div className="w-4 h-4 md:w-5 md:h-5 flex items-center justify-center">
                  {getRepeatIcon()}
                </div>
              </button>
            </div>

            {/* Progress Bar */}
            <div className="flex items-center space-x-1 md:space-x-2 w-full">
              <span className="text-gray-400 text-xs w-10 md:w-12 text-right hidden sm:block">
                {formatTime(currentTime)}
              </span>
              <div
                className="flex-1 h-1 bg-gray-700 rounded-full cursor-pointer group relative"
                onClick={handleSeek}
              >
                <div
                  className="h-full bg-white rounded-full transition-all group-hover:bg-green-500 group-hover:h-1.5"
                  style={{ width: `${duration > 0 ? (currentTime / duration) * 100 : 0}%` }}
                />
              </div>
              <span className="text-gray-400 text-xs w-10 md:w-12 hidden sm:block">
                {formatTime(duration)}
              </span>
            </div>
          </div>

          {/* Volume Control & Queue */}
          <div className="flex items-center space-x-2 flex-1 justify-end max-w-[30%]">
            <button
              onClick={() => setShowQueue(!showQueue)}
              className={`text-gray-400 hover:text-white transition-colors ${showQueue ? 'text-white' : ''}`}
              title="Queue"
            >
              <QueueListIcon className="w-5 h-5" />
            </button>
            
            {/* Equalizer */}
            <div className="relative" ref={equalizerMenuRef}>
              <button
                onClick={() => {
                  setShowEqualizer(!showEqualizer);
                  setShowQualityMenu(false);
                }}
                className={`text-gray-400 hover:text-white transition-colors ${
                  (equalizer.bass !== 0 || equalizer.mid !== 0 || equalizer.treble !== 0) ? 'text-green-500' : ''
                }`}
                title="Equalizer"
              >
                <AdjustmentsHorizontalIcon className="w-5 h-5" />
              </button>
              {showEqualizer && (
                <div className="absolute bottom-full right-0 mb-2 w-64 bg-gray-800 rounded-lg shadow-lg border border-gray-700 z-50">
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-white font-semibold text-sm">Equalizer</h3>
                      <button
                        onClick={resetEqualizer}
                        className="text-gray-400 hover:text-white text-xs"
                      >
                        Reset
                      </button>
                    </div>
                    <div className="space-y-4">
                      {/* Bass */}
                      <div className="flex items-center space-x-3">
                        <span className="text-gray-400 text-xs w-16">Bass</span>
                        <input
                          type="range"
                          min="-12"
                          max="12"
                          step="1"
                          value={equalizer.bass}
                          onChange={(e) => updateEqualizer('bass', parseInt(e.target.value))}
                          className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500"
                        />
                        <span className="text-white text-xs w-8 text-right">
                          {equalizer.bass > 0 ? '+' : ''}{equalizer.bass}dB
                        </span>
                      </div>
                      {/* Mid */}
                      <div className="flex items-center space-x-3">
                        <span className="text-gray-400 text-xs w-16">Mid</span>
                        <input
                          type="range"
                          min="-12"
                          max="12"
                          step="1"
                          value={equalizer.mid}
                          onChange={(e) => updateEqualizer('mid', parseInt(e.target.value))}
                          className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500"
                        />
                        <span className="text-white text-xs w-8 text-right">
                          {equalizer.mid > 0 ? '+' : ''}{equalizer.mid}dB
                        </span>
                      </div>
                      {/* Treble */}
                      <div className="flex items-center space-x-3">
                        <span className="text-gray-400 text-xs w-16">Treble</span>
                        <input
                          type="range"
                          min="-12"
                          max="12"
                          step="1"
                          value={equalizer.treble}
                          onChange={(e) => updateEqualizer('treble', parseInt(e.target.value))}
                          className="flex-1 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer accent-green-500"
                        />
                        <span className="text-white text-xs w-8 text-right">
                          {equalizer.treble > 0 ? '+' : ''}{equalizer.treble}dB
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            {/* Audio Quality Selector */}
            <div className="relative" ref={qualityMenuRef}>
              <button
                onClick={() => {
                  setShowQualityMenu(!showQualityMenu);
                  setShowEqualizer(false);
                }}
                className={`text-gray-400 hover:text-white transition-colors ${audioQuality === 'high' ? 'text-green-500' : ''}`}
                title="Audio Quality"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </button>
              {showQualityMenu && (
                <div className="absolute bottom-full right-0 mb-2 w-48 bg-gray-800 rounded-lg shadow-lg border border-gray-700 z-50">
                  <div className="p-2">
                    <div className="text-gray-400 text-xs px-3 py-2 mb-1">Audio Quality</div>
                    {['high', 'low'].map((quality) => (
                      <button
                        key={quality}
                        onClick={() => {
                          setAudioQuality(quality);
                          setShowQualityMenu(false);
                        }}
                        className={`w-full text-left px-3 py-2 rounded hover:bg-white/10 transition-colors ${
                          audioQuality === quality ? 'text-green-500' : 'text-white'
                        }`}
                      >
                        {quality === 'high' ? 'High (320 kbps)' : 'Low (96 kbps)'}
                        {audioQuality === quality && (
                          <span className="ml-2 text-green-500">✓</span>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            {volume === 0 ? (
              <SpeakerXMarkIcon className="w-5 h-5 text-white" />
            ) : (
              <SpeakerWaveIcon className="w-5 h-5 text-white" />
            )}
            <input
              type="range"
              min="0"
              max="1"
              step="0.01"
              value={volume}
              onChange={handleVolumeChange}
              className="w-24 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer hover:bg-green-500"
            />
          </div>
        </div>
      </div>
    </>
  );
}
