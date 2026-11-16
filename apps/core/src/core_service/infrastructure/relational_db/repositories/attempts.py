from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert

from core_service.application.ports.relational import AsyncSession
from core_service.infrastructure.relational_db.schemas.attempts import attempts_table
from core_service.infrastructure.relational_db.session import sqla_session


class SqlaAttemptsRepository:
    @staticmethod
    async def count(session: AsyncSession, key: str, window_start: datetime) -> int:
        session = sqla_session(session)
        statement = select(attempts_table.c.count).where(
            attempts_table.c.key == key, attempts_table.c.window_start == window_start
        )
        attempts = await session.scalar(statement)
        return attempts or 0

    @staticmethod
    async def add(session: AsyncSession, key: str, window_start: datetime, expires_at: datetime) -> None:
        session = sqla_session(session)
        statement = insert(attempts_table).values(key=key, window_start=window_start, expires_at=expires_at, count=1)
        statement = statement.on_conflict_do_update(
            index_elements=[attempts_table.c.key, attempts_table.c.window_start],
            set_={"count": attempts_table.c.count + 1},
        )
        await session.execute(statement)

    @staticmethod
    async def delete_expired(session: AsyncSession, moment: datetime) -> None:
        session = sqla_session(session)
        await session.execute(delete(attempts_table).where(attempts_table.c.expires_at < moment))
