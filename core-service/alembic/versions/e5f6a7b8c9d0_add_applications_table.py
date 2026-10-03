"""add applications table

Revision ID: e5f6a7b8c9d0
Revises: c9a2c8a70dd0
Create Date: 2026-10-04 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, Sequence[str], None] = 'c9a2c8a70dd0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

applicationtype = sa.Enum("OTHER", "DIPLOMA_DEADLINE_EXTENSION", name="applicationtype")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "applications",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("create_date", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("application_type", applicationtype, nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("applications")
    applicationtype.drop(op.get_bind(), checkfirst=True)
