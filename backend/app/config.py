from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    spotify_client_id: str
    spotify_client_secret: str
    spotify_redirect_uri: str = "http://localhost:8000/auth/callback"
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/spotify_panel"

    # Frontend URL for CORS and redirects after OAuth
    frontend_url: str = "http://localhost:5173"

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
