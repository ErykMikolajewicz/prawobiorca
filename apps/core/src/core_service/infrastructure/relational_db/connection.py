from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager

from sqlalchemy import URL, exc, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import registry

from core_service.shared.exceptions import ServiceUnavailable
from core_service.shared.settings.relational_database import relational_db_settings

mapper_registry = registry()
metadata = mapper_registry.metadata

db_settings = relational_db_settings
DATABASE_URL = URL.create(
    drivername=db_settings.DRIVER,
    username=db_settings.USER,
    password=db_settings.PASSWORD.get_secret_value(),
    host=db_settings.HOST,
    port=db_settings.PORT,
    database=db_settings.NAME,
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
    async def begin(self) -> AsyncGenerator[AsyncSession]:
        try:
            async with self._session_maker.begin() as session:
                yield session
        except DATABASE_UNAVAILABLE_ERRORS as e:
            raise ServiceUnavailable() from e

    @asynccontextmanager
    async def __call__(self) -> AsyncGenerator[AsyncSession]:
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
