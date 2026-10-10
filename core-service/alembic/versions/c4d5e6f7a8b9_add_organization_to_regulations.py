"""add organization to regulations

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-10-10 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4d5e6f7a8b9'
down_revision: Union[str, Sequence[str], None] = 'b3c4d5e6f7a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        'uq_suborganizations_id_organization_id', 'suborganizations', ['id', 'organization_id']
    )
    op.add_column('regulations', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('regulations', sa.Column('suborganization_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'regulations_organization_id_fkey',
        'regulations',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'fk_regulations_suborganization_id_organization_id',
        'regulations',
        'suborganizations',
        ['suborganization_id', 'organization_id'],
        ['id', 'organization_id'],
        ondelete='CASCADE',
    )
    op.create_check_constraint(
        'ck_regulations_private_without_organization', 'regulations', 'user_id IS NULL OR organization_id IS NULL'
    )
    op.create_check_constraint(
        'ck_regulations_suborganization_with_organization',
        'regulations',
        'suborganization_id IS NULL OR organization_id IS NOT NULL',
    )
    op.create_index(
        'ix_regulations_organization_id_suborganization_id',
        'regulations',
        ['organization_id', 'suborganization_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_regulations_organization_id_suborganization_id', table_name='regulations')
    op.drop_constraint('ck_regulations_suborganization_with_organization', 'regulations', type_='check')
    op.drop_constraint('ck_regulations_private_without_organization', 'regulations', type_='check')
    op.drop_constraint('fk_regulations_suborganization_id_organization_id', 'regulations', type_='foreignkey')
    op.drop_constraint('regulations_organization_id_fkey', 'regulations', type_='foreignkey')
    op.drop_column('regulations', 'suborganization_id')
    op.drop_column('regulations', 'organization_id')
    op.drop_constraint('uq_suborganizations_id_organization_id', 'suborganizations', type_='unique')
