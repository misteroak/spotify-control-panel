import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.config import Settings, get_allowed_emails, get_settings
from app.session import create_session_token

logger = logging.getLogger(__name__)
router = APIRouter()

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


@router.get("/login")
async def google_login(settings: Settings = Depends(get_settings)):
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email",
        "access_type": "online",
        "prompt": "select_account",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/callback")
async def google_callback(
    code: str = Query(...),
    settings: Settings = Depends(get_settings),
):
    # Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            logger.error("Google token exchange failed: %s", token_resp.text)
            raise HTTPException(status_code=400, detail="Failed to exchange code")
        token_data = token_resp.json()

    # Verify the ID token and extract email
    try:
        id_info = id_token.verify_oauth2_token(
            token_data["id_token"],
            google_requests.Request(),
            settings.google_client_id,
        )
    except ValueError:
        logger.exception("ID token verification failed")
        raise HTTPException(status_code=401, detail="Invalid ID token")

    email = id_info.get("email", "")
    if email.lower() not in get_allowed_emails():
        logger.warning("Unauthorized login attempt from %s", email)
        raise HTTPException(status_code=403, detail="Access denied")

    # Set session cookie and redirect to frontend
    response = RedirectResponse(settings.frontend_url)
    session_value = create_session_token(email, settings.session_secret)
    is_local = settings.google_redirect_uri.startswith(("http://localhost", "http://127.0.0.1"))
    response.set_cookie(
        key="session",
        value=session_value,
        httponly=True,
        secure=not is_local,
        samesite="lax",
        max_age=7 * 24 * 3600,
        path="/",
    )
    return response


@router.get("/me")
async def me(request: Request):
    return {"email": request.state.user_email}


@router.post("/logout")
async def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie("session", path="/")
    return response
