from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession as SqlaAsyncSession

from core_service.application.ports.relational import AsyncSession


def sqla_session(session: AsyncSession) -> SqlaAsyncSession:
    return cast(SqlaAsyncSession, session)
