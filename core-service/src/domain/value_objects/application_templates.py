from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID

CONTENT_TEMPLATE_VARIABLE = "paragraphs"

CURRENT_DATE_TEMPLATE_VARIABLE = "current_date"

RESERVED_TEMPLATE_VARIABLES = frozenset({CURRENT_DATE_TEMPLATE_VARIABLE, CONTENT_TEMPLATE_VARIABLE})


class ApplicationTemplateStatus(StrEnum):
    NOT_UPLOADED = "NOT_UPLOADED"
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class ApplicationFieldType(StrEnum):
    TEXT = "TEXT"
    NUMBER = "NUMBER"
    SELECT = "SELECT"
    DATE = "DATE"


@dataclass
class ApplicationTemplateField:
    name: str
    label: str
    field_type: ApplicationFieldType = ApplicationFieldType.TEXT
    required: bool = True
    pass_to_ai: bool = True
    default_value: str | None = None
    pattern: str | None = None
    options: list[str] = field(default_factory=list)


@dataclass
class ApplicationTemplateDetails:
    name: str
    instructions: str | None
    fields: list[ApplicationTemplateField]
    organization_id: UUID | None = None
    suborganization_id: UUID | None = None
