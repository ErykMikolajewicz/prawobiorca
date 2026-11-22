"""add mcp monthly limit

Revision ID: f1c3a8e5b2d7
Revises: e4a7c2d9f1b8
Create Date: 2026-11-22 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f1c3a8e5b2d7'
down_revision: Union[str, Sequence[str], None] = 'e4a7c2d9f1b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'usage_tariff',
        sa.Column('mcp_monthly_limit', sa.Numeric(precision=12, scale=4), server_default='30.00', nullable=False),
    )
    op.alter_column('usage_tariff', 'mcp_monthly_limit', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('usage_tariff', 'mcp_monthly_limit')
