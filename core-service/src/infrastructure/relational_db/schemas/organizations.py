import sqlalchemy as sqla

from src.infrastructure.relational_db.connection import metadata
from src.shared.consts import MAX_ORGANIZATION_NAME_LENGTH, MAX_ORGANIZATION_SHORT_NAME_LENGTH

organizations_table = sqla.Table(
    "organizations",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime, server_default=sqla.text("now()"), nullable=False),
    sqla.Column("name", sqla.String(MAX_ORGANIZATION_NAME_LENGTH), nullable=False),
    sqla.Column("short_name", sqla.String(MAX_ORGANIZATION_SHORT_NAME_LENGTH), nullable=False),
)

suborganizations_table = sqla.Table(
    "suborganizations",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime, server_default=sqla.text("now()"), nullable=False),
    sqla.Column("organization_id", sqla.UUID, sqla.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("name", sqla.String(MAX_ORGANIZATION_NAME_LENGTH), nullable=False),
)
