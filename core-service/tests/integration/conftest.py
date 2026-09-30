"""Common pytest fixtures for integration tests.

These fixtures handle container initialization (PostgresSQL, Redis)
and dependency overrides for FastAPI, ensuring test isolation.
"""

# The justification for the applied solutions is in the mkdocs documentation.
import os
import subprocess
from typing import AsyncGenerator, Generator

import alembic.command
import alembic.config
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from src.framework.dependencies.relational import get_session_maker
from src.main import prawobiorca

POSTGRES_IMAGE_VERSION = "pgvector/pgvector:0.8.4-pg18-trixie"


@pytest.fixture(scope="session", autouse=True)
def configure_podman():
    if "DOCKER_HOST" in os.environ:
        return

    subprocess.run(["systemctl", "--user", "enable", "--now", "podman.socket"])

    uid = os.getuid()
    podman_sock = f"unix:///run/user/{uid}/podman/podman.sock"

    os.environ["DOCKER_HOST"] = podman_sock


@pytest.fixture(scope="session", autouse=True)
def run_migrations(postgres_container: PostgresContainer) -> None:
    """Run Alembic migrations on the test PostgresSQL database.

    This fixture automatically runs before tests to ensure
    the schema is up to date.

    Args:
        postgres_container (PostgresContainer): Running PostgresSQL test container.
    """
    alembic_cfg = alembic.config.Config("alembic.ini")
    db_url = postgres_container.get_connection_url()
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)
    alembic.command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None]:
    """Create and manage a PostgresSQL test container.

    Scope is set to `session` to avoid repeated startup overhead.

    Yields:
        PostgresContainer: Running PostgresSQL container.
    """
    with PostgresContainer(POSTGRES_IMAGE_VERSION, driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture
async def override_session_maker(postgres_container: PostgresContainer) -> AsyncGenerator[None, None]:
    """Override the FastAPI relational DB dependency with a test session.

    Replaces the default `get_session_maker` dependency with a session maker
    connected to the PostgresSQL test container.

    Args:
        postgres_container (PostgresContainer): Running PostgresSQL test container.

    Yields:
        None: This is a pytest fixture that sets the override in FastAPI.

    Note:
        This fixture is intended for FastAPI integration tests only.
    """
    url = postgres_container.get_connection_url()
    db_engine = create_async_engine(url, future=True, echo=False)
    async_session_maker = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    async def _override():
        yield async_session_maker

    prawobiorca.dependency_overrides[get_session_maker] = _override
    yield
    await db_engine.dispose()
    prawobiorca.dependency_overrides = {}


@pytest.fixture
async def session_maker(postgres_container: PostgresContainer) -> AsyncGenerator[async_sessionmaker, None]:
    """Get separated session maker, to can make session in pytest - they are running in separated thread than FASTapi.
    This is due to internal pytest implementation, avery async test in separated thread."""
    url = postgres_container.get_connection_url()
    db_engine = create_async_engine(url, future=True, echo=False)
    async_session_maker = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)

    yield async_session_maker
    await db_engine.dispose()
    prawobiorca.dependency_overrides = {}
