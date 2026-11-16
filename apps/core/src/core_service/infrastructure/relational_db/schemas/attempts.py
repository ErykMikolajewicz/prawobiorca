import sqlalchemy as sqla

from core_service.infrastructure.relational_db.connection import metadata

attempts_table = sqla.Table(
    "attempts",
    metadata,
    sqla.Column("key", sqla.String(128), primary_key=True),
    sqla.Column("window_start", sqla.DateTime(timezone=True), primary_key=True),
    sqla.Column("expires_at", sqla.DateTime(timezone=True), nullable=False),
    sqla.Column("count", sqla.Integer, nullable=False),
)
