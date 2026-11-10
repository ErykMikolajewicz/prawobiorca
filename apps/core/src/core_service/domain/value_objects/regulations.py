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


@dataclass
class RegulationRegistrationData:
    presentation_name: str
    regulation_type: RegulationType | None = None
    organization_id: UUID | None = None
    suborganization_id: UUID | None = None
    description_status: DescriptionStatus = DescriptionStatus.NOT_REQUESTED


@dataclass
class RegulationDetails:
    presentation_name: str
    description: str | None = None


@dataclass
class RegulationOwner:
    user_id: UUID | None


@dataclass
class SectionContent:
    header: str | None
    text: str


@dataclass
class RegulationHeading:
    text: str
    level: int


@dataclass
class RegulationDescriptionSource:
    presentation_name: str
    headings: list[RegulationHeading]
    beginning: str
