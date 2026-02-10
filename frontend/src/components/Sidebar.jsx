import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { playlistsAPI } from '../services/api';
import {
  HomeIcon,
  MagnifyingGlassIcon,
  Squares2X2Icon,
  PlusIcon,
  HeartIcon,
  ArrowRightOnRectangleIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  MusicalNoteIcon,
  RectangleStackIcon,
  TagIcon,
  ChartBarIcon,
  ListBulletIcon,
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  MagnifyingGlassIcon as MagnifyingGlassIconSolid,
  Squares2X2Icon as Squares2X2IconSolid,
  HeartIcon as HeartIconSolid,
  MusicalNoteIcon as MusicalNoteIconSolid,
  RectangleStackIcon as RectangleStackIconSolid,
  TagIcon as TagIconSolid,
  ChartBarIcon as ChartBarIconSolid,
  ListBulletIcon as ListBulletIconSolid,
} from '@heroicons/react/24/solid';

const mainMenuItems = [
  { path: '/', label: 'Home', icon: HomeIcon, iconSolid: HomeIconSolid },
  { path: '/search', label: 'Search', icon: MagnifyingGlassIcon, iconSolid: MagnifyingGlassIconSolid },
  { path: '/library', label: 'Library', icon: Squares2X2Icon, iconSolid: Squares2X2IconSolid },
];

const artistMenuItems = [
  { path: '/artist/dashboard', label: 'Dashboard', icon: ChartBarIcon, iconSolid: ChartBarIconSolid },
  { path: '/artist/upload', label: 'Upload Song', icon: MusicalNoteIcon, iconSolid: MusicalNoteIconSolid },
  { path: '/artist/songs', label: 'Manage Songs', icon: ListBulletIcon, iconSolid: ListBulletIconSolid },
  { path: '/artist/albums', label: 'Manage Albums', icon: RectangleStackIcon, iconSolid: RectangleStackIconSolid },
  { path: '/artist/genres', label: 'Manage Genres', icon: TagIcon, iconSolid: TagIconSolid },
];

