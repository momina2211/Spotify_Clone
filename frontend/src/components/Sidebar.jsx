import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  HomeIcon,
  MagnifyingGlassIcon,
  HeartIcon,
  ClockIcon,
  UserGroupIcon,
  MusicalNoteIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import {
  HomeIcon as HomeIconSolid,
  MagnifyingGlassIcon as MagnifyingGlassIconSolid,
  HeartIcon as HeartIconSolid,
  ClockIcon as ClockIconSolid,
  UserGroupIcon as UserGroupIconSolid,
  MusicalNoteIcon as MusicalNoteIconSolid,
} from '@heroicons/react/24/solid';

const menuItems = [
  { path: '/', label: 'Home', icon: HomeIcon, iconSolid: HomeIconSolid },
  { path: '/search', label: 'Search', icon: MagnifyingGlassIcon, iconSolid: MagnifyingGlassIconSolid },
  { path: '/favorites', label: 'Favorites', icon: HeartIcon, iconSolid: HeartIconSolid },
  { path: '/recently-played', label: 'Recently Played', icon: ClockIcon, iconSolid: ClockIconSolid },
  { path: '/artists', label: 'Artists', icon: UserGroupIcon, iconSolid: UserGroupIconSolid },
  { path: '/trending', label: 'Trending', icon: MusicalNoteIcon, iconSolid: MusicalNoteIconSolid },
];

export default function Sidebar() {
  const location = useLocation();
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="w-64 bg-black/80 backdrop-blur-lg h-screen fixed left-0 top-0 p-6 overflow-y-auto flex flex-col">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-white">Spotify Clone</h1>
        {user && (
          <p className="text-gray-400 text-sm mt-2">{user.email}</p>
        )}
      </div>

      <nav className="space-y-2 flex-1">
        {menuItems.map((item) => {
          const isActive = location.pathname === item.path;
          const Icon = isActive ? item.iconSolid : item.icon;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
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
      </nav>

      <button
        onClick={handleLogout}
        className="flex items-center space-x-3 px-4 py-3 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-colors mt-auto"
      >
        <ArrowRightOnRectangleIcon className="w-6 h-6" />
        <span className="font-medium">Logout</span>
      </button>
    </div>
  );
}
