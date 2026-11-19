from datetime import datetime
from typing import Protocol

from core_service.application.ports.relational import AsyncSession


class AttemptsRepository(Protocol):
    async def try_acquire(
        self, session: AsyncSession, key: str, window_start: datetime, expires_at: datetime, max_attempts: int
    ) -> bool: ...

    async def release(self, session: AsyncSession, key: str, window_start: datetime) -> None: ...

    async def delete_expired(self, session: AsyncSession, moment: datetime) -> None: ...
