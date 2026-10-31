from src.domain.services.application_template_description import (
    MAX_DESCRIPTION_CONTENT_CHARS,
    MAX_DESCRIPTION_INSTRUCTIONS_CHARS,
    create_description_source,
)
from src.domain.value_objects.application_templates import (
    ApplicationTemplateDescriptionSource,
    ApplicationTemplateField,
)


def test_create_description_source():
    fields = [
        ApplicationTemplateField(name="student_name", label="Imię i nazwisko"),
        ApplicationTemplateField(name="faculty", label="Wydział"),
    ]

    description_source = create_description_source(
        "Wniosek o urlop", "  Sporządź wniosek o urlop.  ", fields, "\nDziekan Wydziału\n"
    )

    assert description_source == ApplicationTemplateDescriptionSource(
        name="Wniosek o urlop",
        instructions="Sporządź wniosek o urlop.",
        field_labels=["Imię i nazwisko", "Wydział"],
        content="Dziekan Wydziału",
    )


def test_create_description_source_without_instructions():
    description_source = create_description_source("Wniosek o urlop", None, [], "")

    assert description_source.instructions == ""
    assert description_source.field_labels == []


def test_create_description_source_truncates_long_texts():
    description_source = create_description_source(
        "Wniosek o urlop",
        "a" * (MAX_DESCRIPTION_INSTRUCTIONS_CHARS + 10),
        [],
        "b" * (MAX_DESCRIPTION_CONTENT_CHARS + 10),
    )

    assert len(description_source.instructions) == MAX_DESCRIPTION_INSTRUCTIONS_CHARS
    assert len(description_source.content) == MAX_DESCRIPTION_CONTENT_CHARS
