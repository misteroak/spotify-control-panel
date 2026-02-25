from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Account, PlaybackState
from app.services import account_manager

SPOTIFY_API = "https://api.spotify.com/v1/me/player"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"


async def _ensure_token(db: AsyncSession, account: Account) -> str:
    """Return a valid access token, refreshing if expired."""
    if account.token_expires_at > datetime.now(timezone.utc):
        return account.access_token

    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": account.refresh_token,
                "client_id": settings.spotify_client_id,
                "client_secret": settings.spotify_client_secret,
            },
        )
        resp.raise_for_status()
        data = resp.json()

    new_expires = datetime.now(timezone.utc) + timedelta(seconds=data["expires_in"])
    await account_manager.update_tokens(
        db,
        account,
        access_token=data["access_token"],
        token_expires_at=new_expires,
        refresh_token=data.get("refresh_token"),
    )
    return data["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def get_playback_state(db: AsyncSession, account: Account) -> PlaybackState:
    token = await _ensure_token(db, account)
    async with httpx.AsyncClient() as client:
        resp = await client.get(SPOTIFY_API, headers=_headers(token))

    if resp.status_code == 204 or resp.status_code == 202:
        return PlaybackState(is_playing=False)

    resp.raise_for_status()
    data = resp.json()

    track = data.get("item")
    images = track.get("album", {}).get("images", []) if track else []

    return PlaybackState(
        is_playing=data.get("is_playing", False),
        track_name=track.get("name") if track else None,
        artist_name=", ".join(a["name"] for a in track.get("artists", [])) if track else None,
        album_name=track.get("album", {}).get("name") if track else None,
        album_image_url=images[0]["url"] if images else None,
        progress_ms=data.get("progress_ms", 0),
        duration_ms=track.get("duration_ms", 0) if track else 0,
        volume_percent=data.get("device", {}).get("volume_percent"),
        device_name=data.get("device", {}).get("name"),
    )


async def _spotify_command(
    db: AsyncSession, account: Account, method: str, path: str, **kwargs: object
) -> None:
    """Send a command to the Spotify API. 204/202/403 are treated as success."""
    token = await _ensure_token(db, account)
    async with httpx.AsyncClient() as client:
        resp = await client.request(method, f"{SPOTIFY_API}{path}", headers=_headers(token), **kwargs)
        if resp.status_code not in (204, 202, 403):
            resp.raise_for_status()


async def play(db: AsyncSession, account: Account) -> None:
    await _spotify_command(db, account, "PUT", "/play")


async def pause(db: AsyncSession, account: Account) -> None:
    await _spotify_command(db, account, "PUT", "/pause")


async def set_volume(db: AsyncSession, account: Account, volume_percent: int) -> None:
    await _spotify_command(db, account, "PUT", "/volume", params={"volume_percent": volume_percent})


async def seek(db: AsyncSession, account: Account, position_ms: int) -> None:
    await _spotify_command(db, account, "PUT", "/seek", params={"position_ms": position_ms})


async def next_track(db: AsyncSession, account: Account) -> None:
    await _spotify_command(db, account, "POST", "/next")


async def previous_track(db: AsyncSession, account: Account) -> None:
    await _spotify_command(db, account, "POST", "/previous")
