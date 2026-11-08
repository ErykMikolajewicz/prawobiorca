"""initial migration

Revision ID: 83b092221933
Revises:
Create Date: 2026-10-11 00:39:01.392509

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '83b092221933'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ENUM_NAMES = ('applicationtemplatestatus', 'regulationtype', 'regulationpreparationstatus', 'applicationgenerationstatus')


def upgrade() -> None:
    """Upgrade schema."""
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    op.create_table(
        'llm_usage',
        sa.Column('month', sa.Date(), nullable=False),
        sa.Column('input_tokens', sa.BigInteger(), server_default=sa.text('0'), nullable=False),
        sa.Column('output_tokens', sa.BigInteger(), server_default=sa.text('0'), nullable=False),
        sa.PrimaryKeyConstraint('month'),
    )
    organizations_table = op.create_table(
        'organizations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('short_name', sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'task_messages',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('attempts', sa.Integer(), server_default=sa.text('0'), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('hashed_password', sa.LargeBinary(length=60), nullable=False),
        sa.Column('username', sa.String(length=40), nullable=False),
        sa.Column('is_admin', sa.Boolean(), server_default='false', nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
    )
    op.create_table(
        'cases',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'suborganizations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('organization_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id', 'organization_id', name='uq_suborganizations_id_organization_id'),
    )
    op.create_table(
        'users_sessions',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('refresh_token_hash', sa.String(length=64), nullable=False),
        sa.Column('valid_until', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('refresh_token_hash'),
    )
    op.create_table(
        'application_templates',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('instructions', sa.Text(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('NOT_UPLOADED', 'DRAFT', 'PUBLISHED', name='applicationtemplatestatus'),
            nullable=False,
        ),
        sa.Column(
            'fields',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('suborganization_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(
            ['suborganization_id', 'organization_id'],
            ['suborganizations.id', 'suborganizations.organization_id'],
            name='fk_application_templates_suborganization_id_organization_id',
            ondelete='SET NULL (suborganization_id)',
        ),
        sa.ForeignKeyConstraint(['suborganization_id'], ['suborganizations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_application_templates_organization_id_suborganization_id',
        'application_templates',
        ['organization_id', 'suborganization_id'],
    )
    op.create_table(
        'case_documents',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('case_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('presentation_name', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('header', sa.Text(), nullable=True),
        sa.Column(
            'elements',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column('highlight', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'regulations',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('presentation_name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.String(length=1000), nullable=True),
        sa.Column('regulation_type', sa.Enum('ACT', 'DECREE', 'STATUTE', name='regulationtype'), nullable=True),
        sa.Column(
            'preparation_status',
            sa.Enum('NOT_STARTED', 'IN_PROGRESS', 'PREPARED', 'FAILED', name='regulationpreparationstatus'),
            nullable=False,
        ),
        sa.Column('organization_id', sa.UUID(), nullable=True),
        sa.Column('suborganization_id', sa.UUID(), nullable=True),
        sa.CheckConstraint(
            'suborganization_id IS NULL OR organization_id IS NOT NULL',
            name='ck_regulations_suborganization_with_organization',
        ),
        sa.CheckConstraint(
            'user_id IS NULL OR organization_id IS NULL', name='ck_regulations_private_without_organization'
        ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['suborganization_id', 'organization_id'],
            ['suborganizations.id', 'suborganizations.organization_id'],
            name='fk_regulations_suborganization_id_organization_id',
            ondelete='CASCADE',
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('id', 'user_id', name='uq_regulations_id_user_id'),
    )
    op.create_index(
        'ix_regulations_organization_id_suborganization_id',
        'regulations',
        ['organization_id', 'suborganization_id'],
    )
    op.create_table(
        'applications',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('case_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('template_id', sa.UUID(), nullable=True),
        sa.Column('template_name', sa.String(length=255), nullable=False),
        sa.Column(
            'generation_status',
            sa.Enum('IN_PROGRESS', 'GENERATED', 'FAILED', name='applicationgenerationstatus'),
            nullable=False,
        ),
        sa.Column('name', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['application_templates.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'regulations_sections',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('create_date', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('header', sa.Text(), nullable=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('section_order', sa.Integer(), nullable=False),
        sa.Column('elements', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('regulation_id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(
            ['regulation_id', 'user_id'], ['regulations.id', 'regulations.user_id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'ix_regulations_sections_regulation_id_user_id', 'regulations_sections', ['regulation_id', 'user_id']
    )
    op.create_table(
        'regulations_chunks',
        sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('vector', Vector(dim=1024), nullable=False),
        sa.Column('span_start_element', sa.Integer(), nullable=True),
        sa.Column('span_end_element', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['section_id'], ['regulations_sections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_regulations_chunks_section_id', 'regulations_chunks', ['section_id'])
    op.bulk_insert(organizations_table, [{'name': 'Politechnika Wrocławska', 'short_name': 'PWr'}])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('regulations_chunks')
    op.drop_table('regulations_sections')
    op.drop_table('applications')
    op.drop_table('regulations')
    op.drop_table('case_documents')
    op.drop_table('application_templates')
    op.drop_table('users_sessions')
    op.drop_table('suborganizations')
    op.drop_table('cases')
    op.drop_table('users')
    op.drop_table('task_messages')
    op.drop_table('organizations')
    op.drop_table('llm_usage')
    for enum_name in ENUM_NAMES:
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
    op.execute('DROP EXTENSION IF EXISTS vector')
