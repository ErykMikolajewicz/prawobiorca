import sqlalchemy as sqla

from core_service.domain.consts import MAX_OAUTH_CLIENT_NAME_LENGTH, MAX_REDIRECT_URI_LENGTH
from core_service.infrastructure.relational_db.connection import metadata

TOKEN_HASH_LENGTH = 64

oauth_clients_table = sqla.Table(
    "oauth_clients",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime(timezone=True), server_default=sqla.text("now()"), nullable=False),
    sqla.Column("name", sqla.String(MAX_OAUTH_CLIENT_NAME_LENGTH), nullable=False),
    sqla.Column("secret_hash", sqla.String(TOKEN_HASH_LENGTH), nullable=False),
)

oauth_authorization_codes_table = sqla.Table(
    "oauth_authorization_codes",
    metadata,
    sqla.Column("code_hash", sqla.String(TOKEN_HASH_LENGTH), primary_key=True),
    sqla.Column("client_id", sqla.UUID, sqla.ForeignKey("oauth_clients.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("resource", sqla.Text),
    sqla.Column("user_id", sqla.UUID, sqla.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("redirect_uri", sqla.String(MAX_REDIRECT_URI_LENGTH), nullable=False),
    sqla.Column("code_challenge", sqla.String(128), nullable=False),
    sqla.Column("valid_until", sqla.DateTime(timezone=True), nullable=False),
)

oauth_tokens_table = sqla.Table(
    "oauth_tokens",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime(timezone=True), server_default=sqla.text("now()"), nullable=False),
    sqla.Column("client_id", sqla.UUID, sqla.ForeignKey("oauth_clients.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("resource", sqla.Text),
    sqla.Column("user_id", sqla.UUID, sqla.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("access_token_hash", sqla.String(TOKEN_HASH_LENGTH), nullable=False),
    sqla.Column("access_valid_until", sqla.DateTime(timezone=True), nullable=False),
    sqla.Column("refresh_token_hash", sqla.String(TOKEN_HASH_LENGTH), nullable=False),
    sqla.Column("refresh_valid_until", sqla.DateTime(timezone=True), nullable=False),
    sqla.UniqueConstraint("access_token_hash"),
    sqla.UniqueConstraint("refresh_token_hash"),
)
