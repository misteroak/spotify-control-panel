from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from app.config import get_allowed_emails, get_settings
from app.session import verify_session_token

PUBLIC_PATHS = {
    "/google/login",
    "/google/callback",
    "/auth/login",
    "/auth/callback",
    "/api/health",
}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in PUBLIC_PATHS:
            return await call_next(request)

        settings = get_settings()
        session_token = request.cookies.get("session")

        if session_token:
            email = verify_session_token(session_token, settings.session_secret)
            if email and email.lower() in get_allowed_emails():
                request.state.user_email = email
                return await call_next(request)

        # API routes get a 401 JSON response
        if path.startswith(("/auth/", "/playback/", "/api/")):
            return JSONResponse(
                status_code=401,
                content={"detail": "Not authenticated"},
            )

        # Everything else (static files, pages) redirects to Google login
        return RedirectResponse("/google/login")
