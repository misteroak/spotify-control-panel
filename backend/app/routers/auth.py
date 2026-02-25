from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_allowed_emails, get_settings
from app.database import get_db
from app.models import AccountOut
from app.services import account_manager
from app.session import verify_session_token

router = APIRouter()

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_ME_URL = "https://api.spotify.com/v1/me"

SCOPES = "user-read-playback-state user-modify-playback-state user-read-currently-playing"


@router.get("/login")
async def login(request: Request, settings: Settings = Depends(get_settings)):
    # Pass session token via OAuth state so the callback can verify auth
    # even when cookie hostname differs (e.g. localhost vs 127.0.0.1)
    session_token = request.cookies.get("session", "")
    params = {
        "client_id": settings.spotify_client_id,
        "response_type": "code",
        "redirect_uri": settings.spotify_redirect_uri,
        "scope": SCOPES,
        "show_dialog": "true",  # Always show login so user can pick a different account
        "state": session_token,
    }
    return RedirectResponse(f"{SPOTIFY_AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
async def callback(
    request: Request,
    code: str = Query(...),
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    # Verify Google session before linking a Spotify account.
    # Try cookie first, fall back to OAuth state param (handles localhost/127.0.0.1 mismatch)
    session_token = request.cookies.get("session") or request.query_params.get("state", "")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    email = verify_session_token(session_token, settings.session_secret)
    if not email or email.lower() not in get_allowed_emails():
        raise HTTPException(status_code=403, detail="Forbidden")

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            SPOTIFY_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.spotify_redirect_uri,
                "client_id": settings.spotify_client_id,
                "client_secret": settings.spotify_client_secret,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange authorization code")
        token_data = token_resp.json()

        access_token = token_data["access_token"]
        refresh_token = token_data["refresh_token"]
        expires_in = token_data["expires_in"]
        token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        # Fetch user profile
        profile_resp = await client.get(
            SPOTIFY_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if profile_resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch Spotify profile: {profile_resp.status_code} {profile_resp.text}",
            )
        profile = profile_resp.json()

    await account_manager.upsert_account(
        db,
        spotify_user_id=profile["id"],
        display_name=profile.get("display_name") or profile["id"],
        access_token=access_token,
        refresh_token=refresh_token,
        token_expires_at=token_expires_at,
    )

    # Redirect back to the frontend dashboard
    return RedirectResponse(settings.frontend_url)


@router.get("/accounts", response_model=list[AccountOut])
async def list_accounts(db: AsyncSession = Depends(get_db)):
    return await account_manager.get_all_accounts(db)


@router.put("/accounts/reorder")
async def reorder_accounts(
    ordered_ids: list[int],
    db: AsyncSession = Depends(get_db),
):
    await account_manager.reorder_accounts(db, ordered_ids)
    return {"ok": True}


@router.delete("/accounts/{account_id}")
async def remove_account(account_id: int, db: AsyncSession = Depends(get_db)):
    deleted = await account_manager.delete_account(db, account_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"ok": True}
