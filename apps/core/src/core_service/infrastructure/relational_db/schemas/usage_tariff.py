import sqlalchemy as sqla

from core_service.infrastructure.relational_db.connection import metadata

USAGE_TARIFF_ID = 1

usage_tariff_table = sqla.Table(
    "usage_tariff",
    metadata,
    sqla.Column("id", sqla.SmallInteger, primary_key=True, autoincrement=False),
    sqla.Column("semantic_search_price", sqla.Numeric(12, 4), nullable=False),
    sqla.Column("application_generation_price", sqla.Numeric(12, 4), nullable=False),
    sqla.Column("regulation_preparation_price", sqla.Numeric(12, 4), nullable=False),
    sqla.Column("account_daily_limit", sqla.Numeric(12, 4), nullable=False),
    sqla.Column("anonymous_ip_daily_limit", sqla.Numeric(12, 4), nullable=False),
    sqla.Column("anonymous_total_daily_limit", sqla.Numeric(12, 4), nullable=False),
    sqla.Column("mcp_monthly_limit", sqla.Numeric(12, 4), nullable=False),
    sqla.CheckConstraint(f"id = {USAGE_TARIFF_ID}", name="ck_usage_tariff_single_row"),
)
