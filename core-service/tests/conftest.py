"""
Pytest configuration file for the FastAPI project.

Contains common fixtures used in tests, such as the FastAPI test client.
Recurring test data (e.g. ids) is kept as constants in `tests/consts.py`.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx2 import ASGITransport, AsyncClient

from src.main import prawobiorca


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(transport=ASGITransport(app=prawobiorca), base_url="http://test") as client:
        yield client


pytest_plugins = [
    "tests.fixtures.dependencies",
    "tests.integration.fixtures.tasks",
    "tests.integration.fixtures.users",
]
