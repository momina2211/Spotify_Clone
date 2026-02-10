import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { subscriptionsAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function SubscriptionSuccess() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { refreshUser, isArtist, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Redirect artists away from subscription success page
  useEffect(() => {
    if (isArtist || user?.role === 2 || user?.user?.role === 2 || user?.profile_type === 2) {
      navigate('/');
      return;
    }
  }, [isArtist, user, navigate]);

  useEffect(() => {
    const sessionId = searchParams.get('session_id');
    
    if (!sessionId) {
      setError('No session ID found');
      setLoading(false);
      return;
    }

    // Wait a moment for webhook to process, then refresh user data
    const timer = setTimeout(async () => {
      try {
        // Refresh user data multiple times to ensure webhook has processed
        await refreshUser();
        // Wait a bit more and refresh again
        setTimeout(async () => {
          await refreshUser();
          setLoading(false);
          // Redirect to subscriptions page after 2 seconds
          setTimeout(() => {
            navigate('/subscriptions');
          }, 2000);
        }, 3000);
      } catch (error) {
        console.error('Failed to refresh user:', error);
        setError('Failed to verify subscription');
        setLoading(false);
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [searchParams, refreshUser, navigate]);

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-green-500 mx-auto mb-4"></div>
          <p className="text-xl">Processing your subscription...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="text-red-500 text-6xl mb-4">✕</div>
          <h1 className="text-3xl font-bold mb-4">Subscription Error</h1>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => navigate('/subscriptions')}
            className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-full font-semibold"
          >
            Back to Subscriptions
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="text-center">
        <div className="text-green-500 text-6xl mb-4">✓</div>
        <h1 className="text-4xl font-bold mb-4">Welcome to Premium!</h1>
        <p className="text-gray-400 mb-6 text-lg">
          Your subscription has been activated successfully.
        </p>
        <p className="text-gray-500 text-sm mb-8">
          Redirecting to subscriptions page...
        </p>
        <button
          onClick={() => navigate('/subscriptions')}
          className="bg-green-500 hover:bg-green-600 text-white px-6 py-3 rounded-full font-semibold"
        >
          Go to Subscriptions
        </button>
      </div>
    </div>
  );
}
