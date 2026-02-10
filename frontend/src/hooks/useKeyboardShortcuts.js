import { useEffect } from 'react';
import { usePlayer } from '../context/PlayerContext';

export function useKeyboardShortcuts() {
  const {
    togglePlayPause,
    playNext,
    playPrevious,
    setVolume,
    volume,
  } = usePlayer();

  useEffect(() => {
    const handleKeyPress = (e) => {
      // Ignore if typing in input
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        return;
      }

      // Space: Play/Pause
      if (e.code === 'Space') {
        e.preventDefault();
        togglePlayPause();
      }
      // Arrow Right: Next
      else if (e.code === 'ArrowRight' && e.ctrlKey) {
        e.preventDefault();
        playNext();
      }
      // Arrow Left: Previous
      else if (e.code === 'ArrowLeft' && e.ctrlKey) {
        e.preventDefault();
        playPrevious();
      }
      // Arrow Up: Volume Up
      else if (e.code === 'ArrowUp' && e.ctrlKey) {
        e.preventDefault();
        setVolume(Math.min(1, volume + 0.1));
      }
      // Arrow Down: Volume Down
      else if (e.code === 'ArrowDown' && e.ctrlKey) {
        e.preventDefault();
        setVolume(Math.max(0, volume - 0.1));
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [togglePlayPause, playNext, playPrevious, setVolume, volume]);
}
