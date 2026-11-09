import pytest

from core_service.domain.exceptions.application_templates import InvalidApplicationFieldsConfig
from core_service.domain.value_objects.application_templates import ApplicationFieldType, ApplicationTemplateField


@pytest.mark.parametrize(
    "field",
    [
        ApplicationTemplateField(name="student_id", label="Numer albumu", pattern=r"\d{6}", default_value="123456"),
        ApplicationTemplateField(
            name="department", label="Wydział", field_type=ApplicationFieldType.SELECT, options=["W4", "W8"]
        ),
    ],
)
def test_check_config_accepts_valid_field(field):
    field.check_config()


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
def test_check_config_rejects_invalid_field(field):
    with pytest.raises(InvalidApplicationFieldsConfig):
        field.check_config()


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        (ApplicationTemplateField(name="field", label="Pole"), "dowolny tekst", True),
        (ApplicationTemplateField(name="field", label="Pole", pattern=r"\d{6}"), "123456", True),
        (ApplicationTemplateField(name="field", label="Pole", pattern=r"\d{6}"), "1234567", False),
        (ApplicationTemplateField(name="field", label="Pole", field_type=ApplicationFieldType.NUMBER), "4.5", True),
        (ApplicationTemplateField(name="field", label="Pole", field_type=ApplicationFieldType.NUMBER), "NaN", False),
        (ApplicationTemplateField(name="field", label="Pole", field_type=ApplicationFieldType.NUMBER), "four", False),
        (
            ApplicationTemplateField(name="field", label="Pole", field_type=ApplicationFieldType.SELECT, options=["a"]),
            "a",
            True,
        ),
        (
            ApplicationTemplateField(name="field", label="Pole", field_type=ApplicationFieldType.SELECT, options=["a"]),
            "b",
            False,
        ),
        (
            ApplicationTemplateField(name="field", label="Pole", field_type=ApplicationFieldType.DATE),
            "30.06.2026",
            True,
        ),
        (
            ApplicationTemplateField(name="field", label="Pole", field_type=ApplicationFieldType.DATE),
            "2026-06-30",
            False,
        ),
    ],
)
def test_accepts(field, value, expected):
    assert field.accepts(value) is expected
