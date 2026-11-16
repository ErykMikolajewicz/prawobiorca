from uuid import UUID

from core_service.domain.value_objects.usage import UsageBudget, UsageTariff
from core_service.domain.value_objects.users import Caller

ANONYMOUS_TOTAL_BUDGET_KEY = "anonymous"


def get_account_budget(user_id: UUID, tariff: UsageTariff) -> UsageBudget:
    return UsageBudget(key=f"account:{user_id}", daily_limit=tariff.account_daily_limit, is_anonymous=False)


def resolve_budgets(caller: Caller, tariff: UsageTariff) -> list[UsageBudget]:
    if caller.is_admin:
        return []
    if caller.user_id is not None:
        return [get_account_budget(caller.user_id, tariff)]

    budgets = []
    if caller.ip_address is not None:
        budgets.append(
            UsageBudget(key=f"ip:{caller.ip_address}", daily_limit=tariff.anonymous_ip_daily_limit, is_anonymous=True)
        )
    budgets.append(
        UsageBudget(key=ANONYMOUS_TOTAL_BUDGET_KEY, daily_limit=tariff.anonymous_total_daily_limit, is_anonymous=True)
    )
    return budgets
