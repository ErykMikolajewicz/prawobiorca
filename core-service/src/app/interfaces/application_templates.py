from typing import Protocol
from uuid import UUID

from src.app.dtos.application_templates import ApplicationTemplateRepresentation, ApplicationTemplateUploadTarget
from src.app.interfaces.relational import AsyncSession
from src.domain.value_objects.application_templates import (
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from src.domain.value_objects.organizations import OrganizationFilter


class ApplicationTemplatesRepository(Protocol):
    async def list_templates(
        self,
        session: AsyncSession,
        status: ApplicationTemplateStatus | None = None,
        organization_filter: OrganizationFilter | None = None,
    ) -> list[ApplicationTemplateRepresentation]: ...

    async def search_templates(
        self,
        session: AsyncSession,
        status: ApplicationTemplateStatus,
        organization_filter: OrganizationFilter | None,
        vector: list[float],
        threshold: float,
    ) -> list[tuple[ApplicationTemplateRepresentation, float]]: ...

    async def get(self, session: AsyncSession, id_: UUID) -> ApplicationTemplateRepresentation | None: ...

    async def add(self, session: AsyncSession, name: str, instructions: str) -> UUID: ...

    async def confirm_upload(
        self, session: AsyncSession, id_: UUID, fields: list[ApplicationTemplateField]
    ) -> ApplicationTemplateRepresentation | None: ...

    async def set_status(
        self, session: AsyncSession, id_: UUID, status: ApplicationTemplateStatus
    ) -> ApplicationTemplateRepresentation: ...

    async def set_description_status(
        self, session: AsyncSession, id_: UUID, status: ApplicationTemplateDescriptionStatus
    ) -> ApplicationTemplateRepresentation: ...

    async def set_generated_description(
        self, session: AsyncSession, id_: UUID, description: str, vector: list[float]
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
