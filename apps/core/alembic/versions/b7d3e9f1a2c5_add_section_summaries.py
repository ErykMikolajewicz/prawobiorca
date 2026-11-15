"""add section summaries

Revision ID: b7d3e9f1a2c5
Revises: a4bb4eea6c1e
Create Date: 2026-11-15 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b7d3e9f1a2c5'
down_revision: Union[str, Sequence[str], None] = 'a4bb4eea6c1e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

description_status_enum = postgresql.ENUM(
    'NOT_REQUESTED', 'IN_PROGRESS', 'GENERATED', 'FAILED', name='regulationdescriptionstatus', create_type=False
)


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('regulations_sections', sa.Column('summary_label', sa.String(length=64), nullable=True))
    op.add_column('regulations_sections', sa.Column('summary', sa.String(length=500), nullable=True))
    op.add_column(
        'regulations',
        sa.Column('section_summaries_status', description_status_enum, server_default='NOT_REQUESTED', nullable=False),
    )
    op.alter_column('regulations', 'section_summaries_status', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('regulations', 'section_summaries_status')
    op.drop_column('regulations_sections', 'summary')
    op.drop_column('regulations_sections', 'summary_label')
