"""Common pytest fixtures for integration tests.

These fixtures handle container initialization (PostgresSQL), connect the application to the test
database and replace external services with mocks. Every test starts with empty tables, so it does not
need to clean up after itself.
"""

import os
import subprocess
from collections.abc import AsyncGenerator, Generator

import alembic.command
import alembic.config
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from testcontainers.community.postgres import PostgresContainer

from src.framework.dependencies.ai_services import get_texts_embedder
from src.framework.dependencies.application_templates import get_application_templates_storage
from src.framework.dependencies.cases import get_applications_storage
from src.framework.dependencies.regulations import get_broker, get_regulations_storage
from src.framework.dependencies.relational import get_session_maker
from src.main import prawobiorca

POSTGRES_IMAGE_VERSION = "ghcr.io/erykmikolajewicz/pgvector:0.8.4-pg18-trixie"

SELECT_TABLES = text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename != 'alembic_version'")


@pytest.fixture(scope="session")
def configure_podman() -> None:
    if "DOCKER_HOST" in os.environ:
        return

    subprocess.run(["systemctl", "--user", "enable", "--now", "podman.socket"], check=True)

    uid = os.getuid()
    podman_sock = f"unix:///run/user/{uid}/podman/podman.sock"

    os.environ["DOCKER_HOST"] = podman_sock


@pytest.fixture(scope="session")
def postgres_container(configure_podman) -> Generator[PostgresContainer]:
    """Create a PostgresSQL test container, shared by all tests to avoid repeated startup overhead."""
    with PostgresContainer(POSTGRES_IMAGE_VERSION, driver="asyncpg") as postgres:
        yield postgres


@pytest.fixture(scope="session", autouse=True)
def run_migrations(postgres_container: PostgresContainer) -> None:
    alembic_cfg = alembic.config.Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_container.get_connection_url())
    alembic.command.upgrade(alembic_cfg, "head")


@pytest.fixture(scope="session")
async def session_maker(postgres_container: PostgresContainer, run_migrations) -> AsyncGenerator[async_sessionmaker]:
    """Session maker of the test database, shared by the tests and the application.

    The application called through `ASGITransport` runs in the same event loop as the tests, so both can use
    the same engine.
    """
    db_engine = create_async_engine(postgres_container.get_connection_url())
    yield async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    await db_engine.dispose()


@pytest.fixture(autouse=True)
async def clean_database(session_maker: async_sessionmaker) -> None:
    """Empty all tables before each test, including the data inserted by migrations."""
    async with session_maker.begin() as session:
        tables = await session.scalars(SELECT_TABLES)
        await session.execute(text(f"TRUNCATE {', '.join(tables)} CASCADE"))


@pytest.fixture(autouse=True)
def override_dependencies(
    session_maker,
    broker,
    mock_texts_embedder,
    mock_regulations_storage,
    mock_applications_storage,
    mock_application_templates_storage,
) -> Generator[None]:
    """Connect the application to the test database, and replace external services with mocks.

    A test configures or inspects a mock by requesting its fixture, e.g. `mock_regulations_storage`.
    """
    prawobiorca.dependency_overrides.update(
        {
            get_session_maker: lambda: session_maker,
            get_broker: lambda: broker,
            get_texts_embedder: lambda: mock_texts_embedder,
            get_regulations_storage: lambda: mock_regulations_storage,
            get_applications_storage: lambda: mock_applications_storage,
            get_application_templates_storage: lambda: mock_application_templates_storage,
        }
    )
    yield
    prawobiorca.dependency_overrides.clear()
