from core_service.domain.exceptions.descriptions import DescriptionGenerationInProgress
from core_service.domain.value_objects.descriptions import DescriptionStatus


class Describable:
    description: str | None
    description_status: DescriptionStatus

    @property
    def is_description_in_progress(self) -> bool:
        return self.description_status == DescriptionStatus.IN_PROGRESS

    @property
    def is_description_generated(self) -> bool:
        return self.description_status == DescriptionStatus.GENERATED

    def request_description(self) -> None:
        if self.is_description_in_progress:
            raise DescriptionGenerationInProgress
        self.description_status = DescriptionStatus.IN_PROGRESS

    def start_description_generation(self) -> None:
        self.description_status = DescriptionStatus.IN_PROGRESS

    def complete_description_generation(self, description: str) -> None:
        self.description = description
        self.description_status = DescriptionStatus.GENERATED

    def fail_description_generation(self) -> None:
        self.description_status = DescriptionStatus.FAILED
