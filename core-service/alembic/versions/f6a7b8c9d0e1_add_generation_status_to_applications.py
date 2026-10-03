"""add generation_status to applications

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-10-04 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

applicationgenerationstatus = sa.Enum("IN_PROGRESS", "GENERATED", "FAILED", name="applicationgenerationstatus")


def upgrade() -> None:
    """Upgrade schema."""
    applicationgenerationstatus.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "applications",
        sa.Column("generation_status", applicationgenerationstatus, nullable=False, server_default="GENERATED"),
    )
    with op.batch_alter_table("applications", schema=None) as batch_op:
        batch_op.alter_column("generation_status", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("applications", "generation_status")
    applicationgenerationstatus.drop(op.get_bind(), checkfirst=True)
