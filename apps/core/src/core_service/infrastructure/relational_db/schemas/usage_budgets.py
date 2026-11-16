import sqlalchemy as sqla

from core_service.infrastructure.relational_db.connection import metadata

usage_budgets_table = sqla.Table(
    "usage_budgets",
    metadata,
    sqla.Column("budget_key", sqla.String(64), primary_key=True),
    sqla.Column("day", sqla.Date, primary_key=True),
    sqla.Column("spent", sqla.Numeric(12, 4), nullable=False),
)
