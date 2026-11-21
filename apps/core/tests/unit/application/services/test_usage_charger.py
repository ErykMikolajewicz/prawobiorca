from datetime import UTC, date, datetime, tzinfo
from decimal import Decimal
from unittest.mock import create_autospec, patch

import pytest

from core_service.application.ports.usage import UsageBudgetsRepository, UsageTariffRepository
from core_service.application.services.usage import UsageCharger
from core_service.domain.exceptions.limits import UsageLimitExceeded
from core_service.domain.services.usage import ANONYMOUS_TOTAL_BUDGET_KEY
from core_service.domain.value_objects.usage import PaidOperation, UsageTariff
from core_service.domain.value_objects.users import Caller
from tests.consts import ADMIN_ID, IP_ADDRESS, USER_ID
from tests.mocks import get_awaited_arguments

SEARCH_PRICE = Decimal("0.03")
GENERATION_PRICE = Decimal("0.50")

TARIFF = UsageTariff(
    prices={PaidOperation.SEMANTIC_SEARCH: SEARCH_PRICE, PaidOperation.APPLICATION_GENERATION: GENERATION_PRICE},
    account_daily_limit=Decimal("5"),
    anonymous_ip_daily_limit=Decimal("2"),
    anonymous_total_daily_limit=Decimal("50"),
)

NOW = datetime(2026, 11, 16, 23, 30, 0, tzinfo=UTC)
USAGE_DAY = date(2026, 11, 17)
SECONDS_TO_NEXT_DAY = 23 * 60 * 60 + 30 * 60

ANONYMOUS = Caller(user_id=None, ip_address=IP_ADDRESS)
USER = Caller(user_id=USER_ID, ip_address=IP_ADDRESS)
ADMIN = Caller(user_id=ADMIN_ID, is_admin=True, ip_address=IP_ADDRESS)


def get_now(time_zone: tzinfo | None = None) -> datetime:
    return NOW.astimezone(time_zone) if time_zone is not None else NOW.replace(tzinfo=None)


@pytest.fixture(autouse=True)
def mock_now():
    with patch("core_service.application.services.usage.datetime", wraps=datetime) as mock_datetime:
        mock_datetime.now.side_effect = get_now
        yield


@pytest.fixture
def mock_usage_budgets_repo():
    repo = create_autospec(UsageBudgetsRepository)
    repo.spend.return_value = True
    return repo


@pytest.fixture
def mock_usage_tariff_repo():
    repo = create_autospec(UsageTariffRepository)
    repo.get.return_value = TARIFF
    return repo


@pytest.fixture
def usage_charger(mock_usage_budgets_repo, mock_usage_tariff_repo):
    return UsageCharger(usage_budgets_repo=mock_usage_budgets_repo, usage_tariff_repo=mock_usage_tariff_repo)


async def test_charge_spends_price_from_account_budget(usage_charger, mock_usage_budgets_repo, mock_opened_session):
    await usage_charger.charge(mock_opened_session, USER, PaidOperation.APPLICATION_GENERATION)

    mock_usage_budgets_repo.spend.assert_awaited_once_with(
        mock_opened_session, f"account:{USER_ID}", USAGE_DAY, GENERATION_PRICE, Decimal("5")
    )


async def test_charge_spends_price_from_both_anonymous_budgets(
    usage_charger, mock_usage_budgets_repo, mock_opened_session
):
    await usage_charger.charge(mock_opened_session, ANONYMOUS, PaidOperation.SEMANTIC_SEARCH)

    assert get_awaited_arguments(mock_usage_budgets_repo.spend, "budget_key") == [
        f"ip:{IP_ADDRESS}",
        ANONYMOUS_TOTAL_BUDGET_KEY,
    ]
    assert get_awaited_arguments(mock_usage_budgets_repo.spend, "daily_limit") == [Decimal("2"), Decimal("50")]
    assert get_awaited_arguments(mock_usage_budgets_repo.spend, "amount") == [SEARCH_PRICE, SEARCH_PRICE]


async def test_charge_is_free_for_administrator(usage_charger, mock_usage_budgets_repo, mock_opened_session):
    await usage_charger.charge(mock_opened_session, ADMIN, PaidOperation.APPLICATION_GENERATION)

    mock_usage_budgets_repo.spend.assert_not_awaited()


@pytest.mark.parametrize(("caller", "is_anonymous"), [(USER, False), (ANONYMOUS, True)], ids=("account", "anonymous"))
async def test_charge_over_daily_limit(
    usage_charger, mock_usage_budgets_repo, mock_opened_session, caller, is_anonymous
):
    mock_usage_budgets_repo.spend.return_value = False

    with pytest.raises(UsageLimitExceeded) as error:
        await usage_charger.charge(mock_opened_session, caller, PaidOperation.SEMANTIC_SEARCH)

    assert error.value.is_anonymous == is_anonymous
    assert error.value.retry_after_seconds == SECONDS_TO_NEXT_DAY
    mock_usage_budgets_repo.spend.assert_awaited_once()


async def test_refund_returns_price_to_account_budget(usage_charger, mock_usage_budgets_repo, mock_opened_session):
    await usage_charger.refund(mock_opened_session, USER_ID, PaidOperation.APPLICATION_GENERATION)

    mock_usage_budgets_repo.refund.assert_awaited_once_with(
        mock_opened_session, f"account:{USER_ID}", USAGE_DAY, GENERATION_PRICE
    )
