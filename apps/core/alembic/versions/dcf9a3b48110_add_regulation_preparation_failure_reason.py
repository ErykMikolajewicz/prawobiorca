"""Add regulation preparation failure reason.

Revision ID: dcf9a3b48110
Revises: b8e209c3f704
"""
import sqlalchemy as sa
from alembic import op

revision = "dcf9a3b48110"
down_revision = "b8e209c3f704"
branch_labels = None
depends_on = None

failure_reason_enum = sa.Enum(
    "INCOMPLETE_DOCUMENT", "UNREADABLE_DOCUMENT", "PROCESSING_ERROR", name="regulationpreparationfailurereason"
)


def upgrade() -> None:
    failure_reason_enum.create(op.get_bind())
    op.add_column("regulations", sa.Column("preparation_failure_reason", failure_reason_enum, nullable=True))
    op.execute(
        "UPDATE regulations SET preparation_failure_reason = 'PROCESSING_ERROR' WHERE preparation_status = 'FAILED'"
    )


def downgrade() -> None:
    op.drop_column("regulations", "preparation_failure_reason")
    failure_reason_enum.drop(op.get_bind())
