"""add regulations sections order unique constraint

Revision ID: a4bb4eea6c1e
Revises: 4e8a1c7d2f90
Create Date: 2026-11-09 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a4bb4eea6c1e'
down_revision: Union[str, Sequence[str], None] = '4e8a1c7d2f90'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        'uq_regulations_sections_regulation_id_section_order',
        'regulations_sections',
        ['regulation_id', 'section_order'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_regulations_sections_regulation_id_section_order', 'regulations_sections', type_='unique')
