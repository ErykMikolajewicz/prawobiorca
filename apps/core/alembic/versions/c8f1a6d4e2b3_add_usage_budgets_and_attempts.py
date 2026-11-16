"""add usage budgets and attempts

Revision ID: c8f1a6d4e2b3
Revises: b7d3e9f1a2c5
Create Date: 2026-11-16 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c8f1a6d4e2b3'
down_revision: Union[str, Sequence[str], None] = 'b7d3e9f1a2c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'usage_budgets',
        sa.Column('budget_key', sa.String(length=64), nullable=False),
        sa.Column('day', sa.Date(), nullable=False),
        sa.Column('spent', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.PrimaryKeyConstraint('budget_key', 'day'),
    )
    op.create_table(
        'attempts',
        sa.Column('key', sa.String(length=128), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('count', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('key', 'window_start'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('attempts')
    op.drop_table('usage_budgets')
