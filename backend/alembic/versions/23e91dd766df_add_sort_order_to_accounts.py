"""add sort_order to accounts

Revision ID: 23e91dd766df
Revises: 001
Create Date: 2026-02-25 15:37:37.785979
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23e91dd766df'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('accounts', sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False))


def downgrade() -> None:
    op.drop_column('accounts', 'sort_order')
