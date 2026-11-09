from typing import Protocol
from uuid import UUID

from core_service.application.dtos.application_templates import ApplicationTemplateRepresentation
from core_service.application.dtos.applications import ApplicationRepresentation, NewApplication
from core_service.application.dtos.cases import CaseDocument
from core_service.application.ports.relational import AsyncSession
from core_service.domain.value_objects.applications import ApplicationGenerationStatus


class ApplicationsRepository(Protocol):
    async def list_by_case_id(
        self, session: AsyncSession, user_id: UUID, case_id: UUID
    ) -> list[ApplicationRepresentation]: ...

    async def list_ids_by_case_id(self, session: AsyncSession, user_id: UUID, case_id: UUID) -> list[UUID]: ...

    async def get(
        self, session: AsyncSession, user_id: UUID, application_id: UUID
    ) -> ApplicationRepresentation | None: ...

    async def add(
        self, session: AsyncSession, user_id: UUID, case_id: UUID, template_id: UUID, template_name: str
    ) -> UUID: ...

    async def set_generation_status(
        self, session: AsyncSession, user_id: UUID, application_id: UUID, status: ApplicationGenerationStatus
    ) -> None: ...

    async def set_name(self, session: AsyncSession, user_id: UUID, application_id: UUID, name: str) -> None: ...

    async def delete(self, session: AsyncSession, user_id: UUID, case_id: UUID, application_id: UUID) -> None: ...


class ApplicationsStorage(Protocol):
    async def upload_application(self, id_: UUID, file_data: bytes) -> None: ...

    async def delete_application(self, id_: UUID) -> None: ...

    async def get_download_url(self, id_: UUID) -> str: ...


class ApplicationWriter(Protocol):
    async def write(
        self,
        new_application: NewApplication,
        template: ApplicationTemplateRepresentation,
        legal_basis: list[CaseDocument],
    ) -> str: ...

    async def write_name(self, new_application: NewApplication) -> str: ...


class ApplicationRenderer(Protocol):
    async def render(self, template_content: bytes, new_application: NewApplication, content: str) -> bytes: ...
