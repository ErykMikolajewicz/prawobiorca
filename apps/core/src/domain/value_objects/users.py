from dataclasses import dataclass
from uuid import UUID


@dataclass
class UserPrivileges:
    is_admin: bool


@dataclass
class Caller:
    user_id: UUID | None
    is_admin: bool = False
