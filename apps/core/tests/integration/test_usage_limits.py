import asyncio
from datetime import date, timedelta
from decimal import Decimal

import pytest
from fastapi import status
from sqlalchemy import insert, select

from core_service.application.services.usage import get_usage_day
from core_service.domain.services.usage import ANONYMOUS_TOTAL_BUDGET_KEY
from core_service.domain.value_objects.application_templates import ApplicationTemplateStatus
from core_service.domain.value_objects.regulations import RegulationPreparationStatus
from core_service.framework.consts import ACCOUNT_USAGE_LIMIT_EXCEEDED_CODE, ANONYMOUS_USAGE_LIMIT_EXCEEDED_CODE
from core_service.framework.dependencies.client_address import get_trusted_proxies_count
from core_service.infrastructure.relational_db.repositories.usage_budgets import SqlaUsageBudgetsRepository
from core_service.infrastructure.relational_db.schemas.applications import applications_table
from core_service.infrastructure.relational_db.schemas.regulations import regulations_table
from core_service.infrastructure.relational_db.schemas.usage_budgets import usage_budgets_table
from core_service.main import prawobiorca
from tests.consts import IP_ADDRESS, USER_ID
from tests.integration.fixtures.application_templates import insert_application_template
from tests.integration.fixtures.cases import insert_case
from tests.integration.fixtures.regulations import insert_regulation
from tests.integration.fixtures.tasks import execute_task, get_scheduled_tasks
from tests.integration.fixtures.usage import insert_usage_tariff

OTHER_IP_ADDRESS = "198.51.100.4"

SEARCH_PRICE = Decimal("0.03")
GENERATION_PRICE = Decimal("0.50")
PREPARATION_PRICE = Decimal("1.00")


IP_BUDGET_KEY = f"ip:{IP_ADDRESS}"
OTHER_IP_BUDGET_KEY = f"ip:{OTHER_IP_ADDRESS}"
ACCOUNT_BUDGET_KEY = f"account:{USER_ID}"


@pytest.fixture(autouse=True)
async def default_usage_tariff(clean_database, session_maker) -> None:
    async with session_maker.begin() as session:
        await insert_usage_tariff(
            session,
            semantic_search_price=SEARCH_PRICE,
            application_generation_price=GENERATION_PRICE,
            regulation_preparation_price=PREPARATION_PRICE,
            account_daily_limit=Decimal("1.00"),
            anonymous_ip_daily_limit=Decimal("0.06"),
            anonymous_total_daily_limit=Decimal("0.09"),
        )


@pytest.fixture(autouse=True)
def override_trusted_proxies_count(override_dependencies) -> None:
    prawobiorca.dependency_overrides[get_trusted_proxies_count] = lambda: 1


async def get_spent_budgets(session_maker) -> dict[str, Decimal]:
    async with session_maker() as session:
        result = await session.execute(select(usage_budgets_table.c.budget_key, usage_budgets_table.c.spent))
    return {budget.budget_key: budget.spent for budget in result}


async def search(client, ip_address: str = IP_ADDRESS):
    return await client.get(
        "/api/regulations/search",
        params={"query": "zapytanie", "threshold": 0.5},
        headers={"X-Forwarded-For": ip_address},
    )


async def generate_application(client, case_id, template_id):
    return await client.post(
        f"/api/cases/{case_id}/applications",
        json={"templateId": str(template_id), "description": "Proszę o urlop dziekański.", "fieldValues": {}},
    )


async def test_anonymous_search_is_charged_to_address_and_shared_budgets(client, session_maker):
    response = await search(client)

    assert response.status_code == status.HTTP_200_OK
    assert await get_spent_budgets(session_maker) == {
        IP_BUDGET_KEY: SEARCH_PRICE,
        ANONYMOUS_TOTAL_BUDGET_KEY: SEARCH_PRICE,
    }


