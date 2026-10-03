from typing import Protocol
from uuid import UUID

from src.app.dtos.regulations import RegulationRepresentation, RegulationUploadTarget
from src.app.interfaces.relational import AsyncSession
from src.domain.value_objects.regulations import (
    RegulationDetails,
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
    def __init__(self): ...

    async def list_regulations(
        self, session: AsyncSession, user_id: UUID | None, regulation_type: RegulationType | None
    ) -> list[RegulationRepresentation]: ...

    async def register_regulation(
        self, session: AsyncSession, user_id: UUID | None, regulation_registration_data: RegulationRegistrationData
    ) -> UUID: ...

    async def unregister_regulation(self, session: AsyncSession, user_id: UUID | None, id_: UUID) -> None: ...

    async def set_preparation_status(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID, status: RegulationPreparationStatus
    ) -> None: ...

    async def update_regulation_details(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID, regulation_details: RegulationDetails
    ) -> RegulationRepresentation: ...

    async def get_regulation_representation(
        self, session: AsyncSession, user_id: UUID | None, id_: UUID
    ) -> RegulationRepresentation | None: ...
