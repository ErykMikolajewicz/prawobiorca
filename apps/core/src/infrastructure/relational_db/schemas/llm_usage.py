import sqlalchemy as sqla

from src.infrastructure.relational_db.connection import metadata

llm_usage_table = sqla.Table(
    "llm_usage",
    metadata,
    sqla.Column("month", sqla.Date, primary_key=True),
    sqla.Column("input_tokens", sqla.BigInteger, server_default=sqla.text("0"), nullable=False),
    sqla.Column("output_tokens", sqla.BigInteger, server_default=sqla.text("0"), nullable=False),
)
