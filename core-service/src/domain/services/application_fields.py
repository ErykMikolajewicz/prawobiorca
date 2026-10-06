import re
from datetime import datetime
from decimal import Decimal, InvalidOperation

from src.domain.exceptions.application_templates import (
    InvalidApplicationFieldsConfig,
    InvalidApplicationFieldValues,
    InvalidApplicationTemplate,
)
from src.domain.value_objects.application_templates import (
    CONTENT_TEMPLATE_VARIABLE,
    RESERVED_TEMPLATE_VARIABLES,
    ApplicationFieldType,
    ApplicationTemplateField,
)

DATE_FORMAT = "%d.%m.%Y"


def create_default_fields(variables: set[str]) -> list[ApplicationTemplateField]:
    if CONTENT_TEMPLATE_VARIABLE not in variables:
        raise InvalidApplicationTemplate(f"Template must contain {CONTENT_TEMPLATE_VARIABLE} variable!")

    return [ApplicationTemplateField(name=name, label=name) for name in sorted(variables - RESERVED_TEMPLATE_VARIABLES)]


def validate_fields_config(field_names: set[str], fields: list[ApplicationTemplateField]) -> None:
    new_field_names = [field.name for field in fields]
    if len(new_field_names) != len(set(new_field_names)) or set(new_field_names) != field_names:
        raise InvalidApplicationFieldsConfig("Fields must match template variables!")

    for field in fields:
        if field.pattern is not None:
            if field.field_type != ApplicationFieldType.TEXT:
                raise InvalidApplicationFieldsConfig(f"Pattern allowed only for text field: {field.name}!")
            try:
                re.compile(field.pattern)
            except re.error:
                raise InvalidApplicationFieldsConfig(f"Invalid pattern for field: {field.name}!")

        if field.field_type == ApplicationFieldType.SELECT and not field.options:
            raise InvalidApplicationFieldsConfig(f"Options required for select field: {field.name}!")
        if field.field_type != ApplicationFieldType.SELECT and field.options:
            raise InvalidApplicationFieldsConfig(f"Options allowed only for select field: {field.name}!")

        if field.default_value is not None and not _is_value_valid(field, field.default_value):
            raise InvalidApplicationFieldsConfig(f"Invalid default value for field: {field.name}!")


def validate_field_values(fields: list[ApplicationTemplateField], values: dict[str, str]) -> dict[str, str]:
    field_names = {field.name for field in fields}
    unknown_field_names = sorted(values.keys() - field_names)
    if unknown_field_names:
        raise InvalidApplicationFieldValues(unknown_field_names)

    validated_values = {}
    invalid_field_names = []
    for field in fields:
        value = values.get(field.name, "").strip()
        if not value:
            if field.required:
                invalid_field_names.append(field.name)
            validated_values[field.name] = ""
            continue

        if not _is_value_valid(field, value):
            invalid_field_names.append(field.name)
            continue

        validated_values[field.name] = value

    if invalid_field_names:
        raise InvalidApplicationFieldValues(invalid_field_names)

    return validated_values


def _is_value_valid(field: ApplicationTemplateField, value: str) -> bool:
    match field.field_type:
        case ApplicationFieldType.TEXT:
            return field.pattern is None or re.fullmatch(field.pattern, value) is not None
        case ApplicationFieldType.NUMBER:
            try:
                return Decimal(value).is_finite()
            except InvalidOperation:
                return False
        case ApplicationFieldType.SELECT:
            return value in field.options
        case ApplicationFieldType.DATE:
            try:
                datetime.strptime(value, DATE_FORMAT)
                return True
            except ValueError:
                return False
