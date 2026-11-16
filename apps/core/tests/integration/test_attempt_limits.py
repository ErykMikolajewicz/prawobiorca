from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from sqlalchemy import select

from core_service.application.use_cases.limits import DeleteExpiredLimits
from core_service.domain.value_objects.attempts import AttemptLimit
from core_service.framework.consts import TOO_MANY_ATTEMPTS_CODE
from core_service.framework.dependencies.attempts import get_login_attempt_limit, get_registration_attempt_limit
from core_service.framework.dependencies.client_address import get_trusted_proxies_count
from core_service.infrastructure.relational_db.connection import DatabaseSessionMaker
from core_service.infrastructure.relational_db.repositories.attempts import SqlaAttemptsRepository
from core_service.infrastructure.relational_db.repositories.usage_budgets import SqlaUsageBudgetsRepository
from core_service.infrastructure.relational_db.schemas.attempts import attempts_table
from core_service.main import prawobiorca
from tests.consts import IP_ADDRESS, STRONG_PASSWORD, VALID_USERNAME

OTHER_IP_ADDRESS = "198.51.100.4"

MAX_LOGIN_ATTEMPTS = 3
MAX_REGISTRATION_ATTEMPTS = 2

WINDOW = timedelta(minutes=15)


@pytest.fixture(autouse=True)
def override_attempt_limits(override_dependencies) -> None:
    prawobiorca.dependency_overrides[get_login_attempt_limit] = lambda: AttemptLimit(MAX_LOGIN_ATTEMPTS, WINDOW)
    prawobiorca.dependency_overrides[get_registration_attempt_limit] = lambda: AttemptLimit(
        MAX_REGISTRATION_ATTEMPTS, WINDOW
    )
    prawobiorca.dependency_overrides[get_trusted_proxies_count] = lambda: 1


@pytest.fixture(autouse=True)
def mock_prevent_timing_attack():
    with patch("core_service.application.use_cases.auth.prevent_timing_attack", new_callable=AsyncMock):
        yield


async def log_in(client, password: str = STRONG_PASSWORD, ip_address: str = IP_ADDRESS, username: str = VALID_USERNAME):
    return await client.post(
        "/api/auth/login",
        data={"username": username, "password": password},
        headers={"X-Forwarded-For": ip_address},
    )


async def register(client, username: str, ip_address: str = IP_ADDRESS):
    return await client.post(
        "/api/accounts/register",
        json={"username": username, "password": STRONG_PASSWORD},
        headers={"X-Forwarded-For": ip_address},
    )


async def fail_login_attempts(client, **login_data) -> None:
    for _ in range(MAX_LOGIN_ATTEMPTS):
        response = await log_in(client, password="WrongPassword123!", **login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_login_is_blocked_after_failed_attempts(client, user):
    await fail_login_attempts(client)

    response = await log_in(client)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["code"] == TOO_MANY_ATTEMPTS_CODE
    assert 0 < int(response.headers["Retry-After"]) <= WINDOW.total_seconds()


async def test_login_is_not_blocked_by_failed_attempts_from_other_address(client, user):
    await fail_login_attempts(client, ip_address=OTHER_IP_ADDRESS)

    response = await log_in(client)

    assert response.status_code == status.HTTP_200_OK


async def test_login_is_not_blocked_by_failed_attempts_of_other_user(client, user):
    await fail_login_attempts(client, username="other-user")

    response = await log_in(client)

    assert response.status_code == status.HTTP_200_OK


async def test_successful_logins_are_not_limited(client, user):
    for _ in range(MAX_LOGIN_ATTEMPTS + 1):
        response = await log_in(client)

        assert response.status_code == status.HTTP_200_OK


async def test_registration_is_blocked_after_attempts_from_address(client):
    for index in range(MAX_REGISTRATION_ATTEMPTS):
        response = await register(client, f"username{index}")
        assert response.status_code == status.HTTP_201_CREATED

    response = await register(client, "blocked-username")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["code"] == TOO_MANY_ATTEMPTS_CODE
    assert 0 < int(response.headers["Retry-After"]) <= WINDOW.total_seconds()


async def test_registration_is_not_blocked_by_attempts_from_other_address(client):
    for index in range(MAX_REGISTRATION_ATTEMPTS):
        await register(client, f"username{index}", OTHER_IP_ADDRESS)

    response = await register(client, VALID_USERNAME)

    assert response.status_code == status.HTTP_201_CREATED


async def test_delete_expired_limits_keeps_current_attempts(session_maker):
    repository = SqlaAttemptsRepository()
    now = datetime.now(UTC)
    async with session_maker.begin() as session:
        await repository.add(session, "expired", now - 2 * WINDOW, now - WINDOW)
        await repository.add(session, "current", now, now + WINDOW)
        await repository.add(session, "current", now, now + WINDOW)

    await DeleteExpiredLimits(DatabaseSessionMaker(session_maker), SqlaUsageBudgetsRepository(), repository).execute()

    async with session_maker() as session:
        result = await session.execute(select(attempts_table.c.key, attempts_table.c.count))
    assert [tuple(attempt) for attempt in result] == [("current", 2)]
