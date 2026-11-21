from decimal import Decimal

import pytest
from fastapi import status
from sqlalchemy import select

from core_service.infrastructure.relational_db.schemas.usage_tariff import usage_tariff_table

NEW_TARIFF = {
    "semanticSearchPrice": 0.05,
    "applicationGenerationPrice": 0.75,
    "regulationPreparationPrice": 1.5,
    "accountDailyLimit": 10,
    "anonymousIpDailyLimit": 3.25,
    "anonymousTotalDailyLimit": 100,
}


async def test_get_usage_tariff(admin_client):
    response = await admin_client.get("/api/usage-tariff")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "semanticSearchPrice": 0.03,
        "applicationGenerationPrice": 0.5,
        "regulationPreparationPrice": 1.0,
        "accountDailyLimit": 5.0,
        "anonymousIpDailyLimit": 2.0,
        "anonymousTotalDailyLimit": 50.0,
    }


async def test_update_usage_tariff(admin_client, session_maker):
    response = await admin_client.put("/api/usage-tariff", json=NEW_TARIFF)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    async with session_maker() as session:
        result = await session.execute(select(usage_tariff_table))
    tariff = result.one()

    assert tariff.semantic_search_price == Decimal("0.05")
    assert tariff.application_generation_price == Decimal("0.75")
    assert tariff.regulation_preparation_price == Decimal("1.5")
    assert tariff.account_daily_limit == Decimal("10")
    assert tariff.anonymous_ip_daily_limit == Decimal("3.25")
    assert tariff.anonymous_total_daily_limit == Decimal("100")


@pytest.mark.parametrize("value", [-0.01, 0.00001, 100_000_000], ids=("negative", "too precise", "too large"))
async def test_update_usage_tariff_with_invalid_value(admin_client, value):
    response = await admin_client.put("/api/usage-tariff", json={**NEW_TARIFF, "accountDailyLimit": value})

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(("method", "body"), [("GET", None), ("PUT", NEW_TARIFF)], ids=("get", "update"))
async def test_usage_tariff_as_normal_user(user_client, method, body):
    response = await user_client.request(method, "/api/usage-tariff", json=body)

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize(("method", "body"), [("GET", None), ("PUT", NEW_TARIFF)], ids=("get", "update"))
async def test_usage_tariff_unlogged(client, method, body):
    response = await client.request(method, "/api/usage-tariff", json=body)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
