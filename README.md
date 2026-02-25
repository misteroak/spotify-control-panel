# Spotify Multi-Account Control Panel

I got tired of walking to each of my kids' iPads every night to turn off the podcasts they'd fallen asleep to. So I built this: a single dashboard where I can see and control playback across multiple Spotify accounts at once. One screen, a few taps, everyone's audio is off, and I can go back to the couch.

It supports up to 5 Spotify accounts, each with independent play/pause, skip, volume, and seek controls.

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- Node.js 20+
- PostgreSQL 16+ (local instance or Docker)
- A Spotify Developer app ([developer.spotify.com/dashboard](https://developer.spotify.com/dashboard))
- A Google Cloud OAuth 2.0 client ([console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials))

## 1. Create a Spotify App

1. Go to the Spotify Developer Dashboard and create a new app
2. Set the redirect URI to `http://localhost:8000/auth/callback`
3. Note your **Client ID** and **Client Secret**

## 2. Create a Google OAuth Client

1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project (or select an existing one)
2. Navigate to **APIs & Services > OAuth consent screen** and configure it — you just need an app name (e.g. "Spotify Control Panel") and your email address. Save and continue through any remaining steps
3. Navigate to **APIs & Services > Credentials**
4. Click **+ Create Credentials > OAuth client ID**
5. Set Application type to **Web application**
6. Under **Authorized redirect URIs**, add `http://localhost:8000/google/callback`
7. Click **Create** and note your **Client ID** and **Client Secret**

## 3. Start PostgreSQL

If you don't have Postgres running locally, use Docker (make sure Docker Desktop is running first):

```bash
docker run -d --name spotify-panel-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=spotify_panel \
  -p 5432:5432 \
  postgres:16
```

## 4. Backend Setup

```bash
cd backend
uv sync
```

Create your `.env` file (from the `backend/` directory):

```bash
cp .env.example .env
```

Edit `backend/.env` with your values:

```
SPOTIFY_CLIENT_ID=<your client id>
SPOTIFY_CLIENT_SECRET=<your client secret>
SPOTIFY_REDIRECT_URI=http://localhost:8000/auth/callback
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/spotify_panel

GOOGLE_CLIENT_ID=<your google client id>
GOOGLE_CLIENT_SECRET=<your google client secret>
GOOGLE_REDIRECT_URI=http://localhost:8000/google/callback
ALLOWED_EMAIL=you@gmail.com
SESSION_SECRET=<random string, 32+ characters>
```

> **Tip:** Generate a random `SESSION_SECRET` with: `openssl rand -base64 32`

Run database migrations and start the server:

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

## 5. Frontend Setup

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on http://localhost:5173 and proxies API requests to the backend.

## 6. Usage

1. Open http://localhost:5173 — you'll be redirected to sign in with Google
2. Sign in with the Google account matching `ALLOWED_EMAIL`
3. Click **"+"** to connect a Spotify account
4. Once connected, you'll see playback controls for that account
5. Repeat for additional accounts (up to 5)

Each account shows the current track, album art, and has independent play/pause/skip/volume/seek controls.

> **Note:** Spotify requires an active playback device (desktop app, mobile app, or web player) for the controls to work.

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions on deploying to Google Cloud Run.
