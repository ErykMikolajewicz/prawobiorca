"""add regulation description generation

Revision ID: 5f2c8e1a9b47
Revises: 83b092221933
Create Date: 2026-10-25 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5f2c8e1a9b47'
down_revision: Union[str, Sequence[str], None] = '83b092221933'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

description_status_enum = sa.Enum(
    'NOT_REQUESTED', 'IN_PROGRESS', 'GENERATED', 'FAILED', name='regulationdescriptionstatus'
)


def upgrade() -> None:
    """Upgrade schema."""
    description_status_enum.create(op.get_bind())
    op.add_column('regulations', sa.Column('description_vector', Vector(dim=1024), nullable=True))
    op.add_column(
        'regulations',
        sa.Column('description_status', description_status_enum, server_default='NOT_REQUESTED', nullable=False),
    )
    op.alter_column('regulations', 'description_status', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('regulations', 'description_status')
    op.drop_column('regulations', 'description_vector')
    description_status_enum.drop(op.get_bind())
