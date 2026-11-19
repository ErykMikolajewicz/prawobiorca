"""update pgvector to 0.8.7

Revision ID: d9e2f7a1b6c4
Revises: c8f1a6d4e2b3
Create Date: 2026-11-19 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

revision: str = 'd9e2f7a1b6c4'
down_revision: Union[str, Sequence[str], None] = 'c8f1a6d4e2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER EXTENSION vector UPDATE TO '0.8.7'")


def downgrade() -> None:
    pass
