# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-account Spotify control panel. FastAPI (Python) backend + React (TypeScript) frontend, deployed on GCP Cloud Run with Cloud SQL (Postgres).

Supports up to 5 Spotify accounts, each with independent playback controls (play/pause/skip/volume/seek).

## Architecture

**Backend** (`backend/`): FastAPI async app.
- `app/main.py` — entry point, CORS, static file serving, router registration
- `app/config.py` — pydantic-settings `Settings` class, loaded from `.env`
- `app/database.py` — SQLAlchemy async engine/session using asyncpg
- `app/models.py` — SQLAlchemy ORM model (`Account`) + Pydantic response schemas
- `app/routers/auth.py` — Spotify OAuth flow (`/auth/login`, `/auth/callback`, `/auth/accounts`)
- `app/routers/playback.py` — per-account playback endpoints (`/playback/{account_id}/...`)
- `app/services/spotify.py` — Spotify Web API client (httpx), handles token refresh
- `app/services/account_manager.py` — account CRUD, token persistence
- `alembic/` — async database migrations

**Frontend** (`frontend/`): React 18 + TypeScript + Vite.
- `src/api/spotify.ts` — API client wrapping all backend endpoints
- `src/hooks/usePlaybackState.ts` — polling hook (2s interval per account)
- `src/components/Dashboard.tsx` — main view, grid of AccountCards
- `src/components/AccountCard.tsx` — single account: now-playing + controls
- `src/components/PlaybackControls.tsx` — transport buttons, volume, seek
- `src/components/NowPlaying.tsx` — track info, album art, progress bar

**Key data flow**: Frontend polls `GET /playback/{id}/state` every 2s. Playback commands (play/pause/etc.) are fire-and-forget PUTs. Backend auto-refreshes expired Spotify tokens before making API calls.

## Development Commands

### Backend
```bash
cd backend
uv sync                # install dependencies into .venv
cp .env.example .env   # fill in SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, DATABASE_URL
uv run alembic upgrade head   # run migrations against local Postgres
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev            # Vite dev server on :5173, proxied to backend
npm run build          # production build to dist/
```

### Database Migrations
```bash
cd backend
uv run alembic revision --autogenerate -m "description"   # create migration
uv run alembic upgrade head                                # apply migrations
```

## Deployment (Cloud Run)

Single-container deployment via multi-stage Dockerfile. Frontend is built and served as static files by FastAPI.

```bash
# Set these for your environment
SERVICE_URL="spotify-panel-393546321908.us-east1.run.app"
CLOUDSQL_INSTANCE="PROJECT:REGION:INSTANCE"

gcloud run deploy spotify-panel \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --add-cloudsql-instances="$CLOUDSQL_INSTANCE" \
  --set-secrets="SPOTIFY_CLIENT_ID=spotify-client-id:latest,SPOTIFY_CLIENT_SECRET=spotify-client-secret:latest,DATABASE_URL=database-url:latest,GOOGLE_CLIENT_ID=google-client-id:latest,GOOGLE_CLIENT_SECRET=google-client-secret:latest,SESSION_SECRET=session-secret:latest" \
  --set-env-vars="SPOTIFY_REDIRECT_URI=https://${SERVICE_URL}/auth/callback,GOOGLE_REDIRECT_URI=https://${SERVICE_URL}/google/callback,FRONTEND_URL=https://${SERVICE_URL}"
```

**Important**: The redirect URIs must also be registered in the Spotify Developer Dashboard and Google Cloud Console OAuth credentials.

## Spotify API Details

- **Required scopes**: `user-read-playback-state`, `user-modify-playback-state`, `user-read-currently-playing`
- OAuth callback URL must be registered in the Spotify Developer Dashboard
- `show_dialog=true` is used in the auth URL so users can log into different accounts
- The backend handles 204/202/403 responses from Spotify gracefully (no active device, etc.)