export default function Sidebar({ sidebarOpen, setSidebarOpen }) {
  const location = useLocation();
  const { user, logout, isArtist } = useAuth();
  const navigate = useNavigate();
  const [playlists, setPlaylists] = useState([]);
  const [showPlaylists, setShowPlaylists] = useState(true);
  const [loading, setLoading] = useState(true);
  const [profilePicUrl, setProfilePicUrl] = useState(null);
  
  // Close sidebar on mobile when navigating
  useEffect(() => {
    if (sidebarOpen && window.innerWidth < 768) {
      setSidebarOpen(false);
    }
  }, [location.pathname, sidebarOpen, setSidebarOpen]);

  // Update profile picture URL when user changes
  useEffect(() => {
    const pic = user?.profile_picture || user?.user?.profile_picture;
    if (pic) {
      // Add cache busting to force refresh - remove existing query params first
      const baseUrl = pic.split('?')[0]; // Get URL without query params
      const timestamp = Date.now();
      setProfilePicUrl(`${baseUrl}?t=${timestamp}`);
    } else {
      setProfilePicUrl(null);
    }
  }, [user?.profile_picture, user?.user?.profile_picture]);

  // Debug log for artist check
  useEffect(() => {
    console.log('Sidebar - isArtist:', isArtist, 'user:', user);
  }, [isArtist, user]);

  useEffect(() => {
    loadPlaylists();
  }, []);

  const loadPlaylists = async () => {
    try {
      const response = await playlistsAPI.getAll();
      setPlaylists(response.data);
    } catch (error) {
      console.error('Failed to load playlists:', error);
    } finally {
      setLoading(false);
    }
  };

  // Expose refresh function globally so Player can refresh playlists
  useEffect(() => {
    window.refreshPlaylists = loadPlaylists;
    return () => {
      delete window.refreshPlaylists;
    };
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className={`w-64 bg-black h-screen fixed left-0 top-0 flex flex-col z-40 transform transition-transform duration-300 ease-in-out ${
      sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
    }`}>
      {/* Logo and Main Navigation */}
      <div className="p-6 pb-4">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-white">Spotify</h1>
        </div>

        <nav className="space-y-1">
          {mainMenuItems.map((item) => {
            const isActive = location.pathname === item.path;
            const Icon = isActive ? item.iconSolid : item.icon;
            
            return (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => {
                  if (window.innerWidth < 768) {
                    setSidebarOpen(false);
                  }
                }}
                className={`flex items-center space-x-4 px-4 py-3 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-white/10 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <Icon className="w-6 h-6" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
          
          {/* Profile Link - Always visible */}
          <Link
            to="/profile"
            onClick={() => {
              if (window.innerWidth < 768) {
                setSidebarOpen(false);
              }
            }}
            className={`flex items-center space-x-4 px-4 py-3 rounded-lg transition-colors ${
              location.pathname === '/profile'
                ? 'bg-white/10 text-white'
                : 'text-gray-400 hover:text-white hover:bg-white/5'
            }`}
          >
            <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
            <span className="font-medium">Profile</span>
          </Link>
          
          {/* Subscriptions Link - Only for non-artist users */}
          {!(isArtist || user?.role === 2 || user?.user?.role === 2 || user?.profile_type === 2) && (
            <Link
              to="/subscriptions"
              onClick={() => {
                if (window.innerWidth < 768) {
                  setSidebarOpen(false);
                }
              }}
              className={`flex items-center space-x-4 px-4 py-3 rounded-lg transition-colors ${
                location.pathname === '/subscriptions'
                  ? 'bg-white/10 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <svg className="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
              </svg>
              <span className="font-medium">Subscriptions</span>
            </Link>
          )}
          
          {/* Artist-only menu items */}
          {(isArtist || user?.role === 2 || user?.user?.role === 2 || user?.profile_type === 2) && (
            <>
              <div className="pt-4 mt-4 border-t border-gray-800">
                <p className="px-4 mb-2 text-xs font-bold text-gray-400 uppercase">Artist Tools</p>
                {artistMenuItems.map((item) => {
                  const isActive = location.pathname === item.path;
                  const Icon = isActive ? item.iconSolid : item.icon;
                  
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => {
                        if (window.innerWidth < 768) {
                          setSidebarOpen(false);
                        }
                      }}
                      className={`flex items-center space-x-4 px-4 py-3 rounded-lg transition-colors ${
                        isActive
                          ? 'bg-white/10 text-white'
                          : 'text-gray-400 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      <Icon className="w-6 h-6" />
                      <span className="font-medium">{item.label}</span>
                    </Link>
                  );
                })}
              </div>
            </>
          )}
        </nav>
      </div>

      {/* Playlists Section */}
      <div className="flex-1 overflow-y-auto px-6 pb-24">
        <div className="flex items-center justify-between mb-2">
          <button
            onClick={() => setShowPlaylists(!showPlaylists)}
            className="flex items-center space-x-2 text-gray-400 hover:text-white transition-colors"
          >
            {showPlaylists ? (
              <ChevronUpIcon className="w-5 h-5" />
            ) : (
              <ChevronDownIcon className="w-5 h-5" />
            )}
            <span className="text-sm font-medium">Playlists</span>
          </button>
          <Link
            to="/library?create=playlist"
            className="text-gray-400 hover:text-white transition-colors"
            title="Create playlist"
          >
            <PlusIcon className="w-5 h-5" />
          </Link>
        </div>

        {showPlaylists && (
          <div className="space-y-1">
            {/* Find "Liked Songs" playlist or use /favorites as fallback */}
            {(() => {
              const likedSongsPlaylist = playlists.find(p => p.name === 'Liked Songs');
              const likedSongsPath = likedSongsPlaylist ? `/playlist/${likedSongsPlaylist.id}` : '/favorites';
              const isLikedSongsActive = likedSongsPlaylist 
                ? location.pathname === `/playlist/${likedSongsPlaylist.id}`
                : location.pathname === '/favorites';
              
              return (
                <Link
                  to={likedSongsPath}
                  onClick={() => {
                    if (window.innerWidth < 768) {
                      setSidebarOpen(false);
                    }
                  }}
                  className={`flex items-center space-x-4 px-4 py-2 rounded-lg transition-colors ${
                    isLikedSongsActive
                      ? 'bg-white/10 text-white'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <HeartIcon className="w-5 h-5" />
                  <span className="text-sm truncate">Liked Songs</span>
                </Link>
              );
            })()}
            
            {loading ? (
              <div className="text-gray-400 text-sm px-4 py-2">Loading...</div>
            ) : (
              playlists
                .filter(playlist => playlist.name !== 'Liked Songs') // Don't show Liked Songs twice
                .map((playlist) => (
                  <Link
                    key={playlist.id}
                    to={`/playlist/${playlist.id}`}
                    onClick={() => {
                      if (window.innerWidth < 768) {
                        setSidebarOpen(false);
                      }
                    }}
                    className={`block px-4 py-2 rounded-lg transition-colors truncate ${
                      location.pathname === `/playlist/${playlist.id}`
                        ? 'bg-white/10 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <span className="text-sm">{playlist.name}</span>
                  </Link>
                ))
            )}
          </div>
        )}
      </div>

      {/* User Section */}
      <div className="p-4 border-t border-gray-800 space-y-2">
        <Link
          to="/profile"
          onClick={() => {
            if (window.innerWidth < 768) {
              setSidebarOpen(false);
            }
          }}
          className="flex items-center space-x-3 w-full px-4 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center overflow-hidden relative">
            {profilePicUrl ? (
              <img
                key={profilePicUrl}
                src={profilePicUrl}
                alt="Profile"
                className="w-full h-full rounded-full object-cover"
                onError={(e) => {
                  // Fallback if image fails to load - show initial instead
                  console.error('Failed to load profile picture:', profilePicUrl);
                  setProfilePicUrl(null);
                }}
              />
            ) : (
              <span className="text-white text-sm font-bold absolute inset-0 flex items-center justify-center">
                {user?.email?.[0]?.toUpperCase() || user?.user?.email?.[0]?.toUpperCase() || 'U'}
              </span>
            )}
          </div>
          <div className="flex-1 text-left min-w-0">
            <p className="text-white text-sm font-medium truncate">
              {user?.email || user?.user?.email || 'User'}
            </p>
            <p className="text-gray-400 text-xs truncate">
              {(() => {
                if (isArtist) return 'Artist';
                // Check for subscription status
                const subscriptionPlan = user?.subscription_plan_name || user?.subscription_plan?.name;
                const subscriptionStatus = user?.subscription_status;
                if (subscriptionPlan && (subscriptionStatus === 'active' || subscriptionStatus === 'trialing')) {
                  return subscriptionPlan.replace('Premium ', '');
                }
                return 'Free';
              })()}
            </p>
          </div>
        </Link>
        <button
          onClick={handleLogout}
          className="flex items-center space-x-3 w-full px-4 py-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
        >
          <ArrowRightOnRectangleIcon className="w-5 h-5 flex-shrink-0" />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </div>
  );
}
