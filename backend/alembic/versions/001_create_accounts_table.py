"""Create accounts table

Revision ID: 001
Revises:
Create Date: 2026-02-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("spotify_user_id", sa.String(), nullable=False, unique=True),
        sa.Column("display_name", sa.String(), nullable=False),
        sa.Column("access_token", sa.String(), nullable=False),
        sa.Column("refresh_token", sa.String(), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_accounts_spotify_user_id", "accounts", ["spotify_user_id"])


def downgrade() -> None:
    op.drop_index("ix_accounts_spotify_user_id")
    op.drop_table("accounts")
