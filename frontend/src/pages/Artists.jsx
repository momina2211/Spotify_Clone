import { useState, useEffect } from 'react';
import { artistsAPI } from '../services/api';
import { Link } from 'react-router-dom';
import { UserGroupIcon, HeartIcon } from '@heroicons/react/24/outline';
import { HeartIcon as HeartSolidIcon } from '@heroicons/react/24/solid';

export default function Artists() {
  const [artists, setArtists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [following, setFollowing] = useState(new Set());

  useEffect(() => {
    loadArtists();
    loadFollowing();
  }, []);

  const loadArtists = async () => {
    try {
      const response = await artistsAPI.getAll();
      setArtists(response.data);
    } catch (error) {
      console.error('Failed to load artists:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFollowing = async () => {
    try {
      const response = await artistsAPI.following();
      const followingIds = new Set(response.data.map(a => a.id));
      setFollowing(followingIds);
    } catch (error) {
      console.error('Failed to load following:', error);
    }
  };

  const handleFollow = async (artistId, isFollowing) => {
    try {
      if (isFollowing) {
        await artistsAPI.unfollow(artistId);
        setFollowing(prev => {
          const next = new Set(prev);
          next.delete(artistId);
          return next;
        });
      } else {
        await artistsAPI.follow(artistId);
        setFollowing(prev => new Set([...prev, artistId]));
      }
    } catch (error) {
      console.error('Failed to follow/unfollow:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-white text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-8 pb-32">
      <div className="flex items-center space-x-2 mb-8">
        <UserGroupIcon className="w-8 h-8 text-green-500" />
        <h1 className="text-4xl font-bold text-white">Artists</h1>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
        {artists.map((artist) => {
          const isFollowing = following.has(artist.id);
          return (
            <div
              key={artist.id}
              className="bg-white/5 hover:bg-white/10 rounded-lg p-6 cursor-pointer transition-all text-center group"
            >
              <Link to={`/artists/${artist.id}`}>
                <div className="w-full aspect-square rounded-full bg-gradient-to-br from-purple-500 to-blue-500 mb-4 mx-auto group-hover:scale-110 transition-transform" />
                <h3 className="text-white font-medium truncate mb-1">{artist.username}</h3>
                <p className="text-gray-400 text-sm mb-2">{artist.song_count} songs</p>
                <p className="text-gray-500 text-xs">{artist.follower_count} followers</p>
              </Link>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleFollow(artist.id, isFollowing);
                }}
                className="mt-3 text-gray-400 hover:text-red-500 transition-colors"
              >
                {isFollowing ? (
                  <HeartSolidIcon className="w-5 h-5 text-red-500 mx-auto" />
                ) : (
                  <HeartIcon className="w-5 h-5 mx-auto" />
                )}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
