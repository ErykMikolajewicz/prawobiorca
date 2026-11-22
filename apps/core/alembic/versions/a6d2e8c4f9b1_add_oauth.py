"""add oauth

Revision ID: a6d2e8c4f9b1
Revises: f1c3a8e5b2d7
Create Date: 2026-11-22 13:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a6d2e8c4f9b1'
down_revision: Union[str, Sequence[str], None] = 'f1c3a8e5b2d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'oauth_clients',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('secret_hash', sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'oauth_authorization_codes',
        sa.Column('code_hash', sa.String(length=64), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('redirect_uri', sa.String(length=2000), nullable=False),
        sa.Column('code_challenge', sa.String(length=128), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['oauth_clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('code_hash'),
    )
    op.create_table(
        'oauth_tokens',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('client_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('access_token_hash', sa.String(length=64), nullable=False),
        sa.Column('access_valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.Column('refresh_token_hash', sa.String(length=64), nullable=False),
        sa.Column('refresh_valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['client_id'], ['oauth_clients.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('access_token_hash'),
        sa.UniqueConstraint('refresh_token_hash'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('oauth_tokens')
    op.drop_table('oauth_authorization_codes')
    op.drop_table('oauth_clients')
