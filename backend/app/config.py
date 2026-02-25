import logging
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://127.0.0.1:8000/auth/callback"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/spotify_panel"

    # Frontend URL for CORS and redirects after OAuth
    frontend_url: str = "http://localhost:5173"

    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/google/callback"
    session_secret: str  # Required — generate with: openssl rand -base64 32

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _find_allowed_emails_file() -> Path | None:
    """Look for allowed_emails.txt next to this package, then at repo root."""
    candidates = [
        Path(__file__).resolve().parent.parent / "allowed_emails.txt",  # backend/allowed_emails.txt (Docker)
        Path(__file__).resolve().parent.parent.parent / "allowed_emails.txt",  # repo root (local dev)
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


@lru_cache
def get_allowed_emails() -> frozenset[str]:
    path = _find_allowed_emails_file()
    if path is None:
        logger.warning("allowed_emails.txt not found — no users will be able to log in")
        return frozenset()
    emails: set[str] = set()
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            emails.add(line.lower())
    logger.info("Loaded %d allowed email(s) from %s", len(emails), path)
    return frozenset(emails)
