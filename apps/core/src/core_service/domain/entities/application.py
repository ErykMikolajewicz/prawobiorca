from dataclasses import dataclass
from uuid import UUID

from core_service.domain.value_objects.applications import ApplicationGenerationStatus


@dataclass
class Application:
    id: UUID
    case_id: UUID
    generation_status: ApplicationGenerationStatus = ApplicationGenerationStatus.IN_PROGRESS
    name: str | None = None

    @property
    def is_generated(self) -> bool:
        return self.generation_status == ApplicationGenerationStatus.GENERATED

    def start_generation(self) -> None:
        self.generation_status = ApplicationGenerationStatus.IN_PROGRESS

    def complete_generation(self, name: str) -> None:
        self.name = name
        self.generation_status = ApplicationGenerationStatus.GENERATED

    def fail_generation(self) -> None:
        self.generation_status = ApplicationGenerationStatus.FAILED
