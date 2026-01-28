# Spotify Clone - Full-Stack Music Streaming Platform Backend

## Project Overview

A comprehensive, production-ready music streaming platform backend built with Django REST Framework, replicating core features of Spotify. This RESTful API provides complete functionality for music management, user authentication, subscription handling, and payment processing.

## Key Features

### 🎵 Music Management System
- **Song Management**: Upload, manage, and stream audio files with full metadata support
  - Track play counts and user likes
  - Public/private visibility controls
  - Genre and album categorization
  - Duration and release date tracking
  - Trending songs algorithm based on play counts and likes (with time range filters)
  - **Advanced Search**: Full-text search across songs, albums, artists, and genres
  - **Filtering & Sorting**: Filter by genre, artist, album, date range with multiple sort options
  - **File Validation**: Audio file type and size validation (MP3, WAV, M4A, FLAC, OGG, AAC up to 50MB)
  - **Random Songs**: Get random song recommendations
  - **Recommendations**: AI-like recommendations based on user's listening history and favorite genres
- **Album Management**: Create albums with cover images and release dates
  - Image validation for album covers
  - Get all songs in an album
  - Album search and filtering
- **Genre System**: Dynamic genre creation and categorization
- **Audio Storage**: AWS S3 integration for scalable audio file storage
- **Content Visibility**: Artists can control song visibility (public/private)
- **Recently Played**: Automatic tracking of user's recently played songs
- **Favorites System**: Save favorite songs and albums to personal library

### 👥 User Management & Authentication
- **Role-Based Access Control**: Distinguishes between regular users and artists
- **Token-Based Authentication**: Secure API access using Django REST Framework tokens
- **User Profiles**: Comprehensive profile system with:
  - Profile picture uploads
  - Subscription status tracking
  - Audio quality preferences
  - Offline mode settings
- **Custom User Model**: UUID-based user identification for enhanced security
- **Artist Following System**: Follow/unfollow artists with follower counts
- **Artist Profiles**: Detailed artist profiles with statistics:
  - Song count, album count, follower count
  - Total plays and likes across all songs
  - List of all songs by artist
- **Social Features**: View following list, followers list, and artist discovery

### 💳 Subscription & Payment System
- **Multiple Subscription Tiers** (models and feature logic implemented):
  - **Free Plan**: Basic features with ads and limited skips
  - **Premium Individual**: Ad-free, high-quality audio, unlimited skips, offline mode
  - **Premium Duo**: Shared plan for two users
  - **Premium Family**: Up to 6 family members (parental controls mentioned in features)
  - **Premium Student**: Discounted plan (student verification fields exist)
- **Stripe Integration**: Payment processing code with dj-stripe
  - Subscription creation and management endpoints (code exists in payments/views.py)
  - Subscription cancellation with period-end handling
  - Stripe customer and subscription model integration
  - Webhook secret configured (webhook handler not implemented)
  - FREE_TRIAL_DAYS constant defined (30 days) but not actively used in subscription flow
- **Feature Gating**: Subscription-based feature access logic:
  - Audio quality (Low/Medium/High: 96/160/320 kbps)
  - Offline download capability
  - Ad-free experience
  - Skip limits (6/hour for free, unlimited for premium)
  - Family plan member management fields
- **Note**: Payment endpoints are currently commented out in main urls.py but fully implemented in code

### 🔐 Security & Permissions
- **Custom Permission System**: `IsArtistOrReadOnly` - Artists can create/modify content, users can only read
- **Content Ownership**: Artists can only modify their own songs
- **CORS Configuration**: Configurable cross-origin resource sharing
- **Password Validation**: Django's built-in password validators
- **Secure File Uploads**: Validated file uploads with size limits

### 📊 API Features
- **RESTful Design**: Clean, intuitive API endpoints following REST principles
- **ViewSets & Routers**: Efficient CRUD operations using Django REST Framework
- **Custom Actions**: Specialized endpoints for:
  - Song likes/unlikes
  - Play count tracking with recently played history
  - Trending songs retrieval (with time range: all/week/month)
  - Advanced search (songs, albums, artists)
  - Favorites management (songs and albums)
  - Recently played songs
  - Song recommendations
  - Random song discovery
  - Artist following/unfollowing
  - Artist profile and statistics
- **Pagination**: Built-in pagination support for large datasets
- **Filtering & Querying**: Advanced queryset filtering with:
  - Search filters (title, genre, artist, album)
  - Ordering (play count, likes, release date, created date)
  - Date range filtering
  - Genre/artist/album filtering
- **Database Optimization**: Select_related and prefetch_related for efficient queries

## Technical Stack

### Backend Framework
- **Django 5.1.6**: Modern Python web framework
- **Django REST Framework**: Powerful toolkit for building Web APIs
- **Python 3.11**: Latest Python features and performance improvements

### Database
- **PostgreSQL**: Production-ready relational database (with SQLite fallback for development)
- **UUID Primary Keys**: Enhanced security and distributed system compatibility
- **Django Migrations**: Version-controlled database schema management

### Third-Party Integrations
- **AWS S3 (boto3)**: Scalable cloud storage for audio files and media
- **Stripe (dj-stripe)**: Complete payment processing and subscription management
- **Django CORS Headers**: Cross-origin request handling
- **Django Debug Toolbar**: Development debugging tools

### Development Tools
- **Pipenv**: Dependency management and virtual environment
- **python-dotenv**: Environment variable management
- **Pillow**: Image processing for album covers and profile pictures

## Architecture Highlights

### Model Design
- **UUIDModel Base Class**: Abstract base model with UUID primary keys and timestamps
- **Normalized Database Schema**: Proper foreign key relationships and data integrity
- **Flexible Content Model**: Support for user-generated content with ownership tracking

