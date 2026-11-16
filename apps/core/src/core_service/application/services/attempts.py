import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from math import ceil

from core_service.application.ports.attempts import AttemptsRepository
from core_service.application.ports.relational import AsyncSession
from core_service.domain.exceptions.limits import TooManyAttempts
from core_service.domain.value_objects.attempts import AttemptLimit

logger = logging.getLogger(__name__)


@dataclass
class AttemptLimiter:
    attempts_repo: AttemptsRepository
    limit: AttemptLimit

    async def check(self, session: AsyncSession, key: str) -> None:
        now = datetime.now(UTC)
        attempts = await self.attempts_repo.count(session, key, self.limit.get_window_start(now))
        if attempts >= self.limit.max_attempts:
            logger.warning("Too many attempts! key: %s", key)
            raise TooManyAttempts(ceil((self.limit.get_window_end(now) - now).total_seconds()))

    async def record(self, session: AsyncSession, key: str) -> None:
        now = datetime.now(UTC)
        await self.attempts_repo.add(session, key, self.limit.get_window_start(now), self.limit.get_window_end(now))
