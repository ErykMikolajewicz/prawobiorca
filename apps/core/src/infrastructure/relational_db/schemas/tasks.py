import sqlalchemy as sqla

from src.infrastructure.relational_db.connection import metadata

task_messages_table = sqla.Table(
    "task_messages",
    metadata,
    sqla.Column("id", sqla.BigInteger, sqla.Identity(), primary_key=True),
    sqla.Column("message", sqla.Text, nullable=False),
    sqla.Column("attempts", sqla.Integer, server_default=sqla.text("0"), nullable=False),
    sqla.Column("locked_until", sqla.DateTime(timezone=True), nullable=True),
)
