from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class PaidOperation(StrEnum):
    SEMANTIC_SEARCH = "SEMANTIC_SEARCH"
    APPLICATION_GENERATION = "APPLICATION_GENERATION"
    REGULATION_PREPARATION = "REGULATION_PREPARATION"


class BudgetPeriod(StrEnum):
    DAILY = "DAILY"
    MONTHLY = "MONTHLY"


@dataclass(frozen=True)
class UsageBudget:
    key: str
    limit: Decimal
    is_anonymous: bool
    period: BudgetPeriod = BudgetPeriod.DAILY


@dataclass(frozen=True)
class UsageTariff:
    prices: Mapping[PaidOperation, Decimal]
    account_daily_limit: Decimal
    anonymous_ip_daily_limit: Decimal
    anonymous_total_daily_limit: Decimal
    mcp_monthly_limit: Decimal
