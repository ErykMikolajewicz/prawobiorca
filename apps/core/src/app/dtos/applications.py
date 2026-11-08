from datetime import datetime
from uuid import UUID

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from src.domain.value_objects.applications import ApplicationGenerationStatus


@dataclass(config=ConfigDict(alias_generator=to_camel, validate_by_name=True))
class NewApplication:
    template_id: UUID
    description: str = Field(min_length=1)
    field_values: dict[str, str] = Field(default_factory=dict)


@dataclass(config=ConfigDict(alias_generator=to_camel))
class ApplicationRepresentation:
    id: UUID
    case_id: UUID
    create_date: datetime
    template_name: str
    generation_status: ApplicationGenerationStatus
    name: str | None
