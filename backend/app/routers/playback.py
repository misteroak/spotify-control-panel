from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PlaybackState
from app.services import account_manager, spotify

router = APIRouter()


async def _get_account(account_id: int, db: AsyncSession = Depends(get_db)):
    account = await account_manager.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("/{account_id}/state", response_model=PlaybackState)
async def get_state(
    account_id: int,
    db: AsyncSession = Depends(get_db),
):
    account = await _get_account(account_id, db)
    return await spotify.get_playback_state(db, account)


@router.put("/{account_id}/play")
async def play(account_id: int, db: AsyncSession = Depends(get_db)):
    account = await _get_account(account_id, db)
    await spotify.play(db, account)
    return {"ok": True}


@router.put("/{account_id}/pause")
async def pause(account_id: int, db: AsyncSession = Depends(get_db)):
    account = await _get_account(account_id, db)
    await spotify.pause(db, account)
    return {"ok": True}


@router.put("/{account_id}/volume")
async def volume(
    account_id: int,
    level: int = Query(..., ge=0, le=100),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_account(account_id, db)
    await spotify.set_volume(db, account, level)
    return {"ok": True}


@router.put("/{account_id}/seek")
async def seek(
    account_id: int,
    position_ms: int = Query(..., ge=0),
    db: AsyncSession = Depends(get_db),
):
    account = await _get_account(account_id, db)
    await spotify.seek(db, account, position_ms)
    return {"ok": True}


@router.post("/{account_id}/next")
async def next_track(account_id: int, db: AsyncSession = Depends(get_db)):
    account = await _get_account(account_id, db)
    await spotify.next_track(db, account)
    return {"ok": True}


@router.post("/{account_id}/previous")
async def previous_track(account_id: int, db: AsyncSession = Depends(get_db)):
    account = await _get_account(account_id, db)
    await spotify.previous_track(db, account)
    return {"ok": True}
