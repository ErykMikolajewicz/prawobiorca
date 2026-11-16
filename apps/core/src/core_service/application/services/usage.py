import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from math import ceil
from uuid import UUID
from zoneinfo import ZoneInfo

from core_service.application.ports.relational import AsyncSession
from core_service.application.ports.usage import UsageBudgetsRepository
from core_service.domain.exceptions.limits import UsageLimitExceeded
from core_service.domain.services.usage import get_account_budget, resolve_budgets
from core_service.domain.value_objects.usage import PaidOperation, UsageTariff
from core_service.domain.value_objects.users import Caller

logger = logging.getLogger(__name__)

USAGE_TIME_ZONE = ZoneInfo("Europe/Warsaw")


def get_usage_day() -> date:
    return datetime.now(USAGE_TIME_ZONE).date()


def get_seconds_to_next_usage_day() -> int:
    now = datetime.now(USAGE_TIME_ZONE)
    next_day = datetime.combine(now.date() + timedelta(days=1), time.min, USAGE_TIME_ZONE)
    return ceil((next_day.astimezone(UTC) - now.astimezone(UTC)).total_seconds())


@dataclass
class UsageCharger:
    usage_budgets_repo: UsageBudgetsRepository
    tariff: UsageTariff

    async def charge(self, session: AsyncSession, caller: Caller, operation: PaidOperation) -> None:
        price = self.tariff.prices[operation]
        day = get_usage_day()

        for budget in resolve_budgets(caller, self.tariff):
            is_spent = await self.usage_budgets_repo.spend(session, budget.key, day, price, budget.daily_limit)
            if not is_spent:
                logger.warning("Usage limit exceeded! budget: %s, operation: %s", budget.key, operation)
                raise UsageLimitExceeded(budget.is_anonymous, get_seconds_to_next_usage_day())

    async def refund(self, session: AsyncSession, user_id: UUID, operation: PaidOperation) -> None:
        budget = get_account_budget(user_id, self.tariff)
        await self.usage_budgets_repo.refund(session, budget.key, get_usage_day(), self.tariff.prices[operation])
