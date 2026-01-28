import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Token ${token}`;
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
  getAll: (params) => api.get('/songs', { params }),
  getById: (id) => api.get(`/songs/${id}`),
  create: (formData) => api.post('/songs', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  update: (id, data) => api.put(`/songs/${id}`, data),
  delete: (id) => api.delete(`/songs/${id}`),
  like: (id) => api.post(`/songs/${id}/like`),
  unlike: (id) => api.post(`/songs/${id}/unlike`),
  play: (id) => api.post(`/songs/${id}/play`),
  trending: (params) => api.get('/songs/trending', { params }),
  search: (params) => api.get('/songs/search', { params }),
  favorites: () => api.get('/songs/favorites'),
  addFavorite: (id) => api.post(`/songs/${id}/favorite`),
  removeFavorite: (id) => api.delete(`/songs/${id}/favorite`),
  recentlyPlayed: (params) => api.get('/songs/recently_played', { params }),
  random: (params) => api.get('/songs/random', { params }),
  recommendations: (params) => api.get('/songs/recommendations', { params }),
};

// Albums API
export const albumsAPI = {
  getAll: (params) => api.get('/albums', { params }),
  getById: (id) => api.get(`/albums/${id}`),
  create: (formData) => api.post('/albums', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  getSongs: (id) => api.get(`/albums/${id}/songs`),
  favorites: () => api.get('/albums/favorites'),
  addFavorite: (id) => api.post(`/albums/${id}/favorite`),
  removeFavorite: (id) => api.delete(`/albums/${id}/favorite`),
};

// Artists API
export const artistsAPI = {
  getAll: (params) => api.get('/artists', { params }),
  getProfile: (id) => api.get(`/artists/${id}/profile`),
  getSongs: (id) => api.get(`/artists/${id}/songs`),
  follow: (id) => api.post(`/artists/${id}/follow`),
  unfollow: (id) => api.delete(`/artists/${id}/follow`),
  following: () => api.get('/artists/following'),
  followers: () => api.get('/artists/followers'),
};

// Genres API
export const genresAPI = {
  getAll: () => api.get('/genres'),
  create: (data) => api.post('/genres', data),
};

export default api;
