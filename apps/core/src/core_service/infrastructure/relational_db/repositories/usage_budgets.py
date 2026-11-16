from datetime import date
from decimal import Decimal

from sqlalchemy import delete, func, update
from sqlalchemy.dialects.postgresql import insert

from core_service.application.ports.relational import AsyncSession
from core_service.infrastructure.relational_db.schemas.usage_budgets import usage_budgets_table
from core_service.infrastructure.relational_db.session import sqla_session


class SqlaUsageBudgetsRepository:
    @staticmethod
    async def spend(session: AsyncSession, budget_key: str, day: date, amount: Decimal, daily_limit: Decimal) -> bool:
        session = sqla_session(session)
        if amount > daily_limit:
            return False

        statement = insert(usage_budgets_table).values(budget_key=budget_key, day=day, spent=amount)
        spent = usage_budgets_table.c.spent + statement.excluded.spent
        statement = statement.on_conflict_do_update(
            index_elements=[usage_budgets_table.c.budget_key, usage_budgets_table.c.day],
            set_={"spent": spent},
            where=spent <= daily_limit,
        ).returning(usage_budgets_table.c.spent)

        result = await session.execute(statement)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def refund(session: AsyncSession, budget_key: str, day: date, amount: Decimal) -> None:
        session = sqla_session(session)
        statement = (
            update(usage_budgets_table)
            .where(usage_budgets_table.c.budget_key == budget_key, usage_budgets_table.c.day == day)
            .values(spent=func.greatest(usage_budgets_table.c.spent - amount, 0))
        )
        await session.execute(statement)

    @staticmethod
    async def delete_before(session: AsyncSession, day: date) -> None:
        session = sqla_session(session)
        await session.execute(delete(usage_budgets_table).where(usage_budgets_table.c.day < day))
