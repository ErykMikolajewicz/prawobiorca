from typing import Protocol
from uuid import UUID

from src.app.interfaces.relational import AsyncSession


class RegulationPreparationScheduler(Protocol):
    async def schedule_regulation_preparation(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID
    ) -> None: ...