### API Design Patterns
- **ViewSet-Based Views**: Efficient CRUD operations with minimal code
- **Serializer Validation**: Comprehensive data validation and transformation
- **Custom Actions**: Extendable endpoints for specialized operations
- **Permission Classes**: Reusable permission logic

### Business Logic
- **Subscription Feature Management**: Automatic feature updates based on subscription tier
- **Content Visibility Logic**: Smart filtering based on user roles and content ownership
- **Trending Algorithm**: Play count and likes-based content ranking

## Project Structure

```
Spotify_Clone/
├── music/              # Music content management app
│   ├── models.py      # Song, Album, Genre, SongLike models
│   ├── viewsets.py    # API endpoints for music operations
│   ├── serializers.py # Data serialization
│   ├── permissions.py # Custom permission classes
│   └── utils.py       # S3 upload and helper functions
├── users/             # User management app
│   ├── models.py      # User and UserProfile models
│   ├── views.py       # Authentication and profile endpoints
│   └── serializers.py # User data serialization
├── payments/          # Subscription and payment app
│   ├── models.py      # SubscriptionPlan model
│   └── views.py       # Stripe integration endpoints
└── Spotify_Clone/     # Project configuration
    ├── settings.py    # Django settings with AWS/Stripe config
    └── urls.py        # URL routing
```

## API Endpoints

### Authentication
- `POST /api/users` - User registration
- `POST /api/login` - User login (returns auth token)
- `GET/PUT /api/profile` - User profile management

### Music
- `GET/POST /api/songs` - List/create songs (with search, filter, ordering)
- `GET/PUT/DELETE /api/songs/{id}` - Song detail operations
- `POST /api/songs/{id}/like` - Like a song
- `POST /api/songs/{id}/unlike` - Unlike a song
- `POST /api/songs/{id}/play` - Track play count (auto-tracks recently played)
- `POST/DELETE /api/songs/{id}/favorite` - Add/remove from favorites
- `GET /api/songs/trending` - Get trending songs (with time_range: all/week/month)
- `GET /api/songs/search` - Advanced search (songs, albums, artists)
- `GET /api/songs/favorites` - Get user's favorite songs
- `GET /api/songs/recently_played` - Get recently played songs
- `GET /api/songs/random` - Get random songs
- `GET /api/songs/recommendations` - Get personalized recommendations
- `GET/POST /api/genres` - Genre management
- `GET/POST /api/albums` - Album management (with search and filtering)
- `POST/DELETE /api/albums/{id}/favorite` - Add/remove album from favorites
- `GET /api/albums/{id}/songs` - Get all songs in an album
- `GET /api/albums/favorites` - Get user's favorite albums

### Subscriptions
- **Note**: Payment endpoints exist in `payments/views.py` but are currently commented out in main `urls.py`
- Code includes: `GET /api/subscriptions` (list plans), `POST /api/subscriptions/subscribe` (create), `POST /api/subscriptions/cancel` (cancel)

### Artists & Social
- `GET /api/artists` - List all artists (with search)
- `POST/DELETE /api/artists/{id}/follow` - Follow/unfollow an artist
- `GET /api/artists/following` - Get artists user is following
- `GET /api/artists/followers` - Get user's followers (artists only)
- `GET /api/artists/{id}/profile` - Get artist profile with statistics
- `GET /api/artists/{id}/songs` - Get all songs by an artist

## Key Achievements

✅ **Scalable Architecture**: Designed for horizontal scaling with cloud storage integration  
✅ **Production-Ready**: Includes error handling, validation, and security best practices  
✅ **Payment Integration**: Stripe integration code implemented (endpoints currently disabled in URL routing)  
✅ **Role-Based Access**: Sophisticated permission system for multi-role user management  
✅ **Content Management**: Full CRUD operations with ownership and visibility controls  
✅ **Cloud Storage**: AWS S3 integration for scalable media file handling  
✅ **RESTful API**: Clean, intuitive API design following industry standards  

## Development Notes

- Environment variables required for AWS S3 and Stripe configuration
- Supports both PostgreSQL (production) and SQLite (development)
- CORS configured for frontend integration
- Debug toolbar enabled in development mode
- Token authentication for API security

## Recently Added Features

✅ **Advanced Search System**: Full-text search across songs, albums, and artists  
✅ **Smart Filtering**: Filter by genre, artist, album, date range with multiple sort options  
✅ **Favorites Library**: Save favorite songs and albums to personal library  
✅ **Recently Played**: Automatic tracking of listening history  
✅ **Song Recommendations**: Personalized recommendations based on listening patterns  
✅ **Artist Following**: Follow/unfollow artists with social features  
✅ **File Validation**: Comprehensive audio and image file validation  
✅ **Enhanced Trending**: Time-based trending (all time, week, month)  
✅ **Random Discovery**: Random song discovery endpoint  
✅ **Artist Statistics**: Detailed artist profiles with play counts, likes, followers  

## Future Enhancements

- Playlist management system (create, edit, share playlists)
- Comments and reviews on songs/albums
- Advanced recommendation engine with machine learning
- Analytics dashboard for artists (detailed insights)
- WebSocket support for real-time features (live play counts, notifications)
- Advanced audio streaming with HTTP range requests
- Collaborative playlists
- Radio stations based on genres/artists
- Lyrics integration
- Podcast support
- Social sharing features

---

**Technologies**: Django, Django REST Framework, PostgreSQL, AWS S3, Stripe, Python  
**Architecture**: RESTful API, Microservices-ready, Cloud-native  
**Status**: Production-ready backend API
