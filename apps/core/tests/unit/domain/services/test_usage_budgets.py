from datetime import date
from decimal import Decimal

import pytest

from core_service.domain.services.usage import (
    ANONYMOUS_TOTAL_BUDGET_KEY,
    MCP_BUDGET_KEY,
    get_account_budget,
    get_budget_start,
    get_next_budget_start,
    resolve_budgets,
)
from core_service.domain.value_objects.usage import BudgetPeriod, PaidOperation, UsageBudget, UsageTariff
from core_service.domain.value_objects.users import Caller
from tests.consts import ADMIN_ID, IP_ADDRESS, MCP_CLIENT_ID, USER_ID

TARIFF = UsageTariff(
    prices={PaidOperation.SEMANTIC_SEARCH: Decimal("0.03")},
    account_daily_limit=Decimal("5"),
    anonymous_ip_daily_limit=Decimal("2"),
    anonymous_total_daily_limit=Decimal("50"),
    mcp_monthly_limit=Decimal("30"),
)

ACCOUNT_BUDGET = UsageBudget(key=f"account:{USER_ID}", limit=Decimal("5"), is_anonymous=False)
IP_BUDGET = UsageBudget(key=f"ip:{IP_ADDRESS}", limit=Decimal("2"), is_anonymous=True)
ANONYMOUS_TOTAL_BUDGET = UsageBudget(key=ANONYMOUS_TOTAL_BUDGET_KEY, limit=Decimal("50"), is_anonymous=True)
MCP_BUDGET = UsageBudget(key=MCP_BUDGET_KEY, limit=Decimal("30"), is_anonymous=False, period=BudgetPeriod.MONTHLY)


def test_get_account_budget():
    assert get_account_budget(USER_ID, TARIFF) == ACCOUNT_BUDGET


def test_administrator_pays_from_no_budget():
    assert resolve_budgets(Caller(user_id=ADMIN_ID, is_admin=True, ip_address=IP_ADDRESS), TARIFF) == []


def test_logged_user_pays_from_account_budget():
    assert resolve_budgets(Caller(user_id=USER_ID, ip_address=IP_ADDRESS), TARIFF) == [ACCOUNT_BUDGET]


def test_anonymous_caller_pays_from_address_and_shared_budgets():
    assert resolve_budgets(Caller(user_id=None, ip_address=IP_ADDRESS), TARIFF) == [IP_BUDGET, ANONYMOUS_TOTAL_BUDGET]


def test_anonymous_caller_without_address_pays_from_shared_budget():
    assert resolve_budgets(Caller(user_id=None), TARIFF) == [ANONYMOUS_TOTAL_BUDGET]


@pytest.mark.parametrize("is_admin", [True, False], ids=("administrator", "user"))
def test_mcp_client_pays_from_monthly_mcp_budget(is_admin):
    caller = Caller(user_id=ADMIN_ID, is_admin=is_admin, mcp_client_id=MCP_CLIENT_ID)

    assert resolve_budgets(caller, TARIFF) == [MCP_BUDGET]


@pytest.mark.parametrize(
    ("period", "day", "start"),
    [
        (BudgetPeriod.DAILY, date(2026, 11, 17), date(2026, 11, 17)),
        (BudgetPeriod.MONTHLY, date(2026, 11, 17), date(2026, 11, 1)),
        (BudgetPeriod.MONTHLY, date(2026, 11, 1), date(2026, 11, 1)),
    ],
    ids=("daily", "monthly", "monthly first day"),
)
def test_get_budget_start(period, day, start):
    assert get_budget_start(period, day) == start


@pytest.mark.parametrize(
    ("period", "day", "next_start"),
    [
        (BudgetPeriod.DAILY, date(2026, 12, 31), date(2027, 1, 1)),
        (BudgetPeriod.MONTHLY, date(2026, 11, 30), date(2026, 12, 1)),
        (BudgetPeriod.MONTHLY, date(2026, 12, 1), date(2027, 1, 1)),
    ],
    ids=("daily", "monthly", "monthly december"),
)
def test_get_next_budget_start(period, day, next_start):
    assert get_next_budget_start(period, day) == next_start
