import { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      loadUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const loadUser = async () => {
    try {
      const response = await authAPI.getProfile();
      const userData = response.data;
      // Include role from user object if available
      if (userData.user && userData.user.role) {
        userData.role = userData.user.role;
      }
      // Also check profile_type as fallback
      if (!userData.role && userData.profile_type) {
        userData.role = userData.profile_type;
      }
      console.log('User data loaded:', userData); // Debug log
      setUser(userData);
    } catch (error) {
      console.error('Failed to load user:', error);
      // Only logout if it's an authentication error (401/403), not on every error
      if (error.response?.status === 401 || error.response?.status === 403) {
        logout();
      } else {
        // For other errors, just log but don't clear user data
        console.warn('Error loading user, but keeping existing user data');
      }
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await authAPI.login({ email, password });
      const { token: newToken, user: userData } = response.data;
      setToken(newToken);
      setUser(userData);
      localStorage.setItem('token', newToken);
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      console.error('Error response:', error.response);
      
      let errorMessage = 'Login failed';
      
      if (error.response) {
        if (error.response.data) {
          if (typeof error.response.data === 'string') {
            errorMessage = error.response.data;
          } else if (error.response.data.error) {
            errorMessage = error.response.data.error;
          } else if (error.response.data.detail) {
            errorMessage = error.response.data.detail;
          } else if (error.response.data.non_field_errors) {
            errorMessage = error.response.data.non_field_errors[0];
          }
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  const register = async (email, password, role = 1) => {
    try {
      const response = await authAPI.register({ email, password, role });
      const { token: newToken, user: userData } = response.data;
      setToken(newToken);
      setUser(userData);
      localStorage.setItem('token', newToken);
      return { success: true };
    } catch (error) {
      console.error('Registration error:', error);
      console.error('Error response:', error.response);
      
      // Extract error message from various possible formats
      let errorMessage = 'Registration failed';
      
      // Check if it's a network error (backend not running)
      if (error.code === 'ERR_NETWORK' || error.message.includes('Network Error')) {
        errorMessage = 'Cannot connect to server. Please make sure the Django backend is running on http://localhost:8000';
      } else if (error.response) {
        // Handle Django REST Framework error format
        if (error.response.data) {
          if (typeof error.response.data === 'string') {
            errorMessage = error.response.data;
          } else if (error.response.data.error) {
            errorMessage = error.response.data.error;
          } else if (error.response.data.detail) {
            errorMessage = error.response.data.detail;
          } else if (error.response.data.non_field_errors) {
            errorMessage = error.response.data.non_field_errors[0];
          } else if (error.response.data.email) {
            errorMessage = `Email: ${Array.isArray(error.response.data.email) ? error.response.data.email[0] : error.response.data.email}`;
          } else if (error.response.data.password) {
            errorMessage = `Password: ${Array.isArray(error.response.data.password) ? error.response.data.password[0] : error.response.data.password}`;
          } else {
            // Try to get first error message from any field
            const firstKey = Object.keys(error.response.data)[0];
            if (firstKey) {
              const firstError = error.response.data[firstKey];
              errorMessage = `${firstKey}: ${Array.isArray(firstError) ? firstError[0] : firstError}`;
            }
          }
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      return {
        success: false,
        error: errorMessage,
      };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
  };

  const refreshUser = async () => {
    if (token) {
      await loadUser();
    }
  };

  // Check role from multiple possible locations
  const userRole = user?.role || user?.user?.role || user?.profile_type;
  const isArtist = userRole === 2;
  const isUser = !isArtist;
  
  // Debug log
  if (user) {
    console.log('User role check:', { userRole, isArtist, user });
  }

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout,
    loadUser,
    refreshUser,
    isAuthenticated: !!token,
    isArtist,
    isUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
