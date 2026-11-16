from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from core_service.application.ports.attempts import AttemptsRepository
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.usage import UsageBudgetsRepository
from core_service.application.services.usage import get_usage_day


@dataclass
class DeleteExpiredLimits:
    session_maker: SessionMaker
    usage_budgets_repo: UsageBudgetsRepository
    attempts_repo: AttemptsRepository

    async def execute(self) -> None:
        async with self.session_maker.begin() as session:
            await self.usage_budgets_repo.delete_before(session, get_usage_day() - timedelta(days=1))
            await self.attempts_repo.delete_expired(session, datetime.now(UTC))
