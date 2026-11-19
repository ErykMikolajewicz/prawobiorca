import asyncio
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from sqlalchemy import select

from core_service.application.services.accounts import check_user_can_log
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
from core_service.shared.exceptions import ServiceUnavailable
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
        await repository.try_acquire(session, "expired", now - 2 * WINDOW, now - WINDOW, 2)
        await repository.try_acquire(session, "current", now, now + WINDOW, 2)
        await repository.try_acquire(session, "current", now, now + WINDOW, 2)

    await DeleteExpiredLimits(DatabaseSessionMaker(session_maker), SqlaUsageBudgetsRepository(), repository).execute()

    async with session_maker() as session:
        result = await session.execute(select(attempts_table.c.key, attempts_table.c.count))
    assert [tuple(attempt) for attempt in result] == [("current", 2)]


@pytest.mark.parametrize("existing_attempts", [0, 2])
async def test_concurrent_reservations_do_not_exceed_limit(session_maker, existing_attempts):
    repository = SqlaAttemptsRepository()
    now = datetime.now(UTC)
    limit = 3
    async with session_maker.begin() as session:
        for _ in range(existing_attempts):
            await repository.try_acquire(session, "concurrent", now, now + WINDOW, limit)

    barrier = asyncio.Barrier(8)

    async def reserve():
        async with session_maker.begin() as session:
            await barrier.wait()
            return await repository.try_acquire(session, "concurrent", now, now + WINDOW, limit)

    async with asyncio.timeout(10):
        results = await asyncio.gather(*(reserve() for _ in range(8)))

    assert sum(results) == limit - existing_attempts
    async with session_maker() as session:
        assert await session.scalar(select(attempts_table.c.count)) == limit


async def test_release_preserves_other_windows_and_does_not_go_negative(session_maker):
    repository = SqlaAttemptsRepository()
    now = datetime.now(UTC)
    previous_window = now - WINDOW
    async with session_maker.begin() as session:
        await repository.try_acquire(session, "key", previous_window, now, 1)
        await repository.try_acquire(session, "key", now, now + WINDOW, 1)
        await repository.release(session, "key", previous_window)
        await repository.release(session, "key", previous_window)
        await repository.release(session, "missing", now)

    async with session_maker() as session:
        result = await session.execute(select(attempts_table.c.window_start, attempts_table.c.count))
    assert {row.window_start: row.count for row in result} == {previous_window: 0, now: 1}


async def test_concurrent_registrations_are_limited(client):
    responses = await asyncio.gather(*(register(client, f"concurrent-{index}") for index in range(6)))
    statuses = [response.status_code for response in responses]

    assert statuses.count(status.HTTP_201_CREATED) == MAX_REGISTRATION_ATTEMPTS
    assert statuses.count(status.HTTP_429_TOO_MANY_REQUESTS) == 6 - MAX_REGISTRATION_ATTEMPTS


async def test_concurrent_failed_logins_are_limited(client, user):
    responses = await asyncio.gather(*(log_in(client, password="WrongPassword123!") for _ in range(6)))
    statuses = [response.status_code for response in responses]

    assert statuses.count(status.HTTP_401_UNAUTHORIZED) == MAX_LOGIN_ATTEMPTS
    assert statuses.count(status.HTTP_429_TOO_MANY_REQUESTS) == 6 - MAX_LOGIN_ATTEMPTS


async def test_pending_login_reserves_capacity_and_success_releases_it(client, user):
    prawobiorca.dependency_overrides[get_login_attempt_limit] = lambda: AttemptLimit(1, WINDOW)
    verifying = asyncio.Event()
    proceed = asyncio.Event()

    async def delayed_verification(*args):
        verifying.set()
        await proceed.wait()
        return await check_user_can_log(*args)

    with patch("core_service.application.use_cases.auth.check_user_can_log", side_effect=delayed_verification):
        async with asyncio.timeout(10), asyncio.TaskGroup() as tasks:
            pending = tasks.create_task(log_in(client))
            await verifying.wait()
            try:
                blocked = await log_in(client)
                assert blocked.status_code == status.HTTP_429_TOO_MANY_REQUESTS
            finally:
                proceed.set()

    assert pending.result().status_code == status.HTTP_200_OK
    assert (await log_in(client)).status_code == status.HTTP_200_OK


async def test_successful_login_keeps_previous_failures(client, user):
    assert (await log_in(client, password="WrongPassword123!")).status_code == status.HTTP_401_UNAUTHORIZED
    assert (await log_in(client)).status_code == status.HTTP_200_OK

    for _ in range(MAX_LOGIN_ATTEMPTS - 1):
        assert (await log_in(client, password="WrongPassword123!")).status_code == status.HTTP_401_UNAUTHORIZED

    assert (await log_in(client)).status_code == status.HTTP_429_TOO_MANY_REQUESTS


async def test_interrupted_login_keeps_reservation(client):
    prawobiorca.dependency_overrides[get_login_attempt_limit] = lambda: AttemptLimit(1, WINDOW)
    with patch("core_service.application.use_cases.auth.check_user_can_log", side_effect=ServiceUnavailable):
        response = await log_in(client)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert (await log_in(client)).status_code == status.HTTP_429_TOO_MANY_REQUESTS


async def test_zero_attempt_limit_does_not_create_reservation(session_maker):
    repository = SqlaAttemptsRepository()
    now = datetime.now(UTC)
    async with session_maker.begin() as session:
        assert not await repository.try_acquire(session, "disabled", now, now + WINDOW, 0)

    async with session_maker() as session:
        assert await session.scalar(select(attempts_table.c.count)) is None
