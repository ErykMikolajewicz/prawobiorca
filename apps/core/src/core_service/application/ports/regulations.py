from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from core_service.application.dtos.regulations import (
    RegulationRepresentation,
    RegulationSearchResult,
    RegulationUploadTarget,
)
from core_service.application.ports.relational import AsyncSession
from core_service.domain.value_objects.legal_units import RegulationElement
from core_service.domain.value_objects.organizations import OrganizationFilter
from core_service.domain.value_objects.regulations import (
    RegulationDescriptionSource,
    RegulationDescriptionStatus,
    RegulationDetails,
    RegulationOwner,
    RegulationPreparationStatus,
    RegulationRegistrationData,
    RegulationType,
)


class RegulationsStorage(Protocol):
    async def get_regulation(self, id_: UUID) -> bytes: ...

    async def upload_regulation(self, id_: UUID, file_data: bytes) -> None: ...

    async def delete_regulation(self, id_: UUID) -> None: ...

    async def get_download_url(self, id_: UUID) -> str: ...

    async def get_upload_target(self, id_: UUID) -> RegulationUploadTarget: ...

    async def check_regulation_exists(self, id_: UUID) -> bool: ...


class RegulationsRepository(Protocol):
    async def list_regulations(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        regulation_type: RegulationType | None,
        organization_filter: OrganizationFilter | None,
    ) -> list[RegulationRepresentation]: ...

    async def search_regulations(
        self,
        session: AsyncSession,
        user_id: UUID | None,
        regulation_type: RegulationType | None,
        organization_filter: OrganizationFilter | None,
        vector: list[float],
        threshold: float,
    ) -> list[RegulationSearchResult]: ...

    async def register_regulation(
        self, session: AsyncSession, user_id: UUID | None, regulation_registration_data: RegulationRegistrationData
    ) -> UUID: ...

    async def unregister_regulation(self, session: AsyncSession, user_id: UUID | None, id_: UUID) -> None: ...

    async def set_preparation_status(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID, status: RegulationPreparationStatus
    ) -> None: ...

    async def set_description_status(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID, status: RegulationDescriptionStatus
    ) -> None: ...

    async def set_generated_description(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID, description: str, vector: list[float]
    ) -> None: ...

    async def update_regulation_details(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID, regulation_details: RegulationDetails
    ) -> RegulationRepresentation: ...

    async def get_regulation_representation(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID
    ) -> RegulationRepresentation | None: ...

    async def get_regulation_owner(self, session: AsyncSession, id_: UUID) -> RegulationOwner: ...


class RegulationSplitter(Protocol):
    async def split(self, regulation: bytes) -> Iterable[RegulationElement]: ...


class RegulationDescriptionWriter(Protocol):
    async def write(self, description_source: RegulationDescriptionSource) -> str: ...
