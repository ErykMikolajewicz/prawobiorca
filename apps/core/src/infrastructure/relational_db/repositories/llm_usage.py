from datetime import date

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.relational_db.schemas.llm_usage import llm_usage_table


class LlmUsageRepository:
    @staticmethod
    async def get(session: AsyncSession, month: date) -> tuple[int, int]:
        statement = select(llm_usage_table.c.input_tokens, llm_usage_table.c.output_tokens).where(
            llm_usage_table.c.month == month
        )
        result = await session.execute(statement)
        usage = result.one_or_none()
        if usage is None:
            return 0, 0
        return usage.input_tokens, usage.output_tokens

    @staticmethod
    async def add(session: AsyncSession, month: date, input_tokens: int, output_tokens: int) -> None:
        statement = insert(llm_usage_table).values(month=month, input_tokens=input_tokens, output_tokens=output_tokens)
        statement = statement.on_conflict_do_update(
            index_elements=[llm_usage_table.c.month],
            set_={
                "input_tokens": llm_usage_table.c.input_tokens + statement.excluded.input_tokens,
                "output_tokens": llm_usage_table.c.output_tokens + statement.excluded.output_tokens,
            },
        )
        await session.execute(statement)
