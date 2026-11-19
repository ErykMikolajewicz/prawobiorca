from datetime import UTC, datetime, timedelta, tzinfo
from unittest.mock import create_autospec, patch

import pytest

from core_service.application.ports.attempts import AttemptsRepository
from core_service.application.services.attempts import AttemptLimiter
from core_service.domain.exceptions.limits import TooManyAttempts
from core_service.domain.value_objects.attempts import AttemptLimit, AttemptReservation

KEY = "login:key"
MAX_ATTEMPTS = 5

NOW = datetime(2026, 11, 16, 10, 10, 0, tzinfo=UTC)
WINDOW_START = datetime(2026, 11, 16, 10, 0, 0, tzinfo=UTC)
WINDOW_END = datetime(2026, 11, 16, 10, 15, 0, tzinfo=UTC)
SECONDS_TO_WINDOW_END = 5 * 60


def get_now(time_zone: tzinfo | None = None) -> datetime:
    return NOW.astimezone(time_zone) if time_zone is not None else NOW.replace(tzinfo=None)


@pytest.fixture(autouse=True)
def mock_now():
    with patch("core_service.application.services.attempts.datetime", wraps=datetime) as mock_datetime:
        mock_datetime.now.side_effect = get_now
        yield


@pytest.fixture
def mock_attempts_repo():
    return create_autospec(AttemptsRepository)


@pytest.fixture
def attempt_limiter(mock_attempts_repo):
    limit = AttemptLimit(max_attempts=MAX_ATTEMPTS, window=timedelta(minutes=15))
    return AttemptLimiter(attempts_repo=mock_attempts_repo, limit=limit)


async def test_acquire_reserves_attempt_in_current_window(attempt_limiter, mock_attempts_repo, mock_opened_session):
    mock_attempts_repo.try_acquire.return_value = True

    reservation = await attempt_limiter.acquire(mock_opened_session, KEY)

    assert reservation == AttemptReservation(KEY, WINDOW_START)
    mock_attempts_repo.try_acquire.assert_awaited_once_with(
        mock_opened_session, KEY, WINDOW_START, WINDOW_END, MAX_ATTEMPTS
    )


async def test_acquire_rejects_attempts_reaching_limit(attempt_limiter, mock_attempts_repo, mock_opened_session):
    mock_attempts_repo.try_acquire.return_value = False

    with pytest.raises(TooManyAttempts) as error:
        await attempt_limiter.acquire(mock_opened_session, KEY)

    assert error.value.retry_after_seconds == SECONDS_TO_WINDOW_END


async def test_release_uses_original_window(attempt_limiter, mock_attempts_repo, mock_opened_session):
    original_window = WINDOW_START - timedelta(minutes=15)
    reservation = AttemptReservation(KEY, original_window)

    await attempt_limiter.release(mock_opened_session, reservation)

    mock_attempts_repo.release.assert_awaited_once_with(mock_opened_session, KEY, original_window)
