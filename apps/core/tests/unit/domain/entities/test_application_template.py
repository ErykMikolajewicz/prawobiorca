from uuid import UUID

import pytest

from core_service.domain.entities.application_template import (
    MAX_DESCRIPTION_CONTENT_CHARS,
    MAX_DESCRIPTION_INSTRUCTIONS_CHARS,
    ApplicationTemplate,
)
from core_service.domain.exceptions.application_templates import (
    ApplicationTemplateInInvalidState,
    InvalidApplicationFieldsConfig,
    InvalidApplicationFieldValues,
    InvalidApplicationTemplate,
)
from core_service.domain.exceptions.descriptions import DescriptionGenerationInProgress
from core_service.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateDescriptionSource,
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from core_service.domain.value_objects.descriptions import DescriptionStatus
from tests.consts import ORGANIZATION_ID

TEMPLATE_ID = UUID("7d2e3f4a-5b6c-4d7e-8f9a-0b1c2d3e4f5a")

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


def create_template(
    status: ApplicationTemplateStatus = ApplicationTemplateStatus.DRAFT,
    fields: list[ApplicationTemplateField] | None = None,
    instructions: str | None = "Sporządź wniosek o urlop.",
    description_status: DescriptionStatus = DescriptionStatus.NOT_REQUESTED,
) -> ApplicationTemplate:
    return ApplicationTemplate(
        id=TEMPLATE_ID,
        name="Wniosek o urlop",
        status=status,
        fields=FIELDS if fields is None else fields,
        instructions=instructions,
        description_status=description_status,
    )


def create_details(fields: list[ApplicationTemplateField]) -> ApplicationTemplateDetails:
    return ApplicationTemplateDetails(
        name="Wniosek o stypendium",
        instructions="Instrukcje",
        fields=fields,
        description="Opis.",
        organization_id=ORGANIZATION_ID,
    )


def test_confirm_upload_creates_default_fields_without_reserved_variables():
    template = create_template(ApplicationTemplateStatus.NOT_UPLOADED, fields=[])

    template.confirm_upload({"paragraphs", "current_date", "student_id", "department"})

    assert template.status == ApplicationTemplateStatus.DRAFT
    assert template.fields == [
        ApplicationTemplateField(name="department", label="department"),
        ApplicationTemplateField(name="student_id", label="student_id"),
    ]


def test_confirm_upload_requires_content_variable():
    template = create_template(ApplicationTemplateStatus.NOT_UPLOADED, fields=[])

    with pytest.raises(InvalidApplicationTemplate):
        template.confirm_upload({"student_id"})

    assert template.status == ApplicationTemplateStatus.NOT_UPLOADED


def test_confirm_upload_of_confirmed_template():
    with pytest.raises(ApplicationTemplateInInvalidState):
        create_template().confirm_upload({"paragraphs"})


def test_update_details():
    template = create_template()
    fields = [*FIELDS[1:], ApplicationTemplateField(name="student_id", label="Album")]

    template.update_details(create_details(fields))

    assert template.name == "Wniosek o stypendium"
    assert template.instructions == "Instrukcje"
    assert template.fields == fields
    assert template.description == "Opis."
    assert template.organization_id == ORGANIZATION_ID
    assert template.suborganization_id is None


@pytest.mark.parametrize("status", [ApplicationTemplateStatus.NOT_UPLOADED, ApplicationTemplateStatus.PUBLISHED])
def test_update_details_of_not_draft(status):
    template = create_template(status)

    with pytest.raises(ApplicationTemplateInInvalidState):
        template.update_details(create_details(FIELDS))


@pytest.mark.parametrize(
    "fields",
    [
        FIELDS[:1],
        [*FIELDS, FIELDS[0]],
        [*FIELDS[1:], ApplicationTemplateField(name="other", label="Inne")],
        [*FIELDS[1:], ApplicationTemplateField(name="student_id", label="Numer albumu", options=["a"])],
    ],
    ids=("missing field", "duplicated field", "unknown field", "invalid field"),
)
def test_update_details_with_invalid_fields(fields):
    template = create_template()

    with pytest.raises(InvalidApplicationFieldsConfig):
        template.update_details(create_details(fields))

    assert template.fields == FIELDS


def test_publish():
    template = create_template()

    template.publish()

    assert template.is_published


