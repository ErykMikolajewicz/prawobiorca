from collections.abc import Iterable
from typing import Protocol
from uuid import UUID

from core_service.application.dtos.regulations import (
    RegulationRepresentation,
    RegulationSearchResult,
    RegulationUploadTarget,
)
from core_service.application.ports.relational import AsyncSession
from core_service.domain.entities.regulation import Regulation
from core_service.domain.value_objects.legal_units import RegulationElement
from core_service.domain.value_objects.organizations import OrganizationFilter
from core_service.domain.value_objects.regulations import (
    RegulationDescriptionSource,
    RegulationOwner,
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

    async def get_for_update(self, session: AsyncSession, user_id: UUID | None, id_: UUID) -> Regulation | None: ...

    async def save(self, session: AsyncSession, regulation: Regulation) -> RegulationRepresentation: ...

    async def set_description_vector(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID, vector: list[float] | None
    ) -> None: ...

    async def get_regulation_representation(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID
    ) -> RegulationRepresentation | None: ...

    async def get_regulation_owner(self, session: AsyncSession, id_: UUID) -> RegulationOwner: ...


class RegulationSplitter(Protocol):
    async def split(self, regulation: bytes) -> Iterable[RegulationElement]: ...


class RegulationDescriptionWriter(Protocol):
    async def write(self, description_source: RegulationDescriptionSource) -> str: ...
