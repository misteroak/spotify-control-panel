from datetime import datetime, timedelta, timezone

import jwt

SESSION_MAX_AGE = timedelta(days=7)


def create_session_token(email: str, secret: str) -> str:
    payload = {
        "email": email,
        "exp": datetime.now(timezone.utc) + SESSION_MAX_AGE,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def verify_session_token(token: str, secret: str) -> str | None:
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload.get("email")
    except jwt.PyJWTError:
        return None
