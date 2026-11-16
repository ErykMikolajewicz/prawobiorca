from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class PaidOperation(StrEnum):
    SEMANTIC_SEARCH = "SEMANTIC_SEARCH"
    APPLICATION_GENERATION = "APPLICATION_GENERATION"
    REGULATION_PREPARATION = "REGULATION_PREPARATION"


@dataclass(frozen=True)
class UsageBudget:
    key: str
    daily_limit: Decimal
    is_anonymous: bool


@dataclass(frozen=True)
class UsageTariff:
    prices: Mapping[PaidOperation, Decimal]
    account_daily_limit: Decimal
    anonymous_ip_daily_limit: Decimal
    anonymous_total_daily_limit: Decimal
