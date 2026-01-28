# Spotify Clone - Frontend

React frontend for the Spotify Clone music streaming platform.

## Features

- 🎵 Music player with play/pause, next/previous, volume control
- 🔍 Advanced search for songs, albums, and artists
- ❤️ Favorites system for songs and albums
- ⏰ Recently played songs tracking
- 👥 Artist following and profiles
- 📊 Trending songs with time-based filters
- 🎨 Modern, responsive UI with Tailwind CSS

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env` file (or update the existing one):
```
VITE_API_URL=http://localhost:8000/api
```

3. Start the development server:
```bash
npm run dev
```

The app will be available at `http://localhost:5173`

## Build for Production

```bash
npm run build
```

## API Integration

The frontend integrates with the Django REST API backend. Make sure the backend is running on `http://localhost:8000` (or update the `VITE_API_URL` in `.env`).

## Tech Stack

- React 18
- Vite
- React Router DOM
- Axios
- Tailwind CSS
- Heroicons
