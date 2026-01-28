# New Features Added

This document outlines all the new features that have been added to enhance the Spotify Clone project.

## 🎵 Music Features

### 1. Advanced Search System
- **Endpoint**: `GET /api/songs/search?q=<query>&type=<all|song|album|artist>`
- Full-text search across songs, albums, and artists
- Returns results for all types or specific type
- Case-insensitive search

### 2. Smart Filtering & Ordering
- **Enhanced Song Endpoints** with query parameters:
  - `?genre=<genre>` - Filter by genre
  - `?artist=<artist>` - Filter by artist username
  - `?album=<album>` - Filter by album title
  - `?date_from=<YYYY-MM-DD>` - Filter by release date from
  - `?date_to=<YYYY-MM-DD>` - Filter by release date to
  - `?ordering=<field>` - Sort by play_count, likes, release_date, created_at
  - `?search=<term>` - Search in title, genre, album, artist

### 3. Recently Played Tracking
- **Endpoint**: `GET /api/songs/recently_played?limit=<number>`
- Automatically tracks when users play songs
- Returns user's recently played songs in chronological order
- Default limit: 50 songs

### 4. Favorites System
- **Song Favorites**:
  - `POST /api/songs/{id}/favorite` - Add song to favorites
  - `DELETE /api/songs/{id}/favorite` - Remove from favorites
  - `GET /api/songs/favorites` - Get all favorite songs
- **Album Favorites**:
  - `POST /api/albums/{id}/favorite` - Add album to favorites
  - `DELETE /api/albums/{id}/favorite` - Remove from favorites
  - `GET /api/albums/favorites` - Get all favorite albums

### 5. Song Recommendations
- **Endpoint**: `GET /api/songs/recommendations?limit=<number>`
- Personalized recommendations based on:
  - User's favorite genres
  - Listening history
  - Popular songs in favorite genres
- Falls back to trending songs for new users

### 6. Random Discovery
- **Endpoint**: `GET /api/songs/random?limit=<number>`
- Get random songs for discovery
- Default: 10 random songs

### 7. Enhanced Trending
- **Endpoint**: `GET /api/songs/trending?limit=<number>&time_range=<all|week|month>`
- Time-based trending:
  - `all` - All-time trending (default)
  - `week` - Trending in last 7 days
  - `month` - Trending in last 30 days

### 8. File Validation
- **Audio Files**: Validates file type and size
  - Allowed: MP3, WAV, M4A, FLAC, OGG, AAC
  - Max size: 50 MB
- **Image Files**: Validates album covers and profile pictures
  - Allowed: JPG, JPEG, PNG, GIF, WEBP
  - Max size: 10 MB

## 👥 User & Social Features

### 9. Artist Following System
- **Endpoints**:
  - `GET /api/artists` - List all artists (with search)
  - `POST /api/artists/{id}/follow` - Follow an artist
  - `DELETE /api/artists/{id}/follow` - Unfollow an artist
  - `GET /api/artists/following` - Get artists user is following
  - `GET /api/artists/followers` - Get user's followers (artists only)

### 10. Artist Profiles & Statistics
- **Endpoint**: `GET /api/artists/{id}/profile`
- Returns comprehensive artist statistics:
  - Song count
  - Album count
  - Follower count
  - Total plays across all songs
  - Total likes across all songs
  - Whether current user is following

### 11. Artist Songs
- **Endpoint**: `GET /api/artists/{id}/songs`
- Get all public songs by a specific artist

## 📊 Database Models Added

### RecentlyPlayed
- Tracks when users play songs
- Unique constraint on (user, song)
- Indexed for performance

### FavoriteSong
- User's saved/favorite songs
- Unique constraint on (user, song)

### FavoriteAlbum
- User's saved/favorite albums
- Unique constraint on (user, album)

### ArtistFollow
- Follow relationship between users and artists
- Prevents users from following themselves
- Unique constraint on (user, artist)

## 🔧 Technical Improvements

### Query Optimization
- Added `select_related()` for foreign key relationships
- Added `prefetch_related()` for reverse foreign keys
- Database indexes on frequently queried fields

### Enhanced ViewSets
- Added `filter_backends` for search and ordering
- Custom queryset filtering with multiple parameters
- Better error handling and validation

## 📝 Migration Required

After pulling these changes, you need to run:

```bash
python manage.py makemigrations music
python manage.py migrate
```

This will create the new database tables for:
- RecentlyPlayed
- FavoriteSong
- FavoriteAlbum
- ArtistFollow

## 🚀 Usage Examples

### Search for songs
```bash
GET /api/songs/search?q=rock&type=song
```

### Get recommendations
```bash
GET /api/songs/recommendations?limit=20
```

### Follow an artist
```bash
POST /api/artists/{artist_id}/follow
```

### Get recently played
```bash
GET /api/songs/recently_played?limit=30
```

### Filter songs by genre
```bash
GET /api/songs?genre=Pop&ordering=-play_count
```

## ✨ Benefits

1. **Better User Experience**: Users can now discover, save, and organize their music
2. **Social Features**: Follow artists and see their statistics
3. **Personalization**: Recommendations based on listening habits
4. **Data Quality**: File validation ensures only valid files are uploaded
5. **Performance**: Optimized queries with proper indexing
6. **Discovery**: Random songs and enhanced trending help users find new music
