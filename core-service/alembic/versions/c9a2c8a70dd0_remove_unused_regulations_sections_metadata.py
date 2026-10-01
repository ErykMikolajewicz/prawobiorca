"""remove unused regulations sections metadata

Revision ID: c9a2c8a70dd0
Revises: d4e5f6a7b8c9
Create Date: 2026-10-01 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c9a2c8a70dd0'
down_revision: Union[str, Sequence[str], None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('regulations_sections', 'unit_type')
    op.drop_column('regulations_sections', 'unit_number')
    op.drop_column('regulations_sections', 'unit_path')
    op.alter_column(
        'regulations_sections',
        'elements',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=False,
    )
    op.drop_column('regulations_chunks', 'span_start_offset')
    op.drop_column('regulations_chunks', 'span_end_offset')


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column('regulations_chunks', sa.Column('span_end_offset', sa.Integer(), nullable=True))
    op.add_column('regulations_chunks', sa.Column('span_start_offset', sa.Integer(), nullable=True))
    op.alter_column(
        'regulations_sections',
        'elements',
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
        nullable=True,
    )
    op.add_column('regulations_sections', sa.Column('unit_path', sa.ARRAY(sa.Text()), nullable=True))
    op.add_column('regulations_sections', sa.Column('unit_number', sa.String(length=16), nullable=True))
    op.add_column('regulations_sections', sa.Column('unit_type', sa.String(length=32), nullable=True))
