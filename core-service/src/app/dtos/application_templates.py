from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from src.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from src.shared.consts import MAX_APPLICATION_TEMPLATE_DESCRIPTION_LENGTH, MAX_FILENAME_LENGTH, MIN_FILENAME_LENGTH


class ApplicationTemplateData(BaseModel):
    name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)


class ApplicationTemplateDetailsData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)
    instructions: str | None = None
    fields: list[ApplicationTemplateField]
    description: str | None = Field(default=None, max_length=MAX_APPLICATION_TEMPLATE_DESCRIPTION_LENGTH)
    organization_id: UUID | None = None
    suborganization_id: UUID | None = None

    @model_validator(mode="after")
    def validate_organization(self):
        if self.organization_id is None and self.suborganization_id is not None:
            raise ValueError("Suborganization given without organization!")
        return self


@dataclass(config=ConfigDict(alias_generator=to_camel))
class ApplicationTemplateUploadTarget:
    id: UUID
    url: str
    fields: dict[str, str]


@dataclass(config=ConfigDict(alias_generator=to_camel, json_schema_serialization_defaults_required=True))
class ApplicationTemplateRepresentation:
    id: UUID
    create_date: datetime
    name: str
    status: ApplicationTemplateStatus
    fields: list[ApplicationTemplateField]
    instructions: str | None = None
    description: str | None = None
    description_status: ApplicationTemplateDescriptionStatus = ApplicationTemplateDescriptionStatus.NOT_REQUESTED
    organization_id: UUID | None = None
    suborganization_id: UUID | None = None


@dataclass(
    config=ConfigDict(alias_generator=to_camel, validate_by_name=True, json_schema_serialization_defaults_required=True)
)
class PublishedApplicationField:
    name: str
    label: str
    field_type: ApplicationFieldType
    required: bool
    default_value: str | None = None
    pattern: str | None = None
    options: list[str] = Field(default_factory=list)


@dataclass(config=ConfigDict(alias_generator=to_camel, validate_by_name=True))
class PublishedApplicationTemplate:
    id: UUID
    name: str
    fields: list[PublishedApplicationField]
    description: str | None = None


@dataclass(config=ConfigDict(alias_generator=to_camel))
class PublishedApplicationTemplateSearchResult:
    template: PublishedApplicationTemplate
    score: float
