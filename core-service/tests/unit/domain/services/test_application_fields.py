import pytest

from src.domain.exceptions.application_templates import (
    InvalidApplicationFieldsConfig,
    InvalidApplicationFieldValues,
    InvalidApplicationTemplate,
)
from src.domain.services.application_fields import (
    create_default_fields,
    validate_field_values,
    validate_fields_config,
)
from src.domain.value_objects.application_templates import ApplicationFieldType, ApplicationTemplateField


def test_create_default_fields_skips_reserved_variables():
    fields = create_default_fields({"paragraphs", "current_date", "student_id", "department"})

    assert fields == [
        ApplicationTemplateField(name="department", label="department"),
        ApplicationTemplateField(name="student_id", label="student_id"),
    ]


def test_create_default_fields_requires_content_variable():
    with pytest.raises(InvalidApplicationTemplate):
        create_default_fields({"student_id"})


def test_validate_fields_config_accepts_valid_config():
    fields = [
        ApplicationTemplateField(name="student_id", label="Numer albumu", pattern=r"\d{6}", default_value="123456"),
        ApplicationTemplateField(
            name="department", label="Wydział", field_type=ApplicationFieldType.SELECT, options=["W4", "W8"]
        ),
    ]

    validate_fields_config({"student_id", "department"}, fields)


@pytest.mark.parametrize(
    "fields",
    [
        [ApplicationTemplateField(name="student_id", label="Numer albumu")],
        [
            ApplicationTemplateField(name="student_id", label="Numer albumu"),
            ApplicationTemplateField(name="student_id", label="Numer albumu"),
            ApplicationTemplateField(name="department", label="Wydział"),
        ],
        [
            ApplicationTemplateField(name="student_id", label="Numer albumu"),
            ApplicationTemplateField(name="other", label="Inne"),
        ],
    ],
)
def test_validate_fields_config_rejects_not_matching_names(fields):
    with pytest.raises(InvalidApplicationFieldsConfig):
        validate_fields_config({"student_id", "department"}, fields)


@pytest.mark.parametrize(
    "field",
    [
        ApplicationTemplateField(name="field", label="Pole", pattern="("),
        ApplicationTemplateField(name="field", label="Pole", field_type=ApplicationFieldType.NUMBER, pattern=r"\d"),
        ApplicationTemplateField(name="field", label="Pole", field_type=ApplicationFieldType.SELECT),
        ApplicationTemplateField(name="field", label="Pole", options=["a"]),
        ApplicationTemplateField(name="field", label="Pole", pattern=r"\d{6}", default_value="abc"),
    ],
)
def test_validate_fields_config_rejects_invalid_field(field):
    with pytest.raises(InvalidApplicationFieldsConfig):
        validate_fields_config({"field"}, [field])


FIELDS = [
    ApplicationTemplateField(name="student_id", label="Numer albumu", pattern=r"\d{6}"),
    ApplicationTemplateField(name="semester", label="Semestr", field_type=ApplicationFieldType.NUMBER),
    ApplicationTemplateField(
        name="department", label="Wydział", field_type=ApplicationFieldType.SELECT, options=["W4", "W8"]
    ),
    ApplicationTemplateField(name="deadline", label="Termin", field_type=ApplicationFieldType.DATE),
    ApplicationTemplateField(name="title", label="Tytuł", required=False),
]

VALID_VALUES = {
    "student_id": "123456",
    "semester": "4",
    "department": "W4",
    "deadline": "30.06.2026",
}


def test_validate_field_values_returns_values_for_all_fields():
    validated_values = validate_field_values(FIELDS, {**VALID_VALUES, "student_id": " 123456 "})

    assert validated_values == {**VALID_VALUES, "title": ""}


@pytest.mark.parametrize(
    ("values", "invalid_field_names"),
    [
        ({**VALID_VALUES, "student_id": "12345"}, ["student_id"]),
        ({**VALID_VALUES, "semester": "four"}, ["semester"]),
        ({**VALID_VALUES, "department": "W1"}, ["department"]),
        ({**VALID_VALUES, "deadline": "2026-06-30"}, ["deadline"]),
        ({**VALID_VALUES, "student_id": "", "semester": " "}, ["student_id", "semester"]),
        ({**VALID_VALUES, "unknown": "value"}, ["unknown"]),
    ],
)
def test_validate_field_values_rejects_invalid_values(values, invalid_field_names):
    with pytest.raises(InvalidApplicationFieldValues) as exception_info:
        validate_field_values(FIELDS, values)

    assert exception_info.value.field_names == invalid_field_names
