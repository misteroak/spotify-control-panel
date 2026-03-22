import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.services import account_manager, spotify

router = APIRouter()
_bearer = HTTPBearer()


def _verify_key(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    settings = get_settings()
    if not settings.public_api_key or credentials.credentials != settings.public_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")


@router.post("/stop-all", dependencies=[Depends(_verify_key)])
async def stop_all(db: AsyncSession = Depends(get_db)):
    """Pause playback on all accounts. Safe to call even if already paused."""
    accounts = await account_manager.get_all_accounts(db)
    await asyncio.gather(
        *(spotify.pause(db, account) for account in accounts),
        return_exceptions=True,  # don't fail if one account has no active device
    )
    return {"ok": True, "paused": len(accounts)}