async def test_anonymous_search_over_address_limit(client, session_maker, mock_texts_embedder):
    await search(client)
    await search(client)

    response = await search(client)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["code"] == ANONYMOUS_USAGE_LIMIT_EXCEEDED_CODE
    assert 0 < int(response.headers["Retry-After"]) <= timedelta(hours=25).total_seconds()
    assert mock_texts_embedder.embed_queries.await_count == 2
    assert (await get_spent_budgets(session_maker))[IP_BUDGET_KEY] == 2 * SEARCH_PRICE


async def test_anonymous_search_from_other_address_has_own_budget(client):
    await search(client)
    await search(client)

    response = await search(client, OTHER_IP_ADDRESS)

    assert response.status_code == status.HTTP_200_OK


async def test_anonymous_search_over_shared_limit(client, session_maker):
    await search(client)
    await search(client)
    await search(client, OTHER_IP_ADDRESS)

    response = await search(client, OTHER_IP_ADDRESS)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["code"] == ANONYMOUS_USAGE_LIMIT_EXCEEDED_CODE
    assert await get_spent_budgets(session_maker) == {
        IP_BUDGET_KEY: 2 * SEARCH_PRICE,
        OTHER_IP_BUDGET_KEY: SEARCH_PRICE,
        ANONYMOUS_TOTAL_BUDGET_KEY: 3 * SEARCH_PRICE,
    }


async def test_logged_user_search_is_charged_to_account(user_client, session_maker):
    response = await search(user_client)

    assert response.status_code == status.HTTP_200_OK
    assert await get_spent_budgets(session_maker) == {ACCOUNT_BUDGET_KEY: SEARCH_PRICE}


async def test_administrator_is_not_charged(admin_client, session_maker):
    response = await search(admin_client)

    assert response.status_code == status.HTTP_200_OK
    assert await get_spent_budgets(session_maker) == {}


async def test_application_generation_over_account_limit(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        template_id = await insert_application_template(session, status=ApplicationTemplateStatus.PUBLISHED)
    await generate_application(user_client, case_id, template_id)
    await generate_application(user_client, case_id, template_id)

    response = await generate_application(user_client, case_id, template_id)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["code"] == ACCOUNT_USAGE_LIMIT_EXCEEDED_CODE
    assert await get_spent_budgets(session_maker) == {ACCOUNT_BUDGET_KEY: 2 * GENERATION_PRICE}
    assert len(await get_scheduled_tasks(session_maker)) == 2
    async with session_maker() as session:
        applications = await session.scalars(select(applications_table.c.id))
    assert len(applications.all()) == 2


async def test_failed_application_generation_is_refunded(
    user_client, session_maker, broker, mock_application_templates_storage, mock_application_writer
):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        template_id = await insert_application_template(session, status=ApplicationTemplateStatus.PUBLISHED)
    mock_application_templates_storage.get_template.return_value = b""
    mock_application_writer.write.side_effect = RuntimeError
    await search(user_client)
    await generate_application(user_client, case_id, template_id)
    (task,) = await get_scheduled_tasks(session_maker)

    with pytest.raises(RuntimeError):
        await execute_task(broker, task)

    assert await get_spent_budgets(session_maker) == {ACCOUNT_BUDGET_KEY: SEARCH_PRICE}


async def test_private_regulation_preparation_over_account_limit(user_client, session_maker, mock_regulations_storage):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID)
        other_regulation_id = await insert_regulation(session, USER_ID)
    mock_regulations_storage.check_regulation_exists.return_value = True
    await user_client.post(f"/api/regulations/{regulation_id}/confirm-upload")

    response = await user_client.post(f"/api/regulations/{other_regulation_id}/confirm-upload")

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert response.json()["code"] == ACCOUNT_USAGE_LIMIT_EXCEEDED_CODE
    assert await get_spent_budgets(session_maker) == {ACCOUNT_BUDGET_KEY: PREPARATION_PRICE}
    assert len(await get_scheduled_tasks(session_maker)) == 1
    async with session_maker() as session:
        preparation_status = await session.scalar(
            select(regulations_table.c.preparation_status).where(regulations_table.c.id == other_regulation_id)
        )
    assert preparation_status == RegulationPreparationStatus.NOT_STARTED


