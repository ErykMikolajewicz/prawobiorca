import logging
from datetime import UTC, date, datetime

from src.infrastructure.relational_db.connection import DatabaseSessionMaker
from src.infrastructure.relational_db.repositories.llm_usage import LlmUsageRepository
from src.shared.consts import (
    LLM_INPUT_PRICE_USD_PER_MILLION_TOKENS,
    LLM_OUTPUT_PRICE_USD_PER_MILLION_TOKENS,
    USD_TO_PLN_RATE,
)
from src.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


class LlmCostLimiter:
    def __init__(
        self, session_maker: DatabaseSessionMaker, llm_usage_repo: LlmUsageRepository, monthly_limit_pln: float
    ):
        self._session_maker = session_maker
        self._llm_usage_repo = llm_usage_repo
        self._monthly_limit_pln = monthly_limit_pln

    async def check(self) -> None:
        async with self._session_maker() as session:
            input_tokens, output_tokens = await self._llm_usage_repo.get(session, self._current_month())

        cost_usd = (
            input_tokens * LLM_INPUT_PRICE_USD_PER_MILLION_TOKENS
            + output_tokens * LLM_OUTPUT_PRICE_USD_PER_MILLION_TOKENS
        ) / 1_000_000
        cost_pln = cost_usd * USD_TO_PLN_RATE
        if cost_pln >= self._monthly_limit_pln:
            logger.error("Monthly LLM cost limit exceeded! cost: %.2f PLN", cost_pln)
            raise ServiceUnavailable()

    async def record(self, input_tokens: int, output_tokens: int) -> None:
        async with self._session_maker.begin() as session:
            await self._llm_usage_repo.add(session, self._current_month(), input_tokens, output_tokens)

    @staticmethod
    def _current_month() -> date:
        return datetime.now(UTC).date().replace(day=1)
