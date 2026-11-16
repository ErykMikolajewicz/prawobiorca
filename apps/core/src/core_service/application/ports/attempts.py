from datetime import datetime
from typing import Protocol

from core_service.application.ports.relational import AsyncSession


class AttemptsRepository(Protocol):
    async def count(self, session: AsyncSession, key: str, window_start: datetime) -> int: ...

    async def add(self, session: AsyncSession, key: str, window_start: datetime, expires_at: datetime) -> None: ...

    async def delete_expired(self, session: AsyncSession, moment: datetime) -> None: ...
