from decimal import Decimal

from core_service.domain.services.usage import ANONYMOUS_TOTAL_BUDGET_KEY, get_account_budget, resolve_budgets
from core_service.domain.value_objects.usage import PaidOperation, UsageBudget, UsageTariff
from core_service.domain.value_objects.users import Caller
from tests.consts import ADMIN_ID, IP_ADDRESS, USER_ID

TARIFF = UsageTariff(
    prices={PaidOperation.SEMANTIC_SEARCH: Decimal("0.03")},
    account_daily_limit=Decimal("5"),
    anonymous_ip_daily_limit=Decimal("2"),
    anonymous_total_daily_limit=Decimal("50"),
)

ACCOUNT_BUDGET = UsageBudget(key=f"account:{USER_ID}", daily_limit=Decimal("5"), is_anonymous=False)
IP_BUDGET = UsageBudget(key=f"ip:{IP_ADDRESS}", daily_limit=Decimal("2"), is_anonymous=True)
ANONYMOUS_TOTAL_BUDGET = UsageBudget(key=ANONYMOUS_TOTAL_BUDGET_KEY, daily_limit=Decimal("50"), is_anonymous=True)


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
