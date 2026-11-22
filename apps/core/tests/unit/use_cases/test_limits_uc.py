from datetime import date
from unittest.mock import create_autospec, patch

import pytest

from core_service.application.ports.attempts import AttemptsRepository
from core_service.application.ports.usage import UsageBudgetsRepository
from core_service.application.use_cases.limits import DeleteExpiredLimits


@pytest.mark.parametrize(
    ("usage_day", "oldest_kept_day"),
    [(date(2026, 11, 17), date(2026, 11, 1)), (date(2026, 12, 1), date(2026, 11, 30))],
    ids=("middle of month", "first day of month"),
)
async def test_delete_expired_limits_keeps_current_month_budgets(
    mock_session_maker, mock_opened_session, usage_day, oldest_kept_day
):
    usage_budgets_repo = create_autospec(UsageBudgetsRepository)
    use_case = DeleteExpiredLimits(mock_session_maker, usage_budgets_repo, create_autospec(AttemptsRepository))

    with patch("core_service.application.use_cases.limits.get_usage_day", return_value=usage_day):
        await use_case.execute()

    usage_budgets_repo.delete_before.assert_awaited_once_with(mock_opened_session, oldest_kept_day)
