from dataclasses import dataclass
from uuid import UUID

from core_service.domain.entities.describable import Describable
from core_service.domain.exceptions.regulations import (
    RegulationAlreadyInitialized,
    RegulationInInvalidState,
    RegulationPreparationInProgress,
)
from core_service.domain.value_objects.descriptions import DescriptionStatus
from core_service.domain.value_objects.regulations import RegulationDetails, RegulationPreparationStatus


@dataclass
class Regulation(Describable):
    id: UUID
    presentation_name: str
    preparation_status: RegulationPreparationStatus = RegulationPreparationStatus.NOT_STARTED
    description: str | None = None
    description_status: DescriptionStatus = DescriptionStatus.NOT_REQUESTED

    @property
    def is_prepared(self) -> bool:
        return self.preparation_status == RegulationPreparationStatus.PREPARED

    def confirm_upload(self) -> None:
        self._schedule_preparation(RegulationPreparationStatus.NOT_STARTED)

    def retry_preparation(self) -> None:
        self._schedule_preparation(RegulationPreparationStatus.FAILED)

    def start_preparation(self) -> None:
        if self.is_prepared:
            raise RegulationAlreadyInitialized
        self.preparation_status = RegulationPreparationStatus.IN_PROGRESS

    def complete_preparation(self) -> None:
        if self.is_prepared:
            raise RegulationAlreadyInitialized
        self.preparation_status = RegulationPreparationStatus.PREPARED

    def fail_preparation(self) -> None:
        if self.is_prepared:
            raise RegulationAlreadyInitialized
        self.preparation_status = RegulationPreparationStatus.FAILED

    def request_description(self) -> None:
        if not self.is_prepared:
            raise RegulationInInvalidState
        super().request_description()

    def update_details(self, details: RegulationDetails) -> None:
        self.presentation_name = details.presentation_name
        self.description = details.description

    def _schedule_preparation(self, allowed_status: RegulationPreparationStatus) -> None:
        if self.is_prepared:
            raise RegulationAlreadyInitialized
        if self.preparation_status == RegulationPreparationStatus.IN_PROGRESS:
            raise RegulationPreparationInProgress
        if self.preparation_status != allowed_status:
            raise RegulationInInvalidState
        self.preparation_status = RegulationPreparationStatus.IN_PROGRESS
