"""add organization to application templates

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-10-11 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e6f7a8b9c0d1'
down_revision: Union[str, Sequence[str], None] = 'd5e6f7a8b9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('application_templates', sa.Column('organization_id', sa.UUID(), nullable=True))
    op.add_column('application_templates', sa.Column('suborganization_id', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'application_templates_organization_id_fkey',
        'application_templates',
        'organizations',
        ['organization_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'application_templates_suborganization_id_fkey',
        'application_templates',
        'suborganizations',
        ['suborganization_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        'fk_application_templates_suborganization_id_organization_id',
        'application_templates',
        'suborganizations',
        ['suborganization_id', 'organization_id'],
        ['id', 'organization_id'],
        ondelete='SET NULL (suborganization_id)',
    )
    op.create_index(
        'ix_application_templates_organization_id_suborganization_id',
        'application_templates',
        ['organization_id', 'suborganization_id'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_application_templates_organization_id_suborganization_id', table_name='application_templates')
    op.drop_constraint(
        'fk_application_templates_suborganization_id_organization_id', 'application_templates', type_='foreignkey'
    )
    op.drop_constraint('application_templates_suborganization_id_fkey', 'application_templates', type_='foreignkey')
    op.drop_constraint('application_templates_organization_id_fkey', 'application_templates', type_='foreignkey')
    op.drop_column('application_templates', 'suborganization_id')
    op.drop_column('application_templates', 'organization_id')
