import { PlayIcon, PauseIcon } from '@heroicons/react/24/solid';
import { usePlayer } from '../../context/PlayerContext';
import { hasAudio, formatDuration } from '../../utils/helpers';

/**
 * Reusable song list component with consistent styling
 * Supports both table and list layouts
 */
export default function SongList({ 
  songs, 
  layout = 'table', // 'table' or 'list'
  showIndex = true,
  showAlbum = true,
  showDate = false,
  dateValue = null,
  onSongClick = null,
  className = ''
}) {
  const { playSong, currentSong, isPlaying, togglePlayPause } = usePlayer();

  const handleSongClick = (song, songList) => {
    if (onSongClick) {
      onSongClick(song, songList);
      return;
    }

    const songHasAudio = hasAudio(song);
    if (!songHasAudio) {
      console.warn('Cannot play song - no valid audio file:', song.title);
      return;
    }

    const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;
    if (isCurrentlyPlaying) {
      togglePlayPause();
    } else {
      playSong(song, songList || songs);
    }
  };

  if (layout === 'table') {
    return (
      <div className={`space-y-1 ${className}`}>
        {songs.map((song, index) => {
          const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;
          const songHasAudio = hasAudio(song);

          return (
            <div
              key={song.id}
              className={`group grid grid-cols-12 gap-4 items-center p-2 rounded-lg transition-colors ${
                songHasAudio ? 'hover:bg-white/10 cursor-pointer' : 'opacity-60 cursor-not-allowed'
              }`}
              onClick={() => songHasAudio && handleSongClick(song, songs)}
            >
              <div className="col-span-1 text-center text-gray-400 group-hover:hidden">
                {showIndex ? index + 1 : ''}
              </div>
              <div className="col-span-1 hidden group-hover:block">
                {songHasAudio && (
                  isCurrentlyPlaying ? (
                    <PauseIcon className="w-5 h-5 text-white mx-auto" />
                  ) : (
                    <PlayIcon className="w-5 h-5 text-white mx-auto" />
                  )
                )}
              </div>
              <div className="col-span-5 flex items-center space-x-3">
                {song.album?.cover_image && (
                  <img
                    src={song.album.cover_image}
                    alt={song.title}
                    className="w-10 h-10 rounded object-cover"
                  />
                )}
                <div className="min-w-0">
                  <p className={`text-sm truncate ${isCurrentlyPlaying ? 'text-green-500' : 'text-white'}`}>
                    {song.title}
                  </p>
                  <p className="text-gray-400 text-xs truncate">
                    {song.user || 'Unknown Artist'}
                  </p>
                </div>
              </div>
              {showAlbum && (
                <div className="col-span-3 text-gray-400 text-sm truncate">
                  {song.album?.title || '-'}
                </div>
              )}
              {showDate && (
                <div className="col-span-2 text-gray-400 text-sm">
                  {dateValue ? new Date(dateValue).toLocaleDateString() : '-'}
                </div>
              )}
              <div className={`text-gray-400 text-sm text-right ${showAlbum && showDate ? 'col-span-1' : showAlbum || showDate ? 'col-span-2' : 'col-span-4'}`}>
                {formatDuration(song.duration)}
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // List layout
  return (
    <div className={`space-y-1 ${className}`}>
      {songs.map((song, index) => {
        const isCurrentlyPlaying = currentSong?.id === song.id && isPlaying;
        const songHasAudio = hasAudio(song);

        return (
          <div
            key={song.id}
            className={`group flex items-center space-x-4 p-2 rounded-lg transition-colors ${
              songHasAudio ? 'hover:bg-white/10 cursor-pointer' : 'opacity-60 cursor-not-allowed'
            }`}
            onClick={() => songHasAudio && handleSongClick(song, songs)}
          >
            {showIndex && (
              <>
                <div className="w-8 text-center text-gray-400 group-hover:hidden">
                  {index + 1}
                </div>
                <div className="w-8 hidden group-hover:block">
                  {songHasAudio && (
                    isCurrentlyPlaying ? (
                      <PauseIcon className="w-5 h-5 text-white" />
                    ) : (
                      <PlayIcon className="w-5 h-5 text-white" />
                    )
                  )}
                </div>
              </>
            )}
            {song.album?.cover_image && (
              <img
                src={song.album.cover_image}
                alt={song.title}
                className="w-10 h-10 rounded object-cover"
              />
            )}
            <div className="flex-1 min-w-0">
              <p className={`text-sm truncate ${isCurrentlyPlaying ? 'text-green-500' : 'text-white'}`}>
                {song.title}
              </p>
              <p className="text-gray-400 text-xs truncate">
                {song.user || 'Unknown Artist'}
              </p>
            </div>
            <div className="text-gray-400 text-xs">
              {formatDuration(song.duration)}
            </div>
          </div>
        );
      })}
    </div>
  );
}
