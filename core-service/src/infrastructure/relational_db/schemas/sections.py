import sqlalchemy as sqla
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from src.infrastructure.relational_db.connection import metadata
from src.shared.consts import VECTOR_LENGTH

regulations_sections_table = sqla.Table(
    "regulations_sections",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime, server_default=sqla.text("now()"), nullable=False),
    sqla.Column("header", sqla.Text, nullable=True),
    sqla.Column("text", sqla.Text, nullable=False),
    sqla.Column("section_order", sqla.Integer, nullable=False),
    sqla.Column("elements", postgresql.JSONB(astext_type=sqla.Text()), nullable=False),
    sqla.Column("regulation_id", sqla.UUID, nullable=False),
    sqla.Column("user_id", sqla.UUID, nullable=True),
    sqla.ForeignKeyConstraint(
        ["regulation_id", "user_id"], ["regulations.id", "regulations.user_id"], ondelete="CASCADE"
    ),
    sqla.Index("ix_regulations_sections_regulation_id_user_id", "regulation_id", "user_id"),
)

regulations_chunks_table = sqla.Table(
    "regulations_chunks",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column(
        "section_id",
        sqla.UUID,
        sqla.ForeignKey("regulations_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    ),
    sqla.Column("chunk_index", sqla.Integer, nullable=False),
    sqla.Column("text", sqla.Text, nullable=False),
    sqla.Column("vector", Vector(VECTOR_LENGTH), nullable=False),
    sqla.Column("span_start_element", sqla.Integer, nullable=True),
    sqla.Column("span_end_element", sqla.Integer, nullable=True),
)
