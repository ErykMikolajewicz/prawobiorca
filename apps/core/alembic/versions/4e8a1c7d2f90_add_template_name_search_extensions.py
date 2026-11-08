"""add template name search extensions

Revision ID: 4e8a1c7d2f90
Revises: 9c4d7e2b1f36
Create Date: 2026-10-31 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '4e8a1c7d2f90'
down_revision: Union[str, Sequence[str], None] = '9c4d7e2b1f36'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm')
    op.execute('CREATE EXTENSION IF NOT EXISTS unaccent')


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('DROP EXTENSION IF EXISTS unaccent')
    op.execute('DROP EXTENSION IF EXISTS pg_trgm')
