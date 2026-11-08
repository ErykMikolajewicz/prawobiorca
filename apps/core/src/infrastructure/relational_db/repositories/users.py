from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dtos.user import CreateUserData
from src.domain.entities.user import User
from src.domain.value_objects.auth import UserSession
from src.domain.value_objects.users import UserPrivileges
from src.infrastructure.relational_db.schemas.users import users_sessions_table, users_table
from src.shared.exceptions import ObjectExists


class UsersRepository:
    @staticmethod
    async def add(session: AsyncSession, create_data: CreateUserData):
        statement = insert(User).values(**asdict(create_data))
        try:
            await session.execute(statement)
        except IntegrityError:
            raise ObjectExists

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> User | None:
        statement = select(User).where(users_table.c.username == username)
        user = await session.scalar(statement)

        return user

    @staticmethod
    async def get_user_privileges(session: AsyncSession, user_id: UUID) -> UserPrivileges | None:
        statement = select(users_table.c.is_admin).where(users_table.c.id == user_id)

        result = await session.execute(statement)
        is_admin = result.scalar_one_or_none()
        if is_admin is None:
            return None

        user_privileges = UserPrivileges(is_admin=is_admin)

        return user_privileges


class UsersSessionsRepository:
    @staticmethod
    async def create_session(
        session: AsyncSession, user_id: UUID, refresh_token_hash: str, valid_until: datetime
    ) -> UUID:
        statement = (
            insert(users_sessions_table)
            .values(user_id=user_id, refresh_token_hash=refresh_token_hash, valid_until=valid_until)
            .returning(users_sessions_table.c.id)
        )
        result = await session.execute(statement)

        return result.scalar_one()

    @staticmethod
    async def rotate_session(
        session: AsyncSession, old_refresh_token_hash: str, new_refresh_token_hash: str, valid_until: datetime
    ) -> UserSession | None:
        statement = (
            update(users_sessions_table)
            .where(
                users_sessions_table.c.refresh_token_hash == old_refresh_token_hash,
                users_sessions_table.c.valid_until > datetime.now(UTC),
            )
            .values(refresh_token_hash=new_refresh_token_hash, valid_until=valid_until)
            .returning(users_sessions_table.c.id, users_sessions_table.c.user_id)
        )
        result = await session.execute(statement)
        row = result.one_or_none()
        if row is None:
            return None

        return UserSession(id=row.id, user_id=row.user_id)

    @staticmethod
    async def delete_session(session: AsyncSession, session_id: UUID) -> None:
        statement = delete(users_sessions_table).where(users_sessions_table.c.id == session_id)
        await session.execute(statement)

    @staticmethod
    async def delete_session_by_refresh_token_hash(session: AsyncSession, refresh_token_hash: str) -> None:
        statement = delete(users_sessions_table).where(users_sessions_table.c.refresh_token_hash == refresh_token_hash)
        await session.execute(statement)
