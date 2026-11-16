from datetime import UTC, datetime, timedelta

import pytest

from core_service.domain.value_objects.attempts import AttemptLimit

LIMIT = AttemptLimit(max_attempts=5, window=timedelta(minutes=15))


@pytest.mark.parametrize(
    ("moment", "window_start"),
    [
        (datetime(2026, 11, 16, 10, 0, 0, tzinfo=UTC), datetime(2026, 11, 16, 10, 0, 0, tzinfo=UTC)),
        (datetime(2026, 11, 16, 10, 14, 59, tzinfo=UTC), datetime(2026, 11, 16, 10, 0, 0, tzinfo=UTC)),
        (datetime(2026, 11, 16, 10, 15, 0, tzinfo=UTC), datetime(2026, 11, 16, 10, 15, 0, tzinfo=UTC)),
    ],
    ids=("window start", "window end", "next window"),
)
def test_window_start(moment, window_start):
    assert LIMIT.get_window_start(moment) == window_start


def test_window_end():
    moment = datetime(2026, 11, 16, 10, 7, 30, tzinfo=UTC)

    assert LIMIT.get_window_end(moment) == datetime(2026, 11, 16, 10, 15, 0, tzinfo=UTC)
