from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from core_service.domain.value_objects.descriptions import DescriptionStatus


class RegulationType(StrEnum):
    ACT = "ACT"
    DECREE = "DECREE"
    STATUTE = "STATUTE"


class RegulationScope(StrEnum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class RegulationPreparationStatus(StrEnum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    PREPARED = "PREPARED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class RegulationRegistrationData:
    presentation_name: str
    regulation_type: RegulationType | None = None
    organization_id: UUID | None = None
    suborganization_id: UUID | None = None
    description_status: DescriptionStatus = DescriptionStatus.NOT_REQUESTED


@dataclass(frozen=True)
class RegulationDetails:
    presentation_name: str
    description: str | None = None


@dataclass(frozen=True)
class RegulationOwner:
    user_id: UUID | None


@dataclass(frozen=True)
class SectionContent:
    header: str | None
    text: str


@dataclass(frozen=True)
class RegulationHeading:
    text: str
    level: int


@dataclass(frozen=True)
class RegulationDescriptionSource:
    presentation_name: str
    headings: list[RegulationHeading]
    beginning: str
