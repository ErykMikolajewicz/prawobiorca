from dataclasses import dataclass
from uuid import UUID


@dataclass
class AccessTokenClaims:
    user_id: UUID
    session_id: UUID
    is_admin: bool


@dataclass
class UserSession:
    id: UUID
    user_id: UUID
