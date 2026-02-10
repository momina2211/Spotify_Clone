import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { PlayerProvider } from './context/PlayerContext';
import Sidebar from './components/Sidebar';
import Player from './components/Player';
import Login from './components/Login';
import Register from './components/Register';
import Home from './pages/Home';
import Search from './pages/Search';
import Library from './pages/Library';
import Favorites from './pages/Favorites';
import RecentlyPlayed from './pages/RecentlyPlayed';
import Artists from './pages/Artists';
import Trending from './pages/Trending';
import PlaylistDetail from './pages/PlaylistDetail';
import AlbumDetail from './pages/AlbumDetail';
import ArtistDetail from './pages/ArtistDetail';
import ArtistDashboard from './pages/ArtistDashboard';
import UploadSong from './pages/UploadSong';
import ManageAlbums from './pages/ManageAlbums';
import ManageGenres from './pages/ManageGenres';
import ManageSongs from './pages/ManageSongs';
import Profile from './pages/Profile';
import Subscriptions from './pages/Subscriptions';
import SubscriptionSuccess from './pages/SubscriptionSuccess';
import StudentVerification from './pages/StudentVerification';
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts';
import './App.css';

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-black">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" />;
}

function AppLayout({ children }) {
  useKeyboardShortcuts();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  return (
    <div className="flex h-screen bg-black">
      <Sidebar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <main className="flex-1 md:ml-64 overflow-y-auto bg-black">
        {/* Mobile menu button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="md:hidden fixed top-4 left-4 z-50 p-2 bg-black/80 rounded-lg text-white hover:bg-white/10 transition-colors"
          aria-label="Toggle menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            {sidebarOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
        {children}
      </main>
      <Player />
    </div>
  );
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <AppLayout>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/search" element={<Search />} />
                <Route path="/library" element={<Library />} />
                <Route path="/favorites" element={<Favorites />} />
                <Route path="/recently-played" element={<RecentlyPlayed />} />
                <Route path="/artists" element={<Artists />} />
                <Route path="/trending" element={<Trending />} />
                <Route path="/playlist/:id" element={<PlaylistDetail />} />
                <Route path="/album/:id" element={<AlbumDetail />} />
                <Route path="/artist/:id" element={<ArtistDetail />} />
                <Route path="/artist/dashboard" element={<ArtistDashboard />} />
                <Route path="/artist/upload" element={<UploadSong />} />
                <Route path="/artist/songs" element={<ManageSongs />} />
                <Route path="/artist/albums" element={<ManageAlbums />} />
                <Route path="/artist/genres" element={<ManageGenres />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/subscriptions" element={<Subscriptions />} />
                <Route path="/subscriptions/success" element={<SubscriptionSuccess />} />
                <Route path="/student-verification" element={<StudentVerification />} />
              </Routes>
            </AppLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <Router>
      <AuthProvider>
        <PlayerProvider>
          <AppRoutes />
        </PlayerProvider>
      </AuthProvider>
    </Router>
  );
}

export default App;
