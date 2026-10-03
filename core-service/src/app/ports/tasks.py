from typing import Protocol
from uuid import UUID

from src.app.dtos.applications import NewApplication
from src.app.interfaces.relational import AsyncSession


class RegulationPreparationScheduler(Protocol):
    async def schedule_regulation_preparation(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID
    ) -> None: ...


class ApplicationGenerationScheduler(Protocol):
    async def schedule_application_generation(
        self, session: AsyncSession, user_id: UUID, application_id: UUID, new_application: NewApplication
    ) -> None: ...
