from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Account


async def get_all_accounts(db: AsyncSession) -> list[Account]:
    result = await db.execute(select(Account).order_by(Account.sort_order))
    return result.scalars().all()


async def reorder_accounts(db: AsyncSession, ordered_ids: list[int]) -> None:
    for position, account_id in enumerate(ordered_ids):
        account = await db.get(Account, account_id)
        if account:
            account.sort_order = position
    await db.commit()


async def get_account(db: AsyncSession, account_id: int) -> Account | None:
    return await db.get(Account, account_id)


async def get_account_by_spotify_id(db: AsyncSession, spotify_user_id: str) -> Account | None:
    result = await db.execute(
        select(Account).where(Account.spotify_user_id == spotify_user_id)
    )
    return result.scalar_one_or_none()


async def upsert_account(
    db: AsyncSession,
    spotify_user_id: str,
    display_name: str,
    access_token: str,
    refresh_token: str,
    token_expires_at: datetime,
) -> Account:
    account = await get_account_by_spotify_id(db, spotify_user_id)
    if account:
        account.display_name = display_name
        account.access_token = access_token
        account.refresh_token = refresh_token
        account.token_expires_at = token_expires_at
    else:
        account = Account(
            spotify_user_id=spotify_user_id,
            display_name=display_name,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
        )
        db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def delete_account(db: AsyncSession, account_id: int) -> bool:
    account = await db.get(Account, account_id)
    if not account:
        return False
    await db.delete(account)
    await db.commit()
    return True


async def update_tokens(
    db: AsyncSession,
    account: Account,
    access_token: str,
    token_expires_at: datetime,
    refresh_token: str | None = None,
) -> None:
    account.access_token = access_token
    account.token_expires_at = token_expires_at
    if refresh_token:
        account.refresh_token = refresh_token
    await db.commit()
