from src.domain.value_objects.application_templates import (
    ApplicationTemplateDescriptionSource,
    ApplicationTemplateField,
)

MAX_DESCRIPTION_INSTRUCTIONS_CHARS = 4000

MAX_DESCRIPTION_CONTENT_CHARS = 4000


def create_description_source(
    name: str, instructions: str | None, fields: list[ApplicationTemplateField], content: str
) -> ApplicationTemplateDescriptionSource:
    return ApplicationTemplateDescriptionSource(
        name=name,
        instructions=(instructions or "").strip()[:MAX_DESCRIPTION_INSTRUCTIONS_CHARS],
        field_labels=[field.label for field in fields],
        content=content.strip()[:MAX_DESCRIPTION_CONTENT_CHARS],
    )
