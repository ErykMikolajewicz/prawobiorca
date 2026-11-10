from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from uuid import UUID

import regex

from core_service.domain.exceptions.application_templates import InvalidApplicationFieldsConfig

CONTENT_TEMPLATE_VARIABLE = "paragraphs"

CURRENT_DATE_TEMPLATE_VARIABLE = "current_date"

RESERVED_TEMPLATE_VARIABLES = frozenset({CURRENT_DATE_TEMPLATE_VARIABLE, CONTENT_TEMPLATE_VARIABLE})

DATE_FORMAT = "%d.%m.%Y"

PATTERN_MATCH_TIMEOUT_SECONDS = 0.1


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

    def check_config(self) -> None:
        if self.pattern is not None:
            self._check_pattern(self.pattern)

        is_select = self.field_type == ApplicationFieldType.SELECT
        if is_select and not self.options:
            raise InvalidApplicationFieldsConfig(f"Options required for select field: {self.name}!")
        if not is_select and self.options:
            raise InvalidApplicationFieldsConfig(f"Options allowed only for select field: {self.name}!")

        if self.default_value is not None and not self.accepts(self.default_value):
            raise InvalidApplicationFieldsConfig(f"Invalid default value for field: {self.name}!")

    def accepts(self, value: str) -> bool:
        match self.field_type:
            case ApplicationFieldType.TEXT:
                return self.pattern is None or self._matches_pattern(self.pattern, value)
            case ApplicationFieldType.NUMBER:
                try:
                    return Decimal(value).is_finite()
                except InvalidOperation:
                    return False
            case ApplicationFieldType.SELECT:
                return value in self.options
            case ApplicationFieldType.DATE:
                try:
                    date.strptime(value, DATE_FORMAT)
                    return True
                except ValueError:
                    return False

    @staticmethod
    def _matches_pattern(pattern: str, value: str) -> bool:
        try:
            return regex.fullmatch(pattern, value, timeout=PATTERN_MATCH_TIMEOUT_SECONDS) is not None
        except TimeoutError:
            return False

    def _check_pattern(self, pattern: str) -> None:
        if self.field_type != ApplicationFieldType.TEXT:
            raise InvalidApplicationFieldsConfig(f"Pattern allowed only for text field: {self.name}!")
        try:
            regex.compile(pattern)
        except regex.error:
            raise InvalidApplicationFieldsConfig(f"Invalid pattern for field: {self.name}!")


@dataclass
class ApplicationTemplateDetails:
    name: str
    instructions: str | None
    fields: list[ApplicationTemplateField]
    description: str | None = None
    organization_id: UUID | None = None
    suborganization_id: UUID | None = None


@dataclass
class ApplicationTemplateDescriptionSource:
    name: str
    instructions: str
    field_labels: list[str]
    content: str
