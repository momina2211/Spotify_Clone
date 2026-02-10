# Spotify Clone

A full-stack music streaming platform built with Django REST Framework and React, featuring real-time playback synchronization, subscription management, and AI-powered playlist generation.

## Project DNA

### Tech Stack

**Backend:**
- Django 5.2.11 (Python 3.11)
- Django REST Framework 3.16.1
- PostgreSQL (via dj-stripe integration)
- Redis 7.1.0 (caching & Celery broker)
- Celery 5.6.2 (background tasks)
- Django Channels 4.3.2 (WebSocket support)
- Stripe 14.3.0 (payment processing)
- Librosa 0.11.0 (audio analysis)
- OpenAI 2.17.0 (AI features)

**Frontend:**
- React 18
- Vite
- React Router DOM
- Axios
- Tailwind CSS
- Heroicons

### Core Architectural Patterns

1. **RESTful API Design**: ViewSets with custom actions for complex operations
2. **Token Authentication**: Token-based auth for API access
3. **WebSocket Real-time**: Django Channels for synchronized playback rooms
4. **Background Processing**: Celery tasks for audio analysis and metadata enrichment
5. **Base Class Inheritance**: `StripeBaseMixin` pattern for payment operations (see `payments/base_views.py`)

### Primary Goals

- Enable artists to upload and manage their music
- Provide subscription-based premium features
- Support real-time collaborative listening rooms
- Generate AI-powered playlists based on user preferences
- Analyze audio features for intelligent music recommendations

## Installation

### Prerequisites

- Python 3.11
- Node.js 18+
- PostgreSQL (optional, SQLite used by default)
- Redis (for Celery and caching)
- FFmpeg (for audio processing)

### Backend Setup

1. **Clone the repository:**
```bash
git clone <repository-url>
cd Spotify_Clone
```

2. **Install Python dependencies:**
```bash
pip install pipenv
pipenv install
pipenv shell
```

3. **Install system dependencies:**
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg redis-server

# macOS
brew install ffmpeg redis
```

4. **Configure environment variables:**
Create a `.env` file in the project root:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
STRIPE_SECRET_KEY=sk_test_...
DJSTRIPE_WEBHOOK_SECRET=whsec_...
OPENAI_API_KEY=sk-...
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/0
```

5. **Run migrations:**
```bash
python manage.py migrate
```

6. **Create superuser:**
```bash
python manage.py createsuperuser
```

7. **Start development server:**
```bash
python manage.py runserver
```

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend
```

2. **Install dependencies:**
```bash
npm install
```

3. **Configure API URL:**
Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000/api
```

4. **Start development server:**
```bash
npm run dev
```

## Configuration

### Django Settings

Key configuration files:
- `Spotify_Clone/settings.py` - Main Django settings
- `.env` - Environment variables (not committed to git)

### Media Storage

By default, media files are stored in `media/` directory:
- Songs: `media/songs/`
- Album covers: `media/album_covers/`
- Profile pictures: `media/profile_pics/`

For production, configure `DEFAULT_FILE_STORAGE` to use S3 (boto3 is already installed).

### Celery Configuration

Celery is configured in `Spotify_Clone/celery.py`. Ensure Redis is running:
```bash
redis-server
celery -A Spotify_Clone worker --loglevel=info
```

## Usage

### API Endpoints

Base URL: `http://localhost:8000/api`

**Authentication:**
- Obtain token: `POST /api/auth/token/`
- Include in headers: `Authorization: Token <your-token>`

**Key Endpoints:**
- Songs: `/api/music/songs/`
- Albums: `/api/music/albums/`
- Playlists: `/api/music/playlists/`
- Subscriptions: `/api/payments/subscriptions/`
- YouTube Import: `/api/music/songs/import_from_youtube/` (see [YouTube Integration Guide](./docs/YOUTUBE_INTEGRATION.md))

### Common Workflows

**Artist Upload Flow:**
1. Authenticate as artist user
2. `POST /api/music/songs/` with audio file
3. Background tasks analyze audio and enrich metadata
4. Song appears in library after processing

**Subscription Flow:**
1. `GET /api/payments/subscriptions/` - View available plans
2. `POST /api/payments/subscriptions/subscribe/` - Create checkout session
3. Complete payment via Stripe
4. Webhook updates subscription status

## Common Pitfalls

### 1. Missing FFmpeg
**Symptom:** Audio analysis tasks fail silently
**Solution:** Install FFmpeg system-wide: `sudo apt-get install ffmpeg`

### 2. Redis Not Running
**Symptom:** Celery tasks queue but never execute
**Solution:** Start Redis: `redis-server` and verify with `redis-cli ping`

### 3. CORS Errors in Development
**Symptom:** Frontend can't connect to API
**Solution:** Ensure `CORS_ALLOWED_ORIGINS` includes `http://localhost:5173` in settings.py

### 4. Stripe Webhook Failures
**Symptom:** Subscriptions created but not activated
**Solution:** Use Stripe CLI for local testing: `stripe listen --forward-to localhost:8000/api/payments/webhooks/`

### 5. Audio File Upload Size Limits
**Symptom:** Large files fail to upload
**Solution:** Increase `DATA_UPLOAD_MAX_MEMORY_SIZE` and `FILE_UPLOAD_MAX_MEMORY_SIZE` in settings.py

## Project Structure

```
Spotify_Clone/
├── music/                 # Music app (songs, albums, playlists)
│   ├── models.py         # Song, Album, Genre, Playlist models
│   ├── viewsets.py       # REST API endpoints
│   ├── serializers.py    # API serialization
│   ├── tasks.py          # Celery background tasks
│   └── utils.py          # Helper functions
├── payments/              # Subscription management
│   ├── views.py          # SubscriptionViewSet
│   ├── base_views.py     # StripeBaseMixin (shared logic)
│   └── webhooks.py       # Stripe webhook handlers
├── users/                 # User management
│   ├── models.py         # User, UserProfile models
│   └── views.py          # Authentication views
├── frontend/              # React application
│   └── src/
│       ├── components/   # React components
│       ├── pages/        # Page components
│       └── services/     # API client
└── Spotify_Clone/         # Django project settings
    ├── settings.py       # Main configuration
    └── urls.py           # URL routing
```

## Development

### Running Tests
```bash
python manage.py test
```

### Code Quality
- Follow PEP 8 for Python code
- Use ESLint for JavaScript/React
- Run `black` for Python formatting (if configured)

### Database Migrations
```bash
# Create migration
python manage.py makemigrations

# Apply migration
python manage.py migrate
```