@pytest.mark.parametrize(
    ("status", "instructions"),
    [
        (ApplicationTemplateStatus.DRAFT, None),
        (ApplicationTemplateStatus.DRAFT, " "),
        (ApplicationTemplateStatus.NOT_UPLOADED, "Instrukcje"),
        (ApplicationTemplateStatus.PUBLISHED, "Instrukcje"),
    ],
)
def test_publish_rejected(status, instructions):
    template = create_template(status, instructions=instructions)

    with pytest.raises(ApplicationTemplateInInvalidState):
        template.publish()

    assert template.status == status


def test_unpublish():
    template = create_template(ApplicationTemplateStatus.PUBLISHED)

    template.unpublish()

    assert template.status == ApplicationTemplateStatus.DRAFT


def test_unpublish_of_not_published():
    with pytest.raises(ApplicationTemplateInInvalidState):
        create_template().unpublish()


def test_request_description():
    template = create_template(description_status=DescriptionStatus.FAILED)

    template.request_description()

    assert template.is_description_in_progress


@pytest.mark.parametrize(
    ("status", "description_status", "error"),
    [
        (ApplicationTemplateStatus.PUBLISHED, DescriptionStatus.NOT_REQUESTED, ApplicationTemplateInInvalidState),
        (ApplicationTemplateStatus.DRAFT, DescriptionStatus.IN_PROGRESS, DescriptionGenerationInProgress),
    ],
    ids=("not draft", "generation in progress"),
)
def test_request_description_rejected(status, description_status, error):
    template = create_template(status, description_status=description_status)

    with pytest.raises(error):
        template.request_description()


def test_create_description_source():
    template = create_template(fields=FIELDS[:3], instructions="  Sporządź wniosek o urlop.  ")

    description_source = template.create_description_source("\nDziekan Wydziału\n")

    assert description_source == ApplicationTemplateDescriptionSource(
        name="Wniosek o urlop",
        instructions="Sporządź wniosek o urlop.",
        field_labels=["Numer albumu", "Semestr", "Wydział"],
        content="Dziekan Wydziału",
    )


def test_create_description_source_without_instructions():
    description_source = create_template(fields=[], instructions=None).create_description_source("")

    assert description_source.instructions == ""
    assert description_source.field_labels == []


def test_create_description_source_truncates_long_texts():
    template = create_template(instructions="a" * (MAX_DESCRIPTION_INSTRUCTIONS_CHARS + 10))

    description_source = template.create_description_source("b" * (MAX_DESCRIPTION_CONTENT_CHARS + 10))

    assert len(description_source.instructions) == MAX_DESCRIPTION_INSTRUCTIONS_CHARS
    assert len(description_source.content) == MAX_DESCRIPTION_CONTENT_CHARS


def test_validate_field_values_returns_values_for_all_fields():
    validated_values = create_template().validate_field_values({**VALID_VALUES, "student_id": " 123456 "})

    assert validated_values == {**VALID_VALUES, "title": ""}


@pytest.mark.parametrize(
    ("values", "invalid_field_names"),
    [
        ({**VALID_VALUES, "student_id": "12345"}, ["student_id"]),
        ({**VALID_VALUES, "semester": "four"}, ["semester"]),
        ({**VALID_VALUES, "department": "W1"}, ["department"]),
        ({**VALID_VALUES, "deadline": "2026-06-30"}, ["deadline"]),
        ({**VALID_VALUES, "student_id": "", "semester": " "}, ["student_id", "semester"]),
        ({**VALID_VALUES, "student_id": "12345", "semester": "four"}, ["student_id", "semester"]),
        ({**VALID_VALUES, "unknown": "value"}, ["unknown"]),
    ],
)
def test_validate_field_values_rejects_invalid_values(values, invalid_field_names):
    with pytest.raises(InvalidApplicationFieldValues) as exception_info:
        create_template().validate_field_values(values)

    assert exception_info.value.field_names == invalid_field_names


def test_get_ai_field_values_skips_fields_not_passed_to_ai_and_empty_values():
    template = create_template(
        fields=[
            ApplicationTemplateField(name="student_id", label="Numer albumu"),
            ApplicationTemplateField(name="pesel", label="PESEL", pass_to_ai=False),
            ApplicationTemplateField(name="title", label="Tytuł", required=False),
            ApplicationTemplateField(name="department", label="Wydział"),
        ]
    )
    values = {"student_id": "123456", "pesel": "90010112345", "title": "", "department": "W4"}

    assert template.get_ai_field_values(values) == [("Numer albumu", "123456"), ("Wydział", "W4")]
