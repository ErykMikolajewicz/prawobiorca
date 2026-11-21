from decimal import Decimal

from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core_service.infrastructure.relational_db.schemas.usage_tariff import USAGE_TARIFF_ID, usage_tariff_table


async def insert_usage_tariff(
    session: AsyncSession,
    semantic_search_price: Decimal = Decimal("0.03"),
    application_generation_price: Decimal = Decimal("0.50"),
    regulation_preparation_price: Decimal = Decimal("1.00"),
    account_daily_limit: Decimal = Decimal("5.00"),
    anonymous_ip_daily_limit: Decimal = Decimal("2.00"),
    anonymous_total_daily_limit: Decimal = Decimal("50.00"),
) -> None:
    await session.execute(
        insert(usage_tariff_table).values(
            id=USAGE_TARIFF_ID,
            semantic_search_price=semantic_search_price,
            application_generation_price=application_generation_price,
            regulation_preparation_price=regulation_preparation_price,
            account_daily_limit=account_daily_limit,
            anonymous_ip_daily_limit=anonymous_ip_daily_limit,
            anonymous_total_daily_limit=anonymous_total_daily_limit,
        )
    )