async def test_failed_private_regulation_preparation_is_refunded_and_retry_is_charged(
    user_client, session_maker, broker, mock_regulations_storage, mock_regulation_splitter
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID)
    mock_regulations_storage.check_regulation_exists.return_value = True
    mock_regulations_storage.get_regulation.return_value = b"%PDF"
    mock_regulation_splitter.split.side_effect = RuntimeError
    await user_client.post(f"/api/regulations/{regulation_id}/confirm-upload")
    (task,) = await get_scheduled_tasks(session_maker)

    with pytest.raises(RuntimeError):
        await execute_task(broker, task)

    assert await get_spent_budgets(session_maker) == {ACCOUNT_BUDGET_KEY: Decimal(0)}

    response = await user_client.post(f"/api/regulations/{regulation_id}/preparation-retry")

    assert response.status_code == status.HTTP_202_ACCEPTED
    assert await get_spent_budgets(session_maker) == {ACCOUNT_BUDGET_KEY: PREPARATION_PRICE}


async def test_concurrent_spends_do_not_exceed_daily_limit(session_maker):
    repository = SqlaUsageBudgetsRepository()
    day = get_usage_day()

    async def spend() -> bool:
        async with session_maker.begin() as session:
            return await repository.spend(session, IP_BUDGET_KEY, day, SEARCH_PRICE, 3 * SEARCH_PRICE)

    results = await asyncio.gather(*(spend() for _ in range(10)))

    assert results.count(True) == 3
    assert await get_spent_budgets(session_maker) == {IP_BUDGET_KEY: 3 * SEARCH_PRICE}


async def test_spend_above_daily_limit_of_unused_budget(session_maker):
    async with session_maker.begin() as session:
        is_spent = await SqlaUsageBudgetsRepository().spend(
            session, IP_BUDGET_KEY, get_usage_day(), PREPARATION_PRICE, SEARCH_PRICE
        )

    assert is_spent is False
    assert await get_spent_budgets(session_maker) == {}


async def test_spend_reaching_daily_limit(session_maker):
    async with session_maker.begin() as session:
        is_spent = await SqlaUsageBudgetsRepository().spend(
            session, IP_BUDGET_KEY, get_usage_day(), SEARCH_PRICE, SEARCH_PRICE
        )

    assert is_spent is True


async def test_budget_is_renewed_next_day(session_maker):
    repository = SqlaUsageBudgetsRepository()
    day = date(2026, 11, 16)

    async with session_maker.begin() as session:
        await repository.spend(session, IP_BUDGET_KEY, day, SEARCH_PRICE, SEARCH_PRICE)
        same_day = await repository.spend(session, IP_BUDGET_KEY, day, SEARCH_PRICE, SEARCH_PRICE)
        next_day = await repository.spend(session, IP_BUDGET_KEY, day + timedelta(days=1), SEARCH_PRICE, SEARCH_PRICE)

    assert (same_day, next_day) == (False, True)


async def test_refund_does_not_exceed_spent_amount(session_maker):
    repository = SqlaUsageBudgetsRepository()
    day = get_usage_day()

    async with session_maker.begin() as session:
        await repository.spend(session, ACCOUNT_BUDGET_KEY, day, SEARCH_PRICE, PREPARATION_PRICE)
        await repository.refund(session, ACCOUNT_BUDGET_KEY, day, GENERATION_PRICE)
        await repository.refund(session, IP_BUDGET_KEY, day, GENERATION_PRICE)

    assert await get_spent_budgets(session_maker) == {ACCOUNT_BUDGET_KEY: Decimal(0)}


async def test_delete_budgets_before_day(session_maker):
    day = date(2026, 11, 16)
    async with session_maker.begin() as session:
        await session.execute(
            insert(usage_budgets_table),
            [
                {"budget_key": IP_BUDGET_KEY, "day": day - timedelta(days=1), "spent": SEARCH_PRICE},
                {"budget_key": OTHER_IP_BUDGET_KEY, "day": day, "spent": SEARCH_PRICE},
            ],
        )

        await SqlaUsageBudgetsRepository().delete_before(session, day)

    assert await get_spent_budgets(session_maker) == {OTHER_IP_BUDGET_KEY: SEARCH_PRICE}
