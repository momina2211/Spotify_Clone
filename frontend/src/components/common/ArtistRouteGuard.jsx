import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import LoadingSpinner from './LoadingSpinner';

/**
 * Route guard component that redirects non-artists
 * Usage: Wrap artist-only pages with this component
 */
export default function ArtistRouteGuard({ children }) {
  const { isArtist, loading } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Only redirect if auth is loaded and user is not an artist
    if (!loading && !isArtist) {
      navigate('/');
    }
  }, [isArtist, loading, navigate]);

  // Show loading while checking auth
  if (loading) {
    return <LoadingSpinner message="Checking permissions..." />;
  }

  // Don't render children if not artist (will redirect)
  if (!isArtist) {
    return null;
  }

  return children;
}
