import sqlalchemy as sqla

from src.domain.entities.user import User
from src.infrastructure.relational_db.connection import mapper_registry, metadata

users_table = sqla.Table(
    "users",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime(timezone=True), server_default=sqla.text("now()"), nullable=False),
    sqla.Column("hashed_password", sqla.LargeBinary(60), nullable=False),
    sqla.Column("username", sqla.String(40), nullable=False),
    sqla.Column("is_admin", sqla.Boolean, default=False, server_default="false", nullable=False),
    sqla.UniqueConstraint("username"),
)

users_sessions_table = sqla.Table(
    "users_sessions",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime(timezone=True), server_default=sqla.text("now()"), nullable=False),
    sqla.Column("user_id", sqla.UUID, sqla.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("refresh_token_hash", sqla.String(64), nullable=False),
    sqla.Column("valid_until", sqla.DateTime(timezone=True), nullable=False),
    sqla.UniqueConstraint("refresh_token_hash"),
)


mapper_registry.map_imperatively(User, users_table, exclude_properties=["create_date", "is_admin"])
