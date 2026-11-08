from collections.abc import AsyncGenerator

import pytest
from httpx2 import ASGITransport, AsyncClient

from core_service.main import prawobiorca
from core_service.shared.consts import ACCESS_COOKIE_NAME
from tests.consts import ACCESS_TOKEN, ADMIN_ACCESS_TOKEN


def create_client(access_token: str | None = None) -> AsyncClient:
    cookies = {ACCESS_COOKIE_NAME: access_token} if access_token is not None else None
    return AsyncClient(transport=ASGITransport(app=prawobiorca), base_url="http://test", cookies=cookies)


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient]:
    async with create_client() as client:
        yield client


@pytest.fixture
async def user_client(user) -> AsyncGenerator[AsyncClient]:
    async with create_client(ACCESS_TOKEN) as client:
        yield client


@pytest.fixture
async def admin_client(admin) -> AsyncGenerator[AsyncClient]:
    async with create_client(ADMIN_ACCESS_TOKEN) as client:
        yield client
