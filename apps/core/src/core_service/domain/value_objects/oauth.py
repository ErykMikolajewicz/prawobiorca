from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AuthorizationGrant:
    client_id: UUID
    user_id: UUID
    redirect_uri: str
    code_challenge: str
    resource: str | None


@dataclass(frozen=True)
class OAuthTokenHashes:
    access_token_hash: str
    access_valid_until: datetime
    refresh_token_hash: str
    refresh_valid_until: datetime


@dataclass(frozen=True)
class OAuthTokenOwner:
    client_id: UUID
    user_id: UUID
    is_admin: bool
    resource: str | None
    access_valid_until: datetime
