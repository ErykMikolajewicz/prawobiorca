from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserPrivileges:
    is_admin: bool


@dataclass(frozen=True)
class Caller:
    user_id: UUID | None
    is_admin: bool = False
