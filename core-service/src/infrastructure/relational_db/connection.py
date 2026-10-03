from contextlib import asynccontextmanager
from typing import AsyncIterator, Awaitable, Callable

from sqlalchemy import exc, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, registry

from src.shared.exceptions import ServiceUnavailable
from src.shared.settings.relational_database import relational_db_settings

mapper_registry = registry()
metadata = mapper_registry.metadata

db_settings = relational_db_settings
DATABASE_URL = (
    f"{db_settings.DRIVER}://{db_settings.USER}:{db_settings.PASSWORD}@"
    f"{db_settings.HOST}:{db_settings.PORT}/{db_settings.NAME}"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=db_settings.POOL_SIZE,
    max_overflow=db_settings.MAX_OVERFLOW,
    pool_timeout=db_settings.POOL_TIMEOUT,
    pool_recycle=db_settings.POOL_RECYCLE,
    pool_pre_ping=True,
)


DATABASE_UNAVAILABLE_ERRORS = (exc.InterfaceError, exc.OperationalError, exc.TimeoutError, OSError)


class DatabaseSessionMaker:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self._session_maker = session_maker

    @asynccontextmanager
    async def begin(self) -> AsyncIterator[AsyncSession]:
        try:
            async with self._session_maker.begin() as session:
                yield session
        except DATABASE_UNAVAILABLE_ERRORS as e:
            raise ServiceUnavailable() from e

    @asynccontextmanager
    async def __call__(self) -> AsyncIterator[AsyncSession]:
        try:
            async with self._session_maker() as session:
                yield session
        except DATABASE_UNAVAILABLE_ERRORS as e:
            raise ServiceUnavailable() from e


async_session_maker = DatabaseSessionMaker(
    async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
)


async def check_relational_db_connection() -> Callable[..., Awaitable[None]]:
    async with async_session_maker() as session:
        await session.execute(text("SELECT 1"))
    return engine.dispose


class Base(DeclarativeBase):
    pass
