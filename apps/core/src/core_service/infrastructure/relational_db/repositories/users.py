from dataclasses import asdict
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, insert, select, update
from sqlalchemy.exc import IntegrityError

from core_service.application.dtos.user import CreateUserData
from core_service.application.ports.relational import AsyncSession
from core_service.domain.entities.user import User
from core_service.domain.value_objects.auth import UserSession
from core_service.domain.value_objects.users import UserPrivileges
from core_service.infrastructure.relational_db.schemas.users import users_sessions_table, users_table
from core_service.infrastructure.relational_db.session import sqla_session
from core_service.shared.exceptions import ObjectExists


class SqlaUsersRepository:
    @staticmethod
    async def add(session: AsyncSession, create_data: CreateUserData):
        session = sqla_session(session)
        statement = insert(User).values(**asdict(create_data))
        try:
            await session.execute(statement)
        except IntegrityError:
            raise ObjectExists

    @staticmethod
    async def get_by_username(session: AsyncSession, username: str) -> User | None:
        session = sqla_session(session)
        statement = select(User).where(users_table.c.username == username)
        user = await session.scalar(statement)

        return user

    @staticmethod
    async def get_user_privileges(session: AsyncSession, user_id: UUID) -> UserPrivileges | None:
        session = sqla_session(session)
        statement = select(users_table.c.is_admin).where(users_table.c.id == user_id)

        result = await session.execute(statement)
        is_admin = result.scalar_one_or_none()
        if is_admin is None:
            return None

        user_privileges = UserPrivileges(is_admin=is_admin)

        return user_privileges


class SqlaUsersSessionsRepository:
    @staticmethod
    async def create_session(
        session: AsyncSession, user_id: UUID, refresh_token_hash: str, valid_until: datetime
    ) -> UUID:
        session = sqla_session(session)
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
        session = sqla_session(session)
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
        session = sqla_session(session)
        statement = delete(users_sessions_table).where(users_sessions_table.c.id == session_id)
        await session.execute(statement)

    @staticmethod
    async def delete_session_by_refresh_token_hash(session: AsyncSession, refresh_token_hash: str) -> None:
        session = sqla_session(session)
        statement = delete(users_sessions_table).where(users_sessions_table.c.refresh_token_hash == refresh_token_hash)
        await session.execute(statement)
