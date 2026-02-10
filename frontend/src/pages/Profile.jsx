import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { authAPI, studentVerificationAPI } from '../services/api';
import { UserIcon, CameraIcon, CheckIcon, XMarkIcon, AcademicCapIcon } from '@heroicons/react/24/outline';

export default function Profile() {
  const navigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [formData, setFormData] = useState({
    email: '',
    currentPassword: '',
    newPassword: '',
    confirmPassword: '',
    profile_picture: null,
  });
  const [previewImage, setPreviewImage] = useState(null);

  useEffect(() => {
    if (user) {
      setFormData(prev => ({
        ...prev,
        email: user.user?.email || user.email || '',
      }));
      const profilePic = user.profile_picture || user.user?.profile_picture;
      if (profilePic) {
        // Add cache busting to force refresh - remove existing query params first
        const baseUrl = profilePic.split('?')[0]; // Get URL without query params
        const timestamp = new Date(user.updated_at || user.user?.updated_at || Date.now()).getTime();
        setPreviewImage(`${baseUrl}?t=${timestamp}`);
      } else {
        setPreviewImage(null);
      }
    }
    loadVerificationStatus();
  }, [user?.profile_picture, user?.user?.profile_picture, user?.email, user?.user?.email]);

  const loadVerificationStatus = async () => {
    try {
      const response = await studentVerificationAPI.getStatus();
      setVerificationStatus(response.data);
    } catch (error) {
      console.error('Failed to load verification status:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
    setSuccess('');
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) { // 5MB limit
        setError('Image size must be less than 5MB');
        return;
      }
      setFormData(prev => ({ ...prev, profile_picture: file }));
      
      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreviewImage(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    // Validate password change if new password is provided
    if (formData.newPassword) {
      if (!formData.currentPassword) {
        setError('Current password is required to change password');
        setLoading(false);
        return;
      }
      if (formData.newPassword.length < 6) {
        setError('New password must be at least 6 characters');
        setLoading(false);
        return;
      }
      if (formData.newPassword !== formData.confirmPassword) {
        setError('New passwords do not match');
        setLoading(false);
        return;
      }
    }

    try {
      const updateData = new FormData();
      
      // Update email if changed
      if (formData.email && formData.email !== (user.user?.email || user.email)) {
        updateData.append('user[email]', formData.email);
      }

      // Update password if provided
      if (formData.newPassword && formData.currentPassword) {
        updateData.append('user[password]', formData.newPassword);
      }

      // Update profile picture if changed
      if (formData.profile_picture) {
        updateData.append('profile_picture', formData.profile_picture);
      }

      const response = await authAPI.updateProfile(updateData);
      
      setSuccess('Profile updated successfully!');
      
      // Update preview image immediately if profile picture was updated
      if (formData.profile_picture) {
        // Keep the local preview for immediate feedback in Profile page
        const reader = new FileReader();
        reader.onloadend = () => {
          setPreviewImage(reader.result);
        };
        reader.readAsDataURL(formData.profile_picture);
      }
      
      // Update form data but keep email if it was updated
      const updatedEmail = response?.data?.user?.email || response?.data?.email;
      setFormData(prev => ({
        ...prev,
        email: updatedEmail || prev.email,
        currentPassword: '',
        newPassword: '',
        confirmPassword: '',
        profile_picture: null,
      }));
      
      // Reset file input
      const fileInput = document.querySelector('input[type="file"]');
      if (fileInput) fileInput.value = '';
      
      // Immediately refresh user data to update sidebar
      try {
        // First refresh to get the updated profile picture URL
        const updatedUserResponse = await authAPI.getProfile();
        const updatedUserData = updatedUserResponse?.data;
        if (updatedUserData) {
          const profilePic = updatedUserData.profile_picture || updatedUserData.user?.profile_picture;
          if (profilePic) {
            // Update preview with server URL immediately - remove existing query params first
            const baseUrl = profilePic.split('?')[0];
            setPreviewImage(`${baseUrl}?t=${Date.now()}`);
          }
          // Update email in form if it changed
          const newEmail = updatedUserData.user?.email || updatedUserData.email;
          if (newEmail) {
            setFormData(prev => ({ ...prev, email: newEmail }));
          }
        }
        // Refresh user context to update sidebar
        if (refreshUser) {
          await refreshUser();
        }
      } catch (error) {
        console.error('Failed to refresh profile:', error);
        // If immediate refresh fails, try again after delay
        setTimeout(async () => {
          try {
            if (refreshUser) {
              await refreshUser();
            }
          } catch (retryError) {
            console.error('Retry refresh failed:', retryError);
          }
        }, 1000);
      }
    } catch (error) {
      console.error('Profile update failed:', error);
      setError(error.response?.data?.error || error.response?.data?.detail || 'Failed to update profile');
    } finally {
      setLoading(false);
    }
  };

  const removeImage = () => {
    setFormData(prev => ({ ...prev, profile_picture: null }));
    const currentPic = user?.profile_picture || user?.user?.profile_picture;
    if (currentPic) {
      setPreviewImage(`${currentPic}?t=${Date.now()}`);
    } else {
      setPreviewImage(null);
    }
  };

  return (
    <div className="bg-black min-h-screen pb-32">
      <div className="max-w-3xl mx-auto p-8">
        <h1 className="text-4xl font-bold text-white mb-8">Profile Settings</h1>

        {error && (
          <div className="bg-red-500/20 border border-red-500 text-red-200 px-4 py-3 rounded mb-4 flex items-center space-x-2">
            <XMarkIcon className="w-5 h-5" />
            <span>{error}</span>
          </div>
        )}

        {success && (
          <div className="bg-green-500/20 border border-green-500 text-green-200 px-4 py-3 rounded mb-4 flex items-center space-x-2">
            <CheckIcon className="w-5 h-5" />
            <span>{success}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Profile Picture Section */}
          <div className="bg-white/5 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Profile Picture</h2>
            <div className="flex items-center space-x-6">
              <div className="relative">
                {previewImage ? (
                  <img
                    key={previewImage}
                    src={previewImage.includes('data:') ? previewImage : `${previewImage}?t=${Date.now()}`}
                    alt="Profile"
                    className="w-32 h-32 rounded-full object-cover border-2 border-white/20"
                    onError={(e) => {
                      // Fallback if image fails to load
                      e.target.style.display = 'none';
                    }}
                  />
                ) : (
                  <div className="w-32 h-32 rounded-full bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center border-2 border-white/20">
                    <UserIcon className="w-16 h-16 text-white" />
                  </div>
                )}
                <label
                  htmlFor="profile-picture"
                  className="absolute bottom-0 right-0 bg-green-500 hover:bg-green-400 rounded-full p-2 cursor-pointer transition-colors"
                >
                  <CameraIcon className="w-5 h-5 text-black" />
                  <input
                    type="file"
                    id="profile-picture"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="hidden"
                  />
                </label>
              </div>
              <div className="flex-1">
                <p className="text-gray-400 text-sm mb-2">
                  JPG, PNG or GIF. Max size 5MB.
                </p>
                {formData.profile_picture && (
                  <button
                    type="button"
                    onClick={removeImage}
                    className="text-red-400 hover:text-red-300 text-sm"
                  >
                    Remove image
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Account Information */}
          <div className="bg-white/5 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Account Information</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-white mb-2 font-medium">Email</label>
                <input
                  type="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Enter your email"
                />
              </div>

              <div>
                <label className="block text-gray-400 mb-2 text-sm">Account Type</label>
                <div className="px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white">
                  {user?.role === 2 || user?.user?.role === 2 ? 'Artist' : 'User'}
                </div>
              </div>

              {/* Student Verification Section */}
              <div className="pt-4 border-t border-white/10">
                <div className="flex items-center justify-between">
                  <div>
                    <label className="block text-white mb-1 font-medium">Student Verification</label>
                    <p className="text-gray-400 text-sm">
                      {verificationStatus?.is_verified 
                        ? '✓ Verified' 
                        : verificationStatus?.latest_verification?.status === 'pending'
                        ? '⏳ Pending Review'
                        : 'Not verified'}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => navigate('/student-verification')}
                    className="flex items-center gap-2 bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-lg font-semibold transition-colors"
                  >
                    <AcademicCapIcon className="w-5 h-5" />
                    {verificationStatus?.is_verified ? 'View Status' : 'Verify Student Status'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Change Password Section */}
          <div className="bg-white/5 rounded-lg p-6">
            <h2 className="text-xl font-bold text-white mb-4">Change Password</h2>
            <p className="text-gray-400 text-sm mb-4">
              Leave blank if you don't want to change your password
            </p>
            
            <div className="space-y-4">
              <div>
                <label className="block text-white mb-2 font-medium">Current Password</label>
                <input
                  type="password"
                  name="currentPassword"
                  value={formData.currentPassword}
                  onChange={handleInputChange}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Enter current password"
                />
              </div>

              <div>
                <label className="block text-white mb-2 font-medium">New Password</label>
                <input
                  type="password"
                  name="newPassword"
                  value={formData.newPassword}
                  onChange={handleInputChange}
                  minLength={6}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Enter new password (min 6 characters)"
                />
              </div>

              <div>
                <label className="block text-white mb-2 font-medium">Confirm New Password</label>
                <input
                  type="password"
                  name="confirmPassword"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  minLength={6}
                  className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-green-500"
                  placeholder="Confirm new password"
                />
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <div className="flex space-x-4">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 bg-green-500 hover:bg-green-400 text-black font-bold py-3 rounded-lg transition-colors disabled:opacity-50"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
