from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class AccessTokenClaims:
    user_id: UUID
    session_id: UUID
    is_admin: bool


@dataclass(frozen=True)
class UserSession:
    id: UUID
    user_id: UUID
