from datetime import date, timedelta
from uuid import UUID

from core_service.domain.value_objects.usage import BudgetPeriod, UsageBudget, UsageTariff
from core_service.domain.value_objects.users import Caller

ANONYMOUS_TOTAL_BUDGET_KEY = "anonymous"
MCP_BUDGET_KEY = "mcp"


def get_budget_start(period: BudgetPeriod, day: date) -> date:
    if period == BudgetPeriod.MONTHLY:
        return day.replace(day=1)
    return day


def get_next_budget_start(period: BudgetPeriod, day: date) -> date:
    if period == BudgetPeriod.MONTHLY:
        return date(day.year + day.month // 12, day.month % 12 + 1, 1)
    return day + timedelta(days=1)


def get_account_budget(user_id: UUID, tariff: UsageTariff) -> UsageBudget:
    return UsageBudget(key=f"account:{user_id}", limit=tariff.account_daily_limit, is_anonymous=False)


def resolve_budgets(caller: Caller, tariff: UsageTariff) -> list[UsageBudget]:
    if caller.mcp_client_id is not None:
        return [
            UsageBudget(
                key=MCP_BUDGET_KEY, limit=tariff.mcp_monthly_limit, is_anonymous=False, period=BudgetPeriod.MONTHLY
            )
        ]
    if caller.is_admin:
        return []
    if caller.user_id is not None:
        return [get_account_budget(caller.user_id, tariff)]

    budgets = []
    if caller.ip_address is not None:
        budgets.append(
            UsageBudget(key=f"ip:{caller.ip_address}", limit=tariff.anonymous_ip_daily_limit, is_anonymous=True)
        )
    budgets.append(
        UsageBudget(key=ANONYMOUS_TOTAL_BUDGET_KEY, limit=tariff.anonymous_total_daily_limit, is_anonymous=True)
    )
    return budgets
