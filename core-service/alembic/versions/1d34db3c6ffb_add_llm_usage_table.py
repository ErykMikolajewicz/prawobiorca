"""add llm usage table

Revision ID: 1d34db3c6ffb
Revises: f6a7b8c9d0e1
Create Date: 2026-10-04 20:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "1d34db3c6ffb"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "llm_usage",
        sa.Column("month", sa.Date(), nullable=False),
        sa.Column("input_tokens", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.Column("output_tokens", sa.BigInteger(), server_default=sa.text("0"), nullable=False),
        sa.PrimaryKeyConstraint("month"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("llm_usage")
