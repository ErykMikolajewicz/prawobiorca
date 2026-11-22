from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from core_service.application.ports.attempts import AttemptsRepository
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.usage import UsageBudgetsRepository
from core_service.application.services.usage import get_usage_day
from core_service.domain.services.usage import get_budget_start
from core_service.domain.value_objects.usage import BudgetPeriod


@dataclass
class DeleteExpiredLimits:
    session_maker: SessionMaker
    usage_budgets_repo: UsageBudgetsRepository
    attempts_repo: AttemptsRepository

    async def execute(self) -> None:
        async with self.session_maker.begin() as session:
            day = get_usage_day()
            oldest_kept_day = min(day - timedelta(days=1), get_budget_start(BudgetPeriod.MONTHLY, day))
            await self.usage_budgets_repo.delete_before(session, oldest_kept_day)
            await self.attempts_repo.delete_expired(session, datetime.now(UTC))
