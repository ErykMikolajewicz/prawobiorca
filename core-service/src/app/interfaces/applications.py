from typing import Protocol
from uuid import UUID

from src.app.dtos.applications import ApplicationRepresentation
from src.app.interfaces.relational import AsyncSession
from src.domain.value_objects.applications import ApplicationGenerationStatus, ApplicationType


class ApplicationsRepository(Protocol):
    async def list_by_case_id(
        self, session: AsyncSession, user_id: UUID, case_id: UUID
    ) -> list[ApplicationRepresentation]: ...

    async def list_ids_by_case_id(self, session: AsyncSession, user_id: UUID, case_id: UUID) -> list[UUID]: ...

    async def get(
        self, session: AsyncSession, user_id: UUID, application_id: UUID
    ) -> ApplicationRepresentation | None: ...

    async def add(
        self, session: AsyncSession, user_id: UUID, case_id: UUID, application_type: ApplicationType
    ) -> UUID: ...

    async def set_generation_status(
        self, session: AsyncSession, user_id: UUID, application_id: UUID, status: ApplicationGenerationStatus
    ) -> None: ...

    async def set_name(self, session: AsyncSession, user_id: UUID, application_id: UUID, name: str) -> None: ...

    async def delete(self, session: AsyncSession, user_id: UUID, application_id: UUID) -> None: ...


class ApplicationsStorage(Protocol):
    async def upload_application(self, id_: UUID, file_data: bytes) -> None: ...

    async def delete_application(self, id_: UUID) -> None: ...

    async def get_download_url(self, id_: UUID) -> str: ...
