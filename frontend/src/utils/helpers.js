/**
 * Utility functions for common operations
 */

/**
 * Check if a song has a valid audio file
 * @param {Object} song - Song object
 * @returns {boolean} - True if song has valid audio file
 */
export const hasAudio = (song) => {
  if (!song || !song.audio_file) return false;
  if (typeof song.audio_file !== 'string') return false;
  const trimmed = song.audio_file.trim();
  return trimmed !== '' && trimmed !== 'null' && trimmed !== 'undefined';
};

/**
 * Format duration in seconds to MM:SS format
 * @param {number} duration - Duration in seconds
 * @returns {string} - Formatted duration string
 */
export const formatDuration = (duration) => {
  if (!duration || isNaN(duration)) return '0:00';
  const minutes = Math.floor(duration / 60);
  const seconds = Math.floor(duration % 60);
  return `${minutes}:${seconds.toString().padStart(2, '0')}`;
};

/**
 * Format date to readable string
 * @param {string|Date} date - Date string or Date object
 * @param {string} format - Format type: 'short' (MM/DD/YYYY), 'long' (Month DD, YYYY), 'year' (YYYY)
 * @returns {string} - Formatted date string
 */
export const formatDate = (date, format = 'short') => {
  if (!date) return '';
  const d = new Date(date);
  if (isNaN(d.getTime())) return '';

  switch (format) {
    case 'year':
      return d.getFullYear().toString();
    case 'long':
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
    case 'short':
    default:
      return d.toLocaleDateString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit' });
  }
};

/**
 * Get initials from a string (for avatar fallback)
 * @param {string} text - Text to get initials from
 * @returns {string} - First letter uppercase
 */
export const getInitials = (text) => {
  if (!text || typeof text !== 'string') return '?';
  return text.charAt(0).toUpperCase();
};

/**
 * Truncate text to specified length
 * @param {string} text - Text to truncate
 * @param {number} maxLength - Maximum length
 * @returns {string} - Truncated text with ellipsis
 */
export const truncate = (text, maxLength = 50) => {
  if (!text || typeof text !== 'string') return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};
