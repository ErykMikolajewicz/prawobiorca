import pytest
from sqlalchemy import select

from core_service.infrastructure.ai_services.llm_cost_limiter import LlmCostLimiter, LlmPricing
from core_service.infrastructure.relational_db.connection import DatabaseSessionMaker
from core_service.infrastructure.relational_db.repositories.llm_usage import SqlaLlmUsageRepository
from core_service.infrastructure.relational_db.schemas.llm_usage import llm_usage_table
from core_service.shared.exceptions import ServiceUnavailable

MILLION = 1_000_000

PRICING = LlmPricing(
    input_price_usd_per_million_tokens=0.30, output_price_usd_per_million_tokens=2.50, usd_to_pln_rate=4.0
)


def create_cost_limiter(session_maker, monthly_limit_pln: float) -> LlmCostLimiter:
    return LlmCostLimiter(DatabaseSessionMaker(session_maker), SqlaLlmUsageRepository(), monthly_limit_pln, PRICING)


async def test_record_accumulates_usage_of_month(session_maker):
    cost_limiter = create_cost_limiter(session_maker, 1.0)

    await cost_limiter.record(100, 20)
    await cost_limiter.record(50, 5)

    async with session_maker() as session:
        result = await session.execute(select(llm_usage_table.c.input_tokens, llm_usage_table.c.output_tokens))

    assert result.all() == [(150, 25)]


async def test_check_allows_month_without_usage(session_maker):
    await create_cost_limiter(session_maker, 0.01).check()


@pytest.mark.parametrize(
    ("input_tokens", "output_tokens", "cost_pln"),
    [
        (MILLION, 0, PRICING.input_price_usd_per_million_tokens * PRICING.usd_to_pln_rate),
        (0, MILLION, PRICING.output_price_usd_per_million_tokens * PRICING.usd_to_pln_rate),
    ],
    ids=("input tokens", "output tokens"),
)
async def test_check_rejects_usage_reaching_monthly_limit(session_maker, input_tokens, output_tokens, cost_pln):
    await create_cost_limiter(session_maker, cost_pln).record(input_tokens, output_tokens)

    await create_cost_limiter(session_maker, cost_pln * 1.01).check()
    with pytest.raises(ServiceUnavailable):
        await create_cost_limiter(session_maker, cost_pln * 0.99).check()
