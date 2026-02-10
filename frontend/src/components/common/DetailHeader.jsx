import { PlayIcon, PauseIcon } from '@heroicons/react/24/solid';
import { usePlayer } from '../../context/PlayerContext';
import { getInitials } from '../../utils/helpers';

/**
 * Reusable detail header component for playlists, albums, artists
 */
export default function DetailHeader({
  type, // 'playlist', 'album', 'artist'
  title,
  subtitle,
  coverImage,
  coverIcon: CoverIcon,
  metadata = [], // Array of strings to display
  songs = [],
  onPlayAll,
  showPlayButton = true,
  className = ''
}) {
  const { currentSong, isPlaying } = usePlayer();
  const isCurrentlyPlaying = songs.length > 0 && 
    currentSong && 
    songs.some(s => s.id === currentSong.id) && 
    isPlaying;

  const { playSong } = usePlayer();

  const handlePlay = () => {
    if (onPlayAll) {
      onPlayAll();
    } else if (songs.length > 0) {
      // Default play all behavior
      playSong(songs[0], songs);
    }
  };

  return (
    <div className={`relative pt-8 pb-12 px-4 md:px-8 ${className}`}>
      <div className="flex flex-col md:flex-row items-start md:items-end space-y-4 md:space-y-0 md:space-x-6">
        {/* Cover Image */}
        {coverImage ? (
          <img
            src={coverImage}
            alt={title}
            className="w-32 h-32 md:w-64 md:h-64 rounded-lg shadow-2xl object-cover"
          />
        ) : (
          <div className={`w-32 h-32 md:w-64 md:h-64 rounded-lg shadow-2xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center ${
            type === 'artist' ? 'rounded-full' : ''
          }`}>
            {CoverIcon ? (
              <CoverIcon className="w-16 h-16 md:w-32 md:h-32 text-white" />
            ) : (
              <span className="text-white text-4xl md:text-6xl font-bold">
                {getInitials(title)}
              </span>
            )}
          </div>
        )}

        {/* Info */}
        <div className="flex-1">
          <p className="text-sm text-white mb-2 capitalize">{type}</p>
          <h1 className="text-3xl md:text-6xl font-bold text-white mb-4">{title}</h1>
          {subtitle && (
            <p className="text-gray-400 mb-4">{subtitle}</p>
          )}
          <div className="flex items-center space-x-2 text-sm text-gray-400">
            {metadata.map((item, index) => (
              <span key={index}>
                {index > 0 && <span className="mx-2">•</span>}
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Controls */}
      {showPlayButton && songs.length > 0 && (
        <div className="px-4 md:px-8 mt-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={handlePlay}
              className="bg-green-500 hover:bg-green-400 rounded-full p-4 transition-colors"
              aria-label={isCurrentlyPlaying ? 'Pause' : 'Play'}
            >
              {isCurrentlyPlaying ? (
                <PauseIcon className="w-6 h-6 text-black" />
              ) : (
                <PlayIcon className="w-6 h-6 text-black ml-0.5" />
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
