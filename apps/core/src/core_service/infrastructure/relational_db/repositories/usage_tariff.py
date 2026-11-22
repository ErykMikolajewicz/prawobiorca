from sqlalchemy import select, update

from core_service.application.ports.relational import AsyncSession
from core_service.domain.value_objects.usage import PaidOperation, UsageTariff
from core_service.infrastructure.relational_db.schemas.usage_tariff import USAGE_TARIFF_ID, usage_tariff_table
from core_service.infrastructure.relational_db.session import sqla_session


class SqlaUsageTariffRepository:
    @staticmethod
    async def get(session: AsyncSession) -> UsageTariff:
        session = sqla_session(session)
        statement = select(usage_tariff_table).where(usage_tariff_table.c.id == USAGE_TARIFF_ID)
        result = await session.execute(statement)
        row = result.one()
        return UsageTariff(
            prices={
                PaidOperation.SEMANTIC_SEARCH: row.semantic_search_price,
                PaidOperation.APPLICATION_GENERATION: row.application_generation_price,
                PaidOperation.REGULATION_PREPARATION: row.regulation_preparation_price,
            },
            account_daily_limit=row.account_daily_limit,
            anonymous_ip_daily_limit=row.anonymous_ip_daily_limit,
            anonymous_total_daily_limit=row.anonymous_total_daily_limit,
            mcp_monthly_limit=row.mcp_monthly_limit,
        )

    @staticmethod
    async def update(session: AsyncSession, tariff: UsageTariff) -> None:
        session = sqla_session(session)
        statement = (
            update(usage_tariff_table)
            .where(usage_tariff_table.c.id == USAGE_TARIFF_ID)
            .values(
                semantic_search_price=tariff.prices[PaidOperation.SEMANTIC_SEARCH],
                application_generation_price=tariff.prices[PaidOperation.APPLICATION_GENERATION],
                regulation_preparation_price=tariff.prices[PaidOperation.REGULATION_PREPARATION],
                account_daily_limit=tariff.account_daily_limit,
                anonymous_ip_daily_limit=tariff.anonymous_ip_daily_limit,
                anonymous_total_daily_limit=tariff.anonymous_total_daily_limit,
                mcp_monthly_limit=tariff.mcp_monthly_limit,
            )
        )
        await session.execute(statement)
