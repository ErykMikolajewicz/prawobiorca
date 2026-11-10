from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from core_service.domain.consts import MAX_FILENAME_LENGTH, MAX_REGULATION_DESCRIPTION_LENGTH, MIN_FILENAME_LENGTH
from core_service.domain.value_objects.descriptions import DescriptionStatus
from core_service.domain.value_objects.regulations import (
    RegulationPreparationStatus,
    RegulationScope,
    RegulationType,
)


class RegulationData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    scope: RegulationScope
    name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)
    regulation_type: RegulationType | None = None
    organization_id: UUID | None = None
    suborganization_id: UUID | None = None
    generate_description: bool = False

    @model_validator(mode="after")
    def validate_organization(self):
        if self.scope == RegulationScope.PRIVATE and self.organization_id is not None:
            raise ValueError("Private regulation can't belong to organization!")
        if self.organization_id is None and self.suborganization_id is not None:
            raise ValueError("Suborganization given without organization!")
        return self


class RegulationDetailsData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_REGULATION_DESCRIPTION_LENGTH)


@dataclass(config=ConfigDict(alias_generator=to_camel, validate_by_name=True))
class RegulationUploadTarget:
    id: UUID
    url: str
    fields: dict[str, str]


@dataclass(
    config=ConfigDict(alias_generator=to_camel, validate_by_name=True, json_schema_serialization_defaults_required=True)
)
class RegulationRepresentation:
    id: UUID
    create_date: datetime

    presentation_name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)
    description: str | None = None
    regulation_type: RegulationType | None = None
    preparation_status: RegulationPreparationStatus = RegulationPreparationStatus.NOT_STARTED
    description_status: DescriptionStatus = DescriptionStatus.NOT_REQUESTED
    organization_id: UUID | None = None
    suborganization_id: UUID | None = None


@dataclass(config=ConfigDict(alias_generator=to_camel, validate_by_name=True))
class RegulationSearchResult:
    regulation: RegulationRepresentation
    score: float
