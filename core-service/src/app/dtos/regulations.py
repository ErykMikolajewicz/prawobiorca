from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from src.domain.value_objects.regulations import RegulationPreparationStatus, RegulationType
from src.shared.consts import MAX_FILENAME_LENGTH, MAX_REGULATION_DESCRIPTION_LENGTH, MIN_FILENAME_LENGTH


class RegulationData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)
    regulation_type: RegulationType | None = None


class RegulationDetailsData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)
    description: str | None = Field(default=None, max_length=MAX_REGULATION_DESCRIPTION_LENGTH)


@dataclass(config=ConfigDict(alias_generator=to_camel))
class RegulationUploadTarget:
    id: UUID
    url: str
    fields: dict[str, str]


@dataclass(config=ConfigDict(alias_generator=to_camel, json_schema_serialization_defaults_required=True))
class RegulationRepresentation:
    id: UUID
    create_date: datetime

    presentation_name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)
    description: str | None = None
    regulation_type: RegulationType | None = None
    preparation_status: RegulationPreparationStatus = RegulationPreparationStatus.NOT_STARTED
