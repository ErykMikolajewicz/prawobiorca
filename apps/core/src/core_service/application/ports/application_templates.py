from typing import Protocol
from uuid import UUID

from core_service.application.dtos.application_templates import (
    ApplicationTemplateRepresentation,
    ApplicationTemplateUploadTarget,
)
from core_service.application.ports.relational import AsyncSession
from core_service.domain.value_objects.application_templates import (
    ApplicationTemplateDescriptionSource,
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from core_service.domain.value_objects.organizations import OrganizationFilter


class ApplicationTemplatesRepository(Protocol):
    async def list_templates(
        self,
        session: AsyncSession,
        status: ApplicationTemplateStatus | None = None,
        organization_filter: OrganizationFilter | None = None,
    ) -> list[ApplicationTemplateRepresentation]: ...

    async def fuzzy_search_templates(
        self,
        session: AsyncSession,
        status: ApplicationTemplateStatus,
        organization_filter: OrganizationFilter | None,
        query: str,
    ) -> list[ApplicationTemplateRepresentation]: ...

    async def hybrid_search_templates(
        self,
        session: AsyncSession,
        status: ApplicationTemplateStatus,
        organization_filter: OrganizationFilter | None,
        query: str,
        vector: list[float],
    ) -> list[ApplicationTemplateRepresentation]: ...

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

    async def set_description_vector(
        self, session: AsyncSession, id_: UUID, vector: list[float] | None
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


class ApplicationTemplateInspector(Protocol):
    async def get_variables(self, template: bytes) -> set[str]: ...

    async def get_text(self, template: bytes) -> str: ...


class ApplicationTemplateInstructionsProvider(Protocol):
    async def get_default_instructions(self) -> str: ...


class ApplicationTemplateDescriptionWriter(Protocol):
    async def write(self, description_source: ApplicationTemplateDescriptionSource) -> str: ...
