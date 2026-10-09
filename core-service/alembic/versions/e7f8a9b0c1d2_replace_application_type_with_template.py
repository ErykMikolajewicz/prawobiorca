"""replace application type with template

Revision ID: e7f8a9b0c1d2
Revises: c3d4e5f6a7b8
Create Date: 2026-10-07 12:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7f8a9b0c1d2"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

applicationtype = sa.Enum("OTHER", "DIPLOMA_DEADLINE_EXTENSION", name="applicationtype")


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("applications", sa.Column("template_id", sa.UUID(), nullable=True))
    op.create_foreign_key(
        "applications_template_id_fkey",
        "applications",
        "application_templates",
        ["template_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column("applications", sa.Column("template_name", sa.String(length=255), nullable=True))
    op.execute(
        """
        UPDATE applications
        SET template_name = CASE application_type
            WHEN 'DIPLOMA_DEADLINE_EXTENSION' THEN 'Przedłużenie terminu złożenia pracy dyplomowej'
            ELSE 'Inny'
        END
        """
    )
    op.alter_column("applications", "template_name", nullable=False)
    op.drop_column("applications", "application_type")
    applicationtype.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """Downgrade schema."""
    applicationtype.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "applications", sa.Column("application_type", applicationtype, server_default="OTHER", nullable=False)
    )
    op.alter_column("applications", "application_type", server_default=None)
    op.drop_column("applications", "template_name")
    op.drop_constraint("applications_template_id_fkey", "applications", type_="foreignkey")
    op.drop_column("applications", "template_id")
