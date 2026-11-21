"""add usage tariff

Revision ID: e4a7c2d9f1b8
Revises: d9e2f7a1b6c4
Create Date: 2026-11-19 22:00:00.000000

"""
from decimal import Decimal
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e4a7c2d9f1b8'
down_revision: Union[str, Sequence[str], None] = 'd9e2f7a1b6c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    usage_tariff = op.create_table(
        'usage_tariff',
        sa.Column('id', sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column('semantic_search_price', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('application_generation_price', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('regulation_preparation_price', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('account_daily_limit', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('anonymous_ip_daily_limit', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column('anonymous_total_daily_limit', sa.Numeric(precision=12, scale=4), nullable=False),
        sa.CheckConstraint('id = 1', name='ck_usage_tariff_single_row'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.bulk_insert(
        usage_tariff,
        [
            {
                'id': 1,
                'semantic_search_price': Decimal('0.03'),
                'application_generation_price': Decimal('0.50'),
                'regulation_preparation_price': Decimal('1.00'),
                'account_daily_limit': Decimal('5.00'),
                'anonymous_ip_daily_limit': Decimal('2.00'),
                'anonymous_total_daily_limit': Decimal('50.00'),
            }
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('usage_tariff')
