"""change create_date to timestamptz

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-10-10 23:50:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd5e6f7a8b9c0'
down_revision: Union[str, Sequence[str], None] = 'c4d5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = (
    'applications',
    'application_templates',
    'cases',
    'case_documents',
    'organizations',
    'suborganizations',
    'regulations',
    'regulations_sections',
    'users',
    'users_sessions',
)


def upgrade() -> None:
    """Upgrade schema."""
    for table in TABLES:
        op.alter_column(
            table,
            'create_date',
            type_=sa.DateTime(timezone=True),
            existing_type=sa.DateTime(),
            existing_nullable=False,
            existing_server_default=sa.text('now()'),
            postgresql_using="create_date AT TIME ZONE 'UTC'",
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in TABLES:
        op.alter_column(
            table,
            'create_date',
            type_=sa.DateTime(),
            existing_type=sa.DateTime(timezone=True),
            existing_nullable=False,
            existing_server_default=sa.text('now()'),
            postgresql_using="create_date AT TIME ZONE 'UTC'",
        )
