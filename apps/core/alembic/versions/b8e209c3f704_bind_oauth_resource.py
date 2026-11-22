"""Bind authorization codes and tokens to the MCP resource.

Revision ID: b8e209c3f704
Revises: a6d2e8c4f9b1
"""
import sqlalchemy as sa
from alembic import op

revision = "b8e209c3f704"
down_revision = "a6d2e8c4f9b1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Existing grants have no recorded audience and require a new consent.
    op.add_column("oauth_authorization_codes", sa.Column("resource", sa.Text(), nullable=True))
    op.add_column("oauth_tokens", sa.Column("resource", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("oauth_tokens", "resource")
    op.drop_column("oauth_authorization_codes", "resource")
