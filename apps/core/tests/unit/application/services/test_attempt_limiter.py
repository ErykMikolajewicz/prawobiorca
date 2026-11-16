from datetime import UTC, datetime, timedelta, tzinfo
from unittest.mock import create_autospec, patch

import pytest

from core_service.application.ports.attempts import AttemptsRepository
from core_service.application.services.attempts import AttemptLimiter
from core_service.domain.exceptions.limits import TooManyAttempts
from core_service.domain.value_objects.attempts import AttemptLimit

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


async def test_check_allows_attempts_below_limit(attempt_limiter, mock_attempts_repo, mock_opened_session):
    mock_attempts_repo.count.return_value = MAX_ATTEMPTS - 1

    await attempt_limiter.check(mock_opened_session, KEY)

    mock_attempts_repo.count.assert_awaited_once_with(mock_opened_session, KEY, WINDOW_START)


async def test_check_rejects_attempts_reaching_limit(attempt_limiter, mock_attempts_repo, mock_opened_session):
    mock_attempts_repo.count.return_value = MAX_ATTEMPTS

    with pytest.raises(TooManyAttempts) as error:
        await attempt_limiter.check(mock_opened_session, KEY)

    assert error.value.retry_after_seconds == SECONDS_TO_WINDOW_END


async def test_record_adds_attempt_to_current_window(attempt_limiter, mock_attempts_repo, mock_opened_session):
    await attempt_limiter.record(mock_opened_session, KEY)

    mock_attempts_repo.add.assert_awaited_once_with(mock_opened_session, KEY, WINDOW_START, WINDOW_END)
