from datetime import datetime
from typing import Protocol
from uuid import UUID

from src.app.dtos.user import CreateUserData
from src.app.interfaces.relational import AsyncSession
from src.domain.entities.user import User
from src.domain.value_objects.auth import UserSession
from src.domain.value_objects.users import UserPrivileges


class UsersRepository(Protocol):
    async def add(self, session: AsyncSession, create_data: CreateUserData): ...

    async def get_by_username(self, session: AsyncSession, username: str) -> User | None: ...

    async def get_user_privileges(self, session: AsyncSession, user_id: UUID) -> UserPrivileges | None: ...


class UsersSessionsRepository(Protocol):
    async def create_session(
        self, session: AsyncSession, user_id: UUID, refresh_token_hash: str, valid_until: datetime
    ) -> UUID: ...

    async def rotate_session(
        self, session: AsyncSession, old_refresh_token_hash: str, new_refresh_token_hash: str, valid_until: datetime
    ) -> UserSession | None: ...

    async def delete_session(self, session: AsyncSession, session_id: UUID) -> None: ...

    async def delete_session_by_refresh_token_hash(self, session: AsyncSession, refresh_token_hash: str) -> None: ...
