import { usePlayer } from '../context/PlayerContext';
import {
  PlayIcon,
  PauseIcon,
  ForwardIcon,
  BackwardIcon,
  SpeakerWaveIcon,
  SpeakerXMarkIcon,
} from '@heroicons/react/24/solid';

export default function Player() {
  const {
    currentSong,
    isPlaying,
    currentTime,
    duration,
    volume,
    togglePlayPause,
    playNext,
    playPrevious,
    seek,
    setVolume,
    formatTime,
  } = usePlayer();

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

  return (
    <div className="fixed bottom-0 left-0 right-0 bg-gradient-to-t from-black via-gray-900 to-gray-800 border-t border-gray-700 h-24 z-50">
      <div className="flex items-center justify-between h-full px-6">
        {/* Song Info */}
        <div className="flex items-center space-x-4 flex-1 min-w-0">
          {currentSong.album?.cover_image && (
            <img
              src={currentSong.album.cover_image}
              alt={currentSong.title}
              className="w-14 h-14 rounded object-cover"
            />
          )}
          <div className="min-w-0 flex-1">
            <p className="text-white font-medium truncate">{currentSong.title}</p>
            <p className="text-gray-400 text-sm truncate">
              {currentSong.user || 'Unknown Artist'}
            </p>
          </div>
        </div>

        {/* Player Controls */}
        <div className="flex flex-col items-center flex-1 max-w-2xl">
          <div className="flex items-center space-x-4 mb-2">
            <button
              onClick={playPrevious}
              className="text-white hover:text-green-500 transition-colors"
            >
              <BackwardIcon className="w-6 h-6" />
            </button>
            <button
              onClick={togglePlayPause}
              className="bg-white text-black rounded-full p-2 hover:scale-110 transition-transform"
            >
              {isPlaying ? (
                <PauseIcon className="w-6 h-6" />
              ) : (
                <PlayIcon className="w-6 h-6" />
              )}
            </button>
            <button
              onClick={playNext}
              className="text-white hover:text-green-500 transition-colors"
            >
              <ForwardIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Progress Bar */}
          <div className="flex items-center space-x-2 w-full">
            <span className="text-gray-400 text-xs w-12 text-right">
              {formatTime(currentTime)}
            </span>
            <div
              className="flex-1 h-1 bg-gray-700 rounded-full cursor-pointer group"
              onClick={handleSeek}
            >
              <div
                className="h-full bg-green-500 rounded-full transition-all group-hover:bg-green-400"
                style={{ width: `${(currentTime / duration) * 100}%` }}
              />
            </div>
            <span className="text-gray-400 text-xs w-12">
              {formatTime(duration)}
            </span>
          </div>
        </div>

        {/* Volume Control */}
        <div className="flex items-center space-x-2 flex-1 justify-end">
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
            className="w-24 h-1 bg-gray-700 rounded-lg appearance-none cursor-pointer"
          />
        </div>
      </div>
    </div>
  );
}
