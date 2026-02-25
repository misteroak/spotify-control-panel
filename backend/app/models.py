from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# ── SQLAlchemy ORM model ──


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    spotify_user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String)
    access_token: Mapped[str] = mapped_column(String)
    refresh_token: Mapped[str] = mapped_column(String)
    token_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


# ── Pydantic schemas ──


class AccountOut(BaseModel):
    id: int
    spotify_user_id: str
    display_name: str

    model_config = {"from_attributes": True}


class PlaybackState(BaseModel):
    is_playing: bool
    track_name: str | None = None
    artist_name: str | None = None
    album_name: str | None = None
    album_image_url: str | None = None
    progress_ms: int = 0
    duration_ms: int = 0
    volume_percent: int | None = None
    device_name: str | None = None
