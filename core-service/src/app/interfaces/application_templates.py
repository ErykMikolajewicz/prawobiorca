from typing import Protocol
from uuid import UUID

from src.app.dtos.application_templates import ApplicationTemplateRepresentation, ApplicationTemplateUploadTarget
from src.app.interfaces.relational import AsyncSession
from src.domain.value_objects.application_templates import (
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)


class ApplicationTemplatesRepository(Protocol):
    async def list_templates(
        self, session: AsyncSession, status: ApplicationTemplateStatus | None = None
    ) -> list[ApplicationTemplateRepresentation]: ...

    async def get(self, session: AsyncSession, id_: UUID) -> ApplicationTemplateRepresentation | None: ...

    async def add(self, session: AsyncSession, name: str, instructions: str) -> UUID: ...

    async def set_fields(
        self, session: AsyncSession, id_: UUID, fields: list[ApplicationTemplateField]
    ) -> ApplicationTemplateRepresentation: ...

    async def set_status(
        self, session: AsyncSession, id_: UUID, status: ApplicationTemplateStatus
    ) -> ApplicationTemplateRepresentation: ...

    async def update_details(
        self, session: AsyncSession, id_: UUID, details: ApplicationTemplateDetails
    ) -> ApplicationTemplateRepresentation: ...

    async def delete(self, session: AsyncSession, id_: UUID) -> None: ...


class ApplicationTemplatesStorage(Protocol):
    async def get_upload_target(self, id_: UUID) -> ApplicationTemplateUploadTarget: ...

    async def get_template(self, id_: UUID) -> bytes: ...

    async def delete_template(self, id_: UUID) -> None: ...

    async def get_download_url(self, id_: UUID) -> str: ...
