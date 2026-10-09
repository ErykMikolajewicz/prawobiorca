from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from src.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from src.shared.consts import MAX_FILENAME_LENGTH, MIN_FILENAME_LENGTH


class ApplicationTemplateData(BaseModel):
    name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)


class ApplicationTemplateDetailsData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)
    instructions: str | None = None
    fields: list[ApplicationTemplateField]


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
