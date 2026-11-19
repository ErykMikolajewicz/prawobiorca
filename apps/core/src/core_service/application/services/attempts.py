import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from math import ceil

from core_service.application.ports.attempts import AttemptsRepository
from core_service.application.ports.relational import AsyncSession
from core_service.domain.exceptions.limits import TooManyAttempts
from core_service.domain.value_objects.attempts import AttemptLimit, AttemptReservation

logger = logging.getLogger(__name__)


@dataclass
class AttemptLimiter:
    attempts_repo: AttemptsRepository
    limit: AttemptLimit

    async def acquire(self, session: AsyncSession, key: str) -> AttemptReservation:
        now = datetime.now(UTC)
        window_start = self.limit.get_window_start(now)
        window_end = self.limit.get_window_end(now)
        acquired = await self.attempts_repo.try_acquire(session, key, window_start, window_end, self.limit.max_attempts)
        if not acquired:
            logger.warning("Too many attempts! key: %s", key)
            raise TooManyAttempts(ceil((window_end - now).total_seconds()))
        return AttemptReservation(key, window_start)

    async def release(self, session: AsyncSession, reservation: AttemptReservation) -> None:
        await self.attempts_repo.release(session, reservation.key, reservation.window_start)
