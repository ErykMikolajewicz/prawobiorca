"""
Pytest configuration file for the FastAPI project.

Contains common fixtures used in tests, such as the FastAPI test client
and generators for tokens and UUIDs.
"""

from collections.abc import Iterator
from uuid import UUID

import pytest
from httpx2 import ASGITransport, AsyncClient

from src.main import prawobiorca


@pytest.fixture(scope="function")
def uuid_generator() -> Iterator[UUID]:
    """
    Generates a sequence of predefined UUIDs.

    Can be used max 4 time per test, currently sufficient for all test scenarios.

    Yields:
        str: The next UUID from the predefined list.
    """
    uuids = (
        UUID("1b4a1b7a-dbd6-4be4-a52e-80fdd9ddbfb0"),
        UUID("a3f54f36-9653-4ccf-b9f4-81bf885d02ee"),
        UUID("8f7a6b5c-4d3e-2f1a-9b8c-7d6e5f4a3b2c"),
        UUID("1a2b3c4d-5e6f-7a8b-9c0d-1e2f3a4b5c6d"),
    )

    return iter(uuids)


@pytest.fixture(scope="function")
async def client() -> AsyncClient:
    async with AsyncClient(transport=ASGITransport(app=prawobiorca), base_url="http://test") as client:
        yield client


pytest_plugins = [
    "tests.fixtures.dependencies",
    "tests.integration.fixtures.tasks",
    "tests.integration.fixtures.users",
]
