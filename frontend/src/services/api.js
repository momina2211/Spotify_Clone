import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});


// Add token to requests if available and handle FormData
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
    }
    // If data is FormData, remove Content-Type header to let browser set it with boundary
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type'];
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for better error logging
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'ERR_NETWORK') {
      console.error('Network Error: Backend server is not running or not accessible at', API_BASE_URL);
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => api.post('/users', data),
  login: (data) => api.post('/login', data),
  getProfile: () => api.get('/profile'),
  updateProfile: (data) => api.put('/profile', data),
};

// Songs API
export const songsAPI = {
  getAll: (params) => api.get('/songs/', { params }),
  getById: (id) => api.get(`/songs/${id}/`),
  create: (formData) => api.post('/songs/', formData),
  update: (id, data) => api.put(`/songs/${id}/`, data),
  delete: (id) => api.delete(`/songs/${id}/`),
  like: (id) => api.post(`/songs/${id}/like/`),
  unlike: (id) => api.post(`/songs/${id}/unlike/`),
  play: (id) => api.post(`/songs/${id}/play/`),
  trending: (params) => api.get('/songs/trending/', { params }),
  search: (params) => api.get('/songs/search/', { params }),
  favorites: () => api.get('/songs/favorites/'),
  addFavorite: (id) => api.post(`/songs/${id}/favorite/`),
  removeFavorite: (id) => api.delete(`/songs/${id}/favorite/`),
  recentlyPlayed: (params) => api.get('/songs/recently_played/', { params }),
  random: (params) => api.get('/songs/random/', { params }),
  recommendations: (params) => api.get('/songs/recommendations/', { params }),
};

// Albums API
export const albumsAPI = {
  getAll: (params) => api.get('/albums/', { params }),
  getById: (id) => api.get(`/albums/${id}/`),
  create: (formData) => api.post('/albums/', formData),
  getSongs: (id) => api.get(`/albums/${id}/songs/`),
  favorites: () => api.get('/albums/favorites/'),
  addFavorite: (id) => api.post(`/albums/${id}/favorite/`),
  removeFavorite: (id) => api.delete(`/albums/${id}/favorite/`),
};

// Artists API
export const artistsAPI = {
  getAll: (params) => api.get('/artists/list_artists', { params }),
  getProfile: (id) => api.get(`/artists/${id}/profile`),
  getSongs: (id) => api.get(`/artists/${id}/songs`),
  follow: (id) => api.post(`/artists/${id}/follow`),
  unfollow: (id) => api.delete(`/artists/${id}/follow`),
  following: () => api.get('/artists/following'),
  followers: () => api.get('/artists/followers'),
};

// Genres API
export const genresAPI = {
  getAll: () => api.get('/genres/'),
  create: (data) => api.post('/genres/', data),
  delete: (id) => api.delete(`/genres/${id}/`),
};

// Playlists API
export const playlistsAPI = {
  getAll: (params) => api.get('/playlists/', { params }),
  getById: (id) => api.get(`/playlists/${id}/`),
  create: (formData) => api.post('/playlists/', formData),
  update: (id, data) => api.put(`/playlists/${id}/`, data),
  delete: (id) => api.delete(`/playlists/${id}/`),
  addSong: (id, songId) => api.post(`/playlists/${id}/songs/`, { song_id: songId }),
  removeSong: (id, songId) => api.delete(`/playlists/${id}/songs/`, { data: { song_id: songId } }),
  reorder: (id, songOrders) => api.post(`/playlists/${id}/reorder/`, { song_orders: songOrders }),
};

// Subscriptions API
export const subscriptionsAPI = {
  getAll: () => api.get('/payments/subscriptions/'),
  subscribe: (planId, frontendUrl) => api.post('/payments/subscriptions/subscribe/', { 
    plan_id: planId,
    frontend_url: frontendUrl 
  }),
  cancel: () => api.post('/payments/subscriptions/cancel/'),
  resume: () => api.post('/payments/subscriptions/resume/'),
  getCurrent: () => api.get('/payments/subscriptions/current/'),
  trialEligibility: () => api.get('/payments/subscriptions/trial_eligibility/'),
};

// Student Verification API
export const studentVerificationAPI = {
  submit: (formData) => api.post('/student-verification/submit/', formData),
  getStatus: () => api.get('/student-verification/status/'),
  getHistory: () => api.get('/student-verification/history/'),
};

export default api;
