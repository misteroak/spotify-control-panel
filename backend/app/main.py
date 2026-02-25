from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.middleware.auth import AuthMiddleware
from app.routers import auth, google_auth, playback

app = FastAPI(title="Spotify Control Panel")

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

app.include_router(google_auth.router, prefix="/google", tags=["google-auth"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(playback.router, prefix="/playback", tags=["playback"])

# Serve frontend static files in production (built React app)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
