import { createContext, useContext, useState, useRef, useEffect } from 'react';
import { songsAPI } from '../services/api';
import { useAuth } from './AuthContext';

const PlayerContext = createContext(null);

export const usePlayer = () => {
  const context = useContext(PlayerContext);
  if (!context) {
    throw new Error('usePlayer must be used within PlayerProvider');
  }
  return context;
};

export const PlayerProvider = ({ children }) => {
  const { user } = useAuth();
  const [currentSong, setCurrentSong] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [queue, setQueue] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [shuffle, setShuffle] = useState(false);
  const [repeat, setRepeat] = useState('off'); // 'off', 'all', 'one'
  const [showQueue, setShowQueue] = useState(false);
  
  // Get audio quality from user profile, default to 'high'
  const [audioQuality, setAudioQuality] = useState(
    user?.audio_quality || user?.profile?.audio_quality || 'high'
  );
  
  // Equalizer settings (bass, mid, treble) in dB (-12 to +12)
  const [equalizer, setEqualizer] = useState({
    bass: 0,    // 60 Hz
    mid: 0,     // 1000 Hz
    treble: 0,  // 10000 Hz
  });
  const [showEqualizer, setShowEqualizer] = useState(false);
  
  const audioRef = useRef(null);
  const audioContextRef = useRef(null);
  const sourceRef = useRef(null);
  const gainNodeRef = useRef(null);
  const bassFilterRef = useRef(null);
  const midFilterRef = useRef(null);
  const trebleFilterRef = useRef(null);
  
  // Update audio quality when user changes
  useEffect(() => {
    const quality = user?.audio_quality || user?.profile?.audio_quality || 'high';
    setAudioQuality(quality);
  }, [user]);
  
  // Initialize Web Audio API (only once)
  useEffect(() => {
    if (!audioContextRef.current) {
      try {
        const AudioContext = window.AudioContext || window.webkitAudioContext;
        const audioContext = new AudioContext();
        audioContextRef.current = audioContext;
        
        // Create gain nodes for equalizer
        const bassFilter = audioContext.createBiquadFilter();
        bassFilter.type = 'lowshelf';
        bassFilter.frequency.value = 60;
        bassFilter.gain.value = 0;
        bassFilterRef.current = bassFilter;
        
        const midFilter = audioContext.createBiquadFilter();
        midFilter.type = 'peaking';
        midFilter.frequency.value = 1000;
        midFilter.Q.value = 1;
        midFilter.gain.value = 0;
        midFilterRef.current = midFilter;
        
        const trebleFilter = audioContext.createBiquadFilter();
        trebleFilter.type = 'highshelf';
        trebleFilter.frequency.value = 10000;
        trebleFilter.gain.value = 0;
        trebleFilterRef.current = trebleFilter;
        
        // Create master gain node
        const gainNode = audioContext.createGain();
        gainNode.gain.value = 1;
        gainNodeRef.current = gainNode;
        
        // Connect filters in series
        bassFilter.connect(midFilter);
        midFilter.connect(trebleFilter);
        trebleFilter.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        console.log('Web Audio API initialized');
      } catch (error) {
        console.error('Error initializing Web Audio API:', error);
        // Continue without Web Audio API - audio will play normally
      }
    }
    
    return () => {
      // Don't close audio context on unmount - keep it alive for the session
    };
  }, []);
  
  // Update equalizer filters when settings change
  useEffect(() => {
    // Only connect to Web Audio API if equalizer is actually being used
    const needsEqualizer = equalizer.bass !== 0 || equalizer.mid !== 0 || equalizer.treble !== 0;
    
    if (needsEqualizer && audioRef.current && !sourceRef.current) {
      connectAudioSource();
    }
    
    if (bassFilterRef.current) {
      bassFilterRef.current.gain.value = equalizer.bass;
    }
    if (midFilterRef.current) {
      midFilterRef.current.gain.value = equalizer.mid;
    }
    if (trebleFilterRef.current) {
      trebleFilterRef.current.gain.value = equalizer.treble;
    }
  }, [equalizer]);
  
  // Update master volume
  useEffect(() => {
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = volume;
    }
    if (audioRef.current) {
      audioRef.current.volume = volume;
    }
  }, [volume]);
  
  // Connect audio element to Web Audio API
  const connectAudioSource = () => {
    if (!audioRef.current || !audioContextRef.current || !bassFilterRef.current) {
      console.warn('Cannot connect audio source: missing required components');
      return false;
    }
    
    // Only create source if it doesn't exist (createMediaElementSource can only be called once)
    if (!sourceRef.current) {
      try {
        // Check if audio context is in a valid state
        if (audioContextRef.current.state === 'closed') {
          console.warn('Audio context is closed, cannot connect source');
          return false;
        }
        
        // Resume audio context if suspended
        if (audioContextRef.current.state === 'suspended') {
          audioContextRef.current.resume().catch(console.error);
        }
        
        const source = audioContextRef.current.createMediaElementSource(audioRef.current);
        sourceRef.current = source;
        source.connect(bassFilterRef.current);
        console.log('Audio source connected to Web Audio API');
        return true;
      } catch (error) {
        console.error('Error connecting audio source:', error);
        // If this fails, don't set sourceRef so we can try again later
        return false;
      }
    }
    return true;
  };

  const handleTimeUpdate = () => {
    if (audioRef.current) {
      setCurrentTime(audioRef.current.currentTime);
    }
  };

  const handleLoadedMetadata = () => {
    if (audioRef.current) {
      setDuration(audioRef.current.duration);
    }
  };

  const handleSongEnd = () => {
    if (repeat === 'one') {
      // Repeat current song
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
        audioRef.current.play().catch(console.error);
      }
    } else {
      playNext();
    }
  };

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.addEventListener('timeupdate', handleTimeUpdate);
      audioRef.current.addEventListener('loadedmetadata', handleLoadedMetadata);
      audioRef.current.addEventListener('ended', handleSongEnd);
      return () => {
        audioRef.current?.removeEventListener('timeupdate', handleTimeUpdate);
        audioRef.current?.removeEventListener('loadedmetadata', handleLoadedMetadata);
        audioRef.current?.removeEventListener('ended', handleSongEnd);
      };
    }
  }, []);

  const playSong = async (song, songList = []) => {
    // Check if song has an audio file - handle null, undefined, empty string, etc.
    const hasAudioFile = song.audio_file && 
                        typeof song.audio_file === 'string' && 
                        song.audio_file.trim() !== '' &&
                        song.audio_file !== 'null' &&
                        song.audio_file !== 'undefined';
    
    if (!hasAudioFile) {
      console.warn('Song has no audio file:', song);
      // Show a more user-friendly notification (you can replace with a toast library)
      if (window.showToast) {
        window.showToast('This song has no audio file available.', 'warning');
      } else {
        // Fallback to console log instead of alert
        console.info('This song does not have an audio file. Audio files must be uploaded separately.');
      }
      return;
    }

    if (songList.length > 0) {
      setQueue(songList);
      const index = songList.findIndex(s => s.id === song.id);
      setCurrentIndex(index >= 0 ? index : 0);
    }
    
    setCurrentSong(song);
    
    // Track play in backend
    try {
      await songsAPI.play(song.id);
    } catch (error) {
      console.error('Failed to track play:', error);
    }

    if (audioRef.current) {
      // Use the audio file URL from the backend as-is
      // The backend serializer already handles URL encoding via build_absolute_uri
      let audioUrl = song.audio_file;
      
      // Double-check that we have a valid URL
      if (!audioUrl || 
          typeof audioUrl !== 'string' || 
          audioUrl.trim() === '' ||
          audioUrl === 'null' ||
          audioUrl === 'undefined') {
        console.error('No valid audio file URL provided for song:', song);
        setIsPlaying(false);
        if (window.showToast) {
          window.showToast('This song does not have a valid audio file. Please contact the artist to upload the audio file.', 'error');
        } else {
          alert('This song does not have a valid audio file. Please contact the artist to upload the audio file.');
        }
        return;
      }
      
      // Clean up the URL - remove any escape sequences that might have been added
      // Replace escaped underscores and other characters
      audioUrl = audioUrl.replace(/\\_/g, '_').replace(/\\/g, '');
      
      // If it's a relative URL, construct the full URL
      if (audioUrl.startsWith('/media/')) {
        // It's a relative URL, prepend the backend URL
        const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        audioUrl = `${backendUrl}${audioUrl}`;
      } else if (!audioUrl.startsWith('http://') && !audioUrl.startsWith('https://')) {
        // If it doesn't start with http/https and doesn't start with /, add /
        if (!audioUrl.startsWith('/')) {
          audioUrl = `/${audioUrl}`;
        }
        // If it's still relative, prepend backend URL
        const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        audioUrl = `${backendUrl}${audioUrl}`;
      }
      
      console.log('Playing audio from URL:', audioUrl);
      console.log('Original audio_file from song:', song.audio_file);
      
      // Final validation before setting src - prevent setting invalid URLs
      if (!audioUrl || 
          audioUrl === 'null' || 
          audioUrl === 'undefined' || 
          audioUrl.trim() === '' ||
          audioUrl.includes('/null') ||
          audioUrl.includes('/undefined')) {
        console.error('Invalid audio URL detected, preventing playback:', audioUrl);
        setIsPlaying(false);
        if (window.showToast) {
          window.showToast('This song does not have a valid audio file. Please contact the artist to upload the audio file.', 'error');
        } else {
          alert('This song does not have a valid audio file. Please contact the artist to upload the audio file.');
        }
        return;
      }
      
      // Set the source and load
      audioRef.current.src = audioUrl;
      audioRef.current.load();
      
      // Add error handler for audio loading
      audioRef.current.onerror = (e) => {
        console.error('Error loading audio:', e);
        console.error('Audio URL:', audioUrl);
        console.error('Original audio_file from song:', song.audio_file);
        console.error('Audio element error details:', {
          error: audioRef.current.error,
          networkState: audioRef.current.networkState,
          readyState: audioRef.current.readyState,
          src: audioRef.current.src
        });
        
        // Get more specific error message
        let errorMessage = 'Failed to load audio file.';
        if (audioRef.current.error) {
          switch (audioRef.current.error.code) {
            case MediaError.MEDIA_ERR_ABORTED:
              errorMessage = 'Audio loading was aborted.';
              break;
            case MediaError.MEDIA_ERR_NETWORK:
              errorMessage = 'Network error while loading audio.';
              break;
            case MediaError.MEDIA_ERR_DECODE:
              errorMessage = 'Audio decoding error.';
              break;
            case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
              errorMessage = 'Audio format not supported or file not found.';
              break;
          }
        }
        
        // Show user-friendly error message
        const displayUrl = audioUrl.replace(/\\_/g, '_'); // Clean up URL for display
        if (window.showToast) {
          window.showToast(`${errorMessage} Please check if the file exists on the server.`, 'error');
        } else {
          alert(`${errorMessage}\n\nURL: ${displayUrl}\n\nPlease check if the file exists on the server.`);
        }
        setIsPlaying(false);
      };
      
      // Add load event to verify successful loading
      audioRef.current.onloadeddata = () => {
        console.log('Audio file loaded successfully:', audioUrl);
      };
      
      // Add canplay event
      audioRef.current.oncanplay = () => {
        console.log('Audio can start playing:', audioUrl);
      };
      
      // Don't connect to Web Audio API here - let audio play normally
      // Connection will happen automatically when equalizer is adjusted
      
      // Resume audio context if suspended (required by some browsers)
      if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
        audioContextRef.current.resume().catch(console.error);
      }
      
      // Play audio normally (without Web Audio API unless equalizer is active)
      audioRef.current.play()
        .then(() => {
          setIsPlaying(true);
        })
        .catch((error) => {
          console.error('Error playing audio:', error);
          setIsPlaying(false);
          // Try to resume audio context if it's suspended
          if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
            audioContextRef.current.resume().then(() => {
              audioRef.current?.play()
                .then(() => setIsPlaying(true))
                .catch(err => {
                  console.error('Error playing after resume:', err);
                  alert('Failed to play audio. Please interact with the page first (browser autoplay policy).');
                });
            }).catch(console.error);
          } else {
            alert('Failed to play audio. Please check your browser console for details.');
          }
        });
    }
  };

  const togglePlayPause = () => {
    if (audioRef.current) {
      if (isPlaying) {
        audioRef.current.pause();
      } else {
        audioRef.current.play();
      }
      setIsPlaying(!isPlaying);
    }
  };

  const playNext = () => {
    if (queue.length === 0) return;
    
    if (shuffle) {
      // Random next song
      let nextIndex;
      do {
        nextIndex = Math.floor(Math.random() * queue.length);
      } while (nextIndex === currentIndex && queue.length > 1);
      setCurrentIndex(nextIndex);
      playSong(queue[nextIndex], queue);
    } else if (currentIndex < queue.length - 1) {
      const nextIndex = currentIndex + 1;
      setCurrentIndex(nextIndex);
      playSong(queue[nextIndex], queue);
    } else if (repeat === 'all') {
      // Loop back to start
      setCurrentIndex(0);
      playSong(queue[0], queue);
    }
  };

  const playPrevious = () => {
    if (queue.length === 0) {
      if (audioRef.current) {
        audioRef.current.currentTime = 0;
      }
      return;
    }
    
    if (shuffle) {
      // Random previous song
      let prevIndex;
      do {
        prevIndex = Math.floor(Math.random() * queue.length);
      } while (prevIndex === currentIndex && queue.length > 1);
      setCurrentIndex(prevIndex);
      playSong(queue[prevIndex], queue);
    } else if (currentIndex > 0) {
      const prevIndex = currentIndex - 1;
      setCurrentIndex(prevIndex);
      playSong(queue[prevIndex], queue);
    } else if (repeat === 'all') {
      // Loop to end
      const lastIndex = queue.length - 1;
      setCurrentIndex(lastIndex);
      playSong(queue[lastIndex], queue);
    } else if (audioRef.current) {
      audioRef.current.currentTime = 0;
    }
  };

  const seek = (time) => {
    if (audioRef.current) {
      audioRef.current.currentTime = time;
      setCurrentTime(time);
    }
  };

  const formatTime = (seconds) => {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const toggleShuffle = () => {
    setShuffle(!shuffle);
  };

  const toggleRepeat = () => {
    const modes = ['off', 'all', 'one'];
    const currentModeIndex = modes.indexOf(repeat);
    setRepeat(modes[(currentModeIndex + 1) % modes.length]);
  };

  const updateEqualizer = (band, value) => {
    setEqualizer(prev => ({
      ...prev,
      [band]: Math.max(-12, Math.min(12, value))
    }));
  };

  const resetEqualizer = () => {
    setEqualizer({ bass: 0, mid: 0, treble: 0 });
  };

  const value = {
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
    audioQuality,
    setAudioQuality,
    equalizer,
    updateEqualizer,
    resetEqualizer,
    showEqualizer,
    setShowEqualizer,
    audioRef,
    playSong,
    togglePlayPause,
    playNext,
    playPrevious,
    seek,
    setVolume,
    formatTime,
    toggleShuffle,
    toggleRepeat,
    setShowQueue,
  };

  return (
    <PlayerContext.Provider value={value}>
      {children}
      <audio ref={audioRef} />
    </PlayerContext.Provider>
  );
};
