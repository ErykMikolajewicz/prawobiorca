import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime

from core_service.infrastructure.relational_db.connection import DatabaseSessionMaker
from core_service.infrastructure.relational_db.repositories.llm_usage import SqlaLlmUsageRepository
from core_service.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LlmPricing:
    input_price_usd_per_million_tokens: float
    output_price_usd_per_million_tokens: float
    usd_to_pln_rate: float


class LlmCostLimiter:
    def __init__(
        self,
        session_maker: DatabaseSessionMaker,
        llm_usage_repo: SqlaLlmUsageRepository,
        monthly_limit_pln: float,
        pricing: LlmPricing,
    ):
        self._session_maker = session_maker
        self._llm_usage_repo = llm_usage_repo
        self._monthly_limit_pln = monthly_limit_pln
        self._pricing = pricing

    async def check(self) -> None:
        async with self._session_maker() as session:
            input_tokens, output_tokens = await self._llm_usage_repo.get(session, self._current_month())

        cost_usd = (
            input_tokens * self._pricing.input_price_usd_per_million_tokens
            + output_tokens * self._pricing.output_price_usd_per_million_tokens
        ) / 1_000_000
        cost_pln = cost_usd * self._pricing.usd_to_pln_rate
        if cost_pln >= self._monthly_limit_pln:
            logger.error("Monthly LLM cost limit exceeded! cost: %.2f PLN", cost_pln)
            raise ServiceUnavailable()

    async def record(self, input_tokens: int, output_tokens: int) -> None:
        async with self._session_maker.begin() as session:
            await self._llm_usage_repo.add(session, self._current_month(), input_tokens, output_tokens)

    @staticmethod
    def _current_month() -> date:
        return datetime.now(UTC).date().replace(day=1)
