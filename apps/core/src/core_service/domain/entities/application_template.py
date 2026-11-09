from dataclasses import dataclass, field
from uuid import UUID

from core_service.domain.entities.describable import Describable
from core_service.domain.exceptions.application_templates import (
    ApplicationTemplateInInvalidState,
    InvalidApplicationFieldsConfig,
    InvalidApplicationFieldValues,
    InvalidApplicationTemplate,
)
from core_service.domain.value_objects.application_templates import (
    CONTENT_TEMPLATE_VARIABLE,
    RESERVED_TEMPLATE_VARIABLES,
    ApplicationTemplateDescriptionSource,
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from core_service.domain.value_objects.descriptions import DescriptionStatus

MAX_DESCRIPTION_INSTRUCTIONS_CHARS = 4000

MAX_DESCRIPTION_CONTENT_CHARS = 4000


@dataclass
class ApplicationTemplate(Describable):
    id: UUID
    name: str
    status: ApplicationTemplateStatus = ApplicationTemplateStatus.NOT_UPLOADED
    fields: list[ApplicationTemplateField] = field(default_factory=list)
    instructions: str | None = None
    description: str | None = None
    description_status: DescriptionStatus = DescriptionStatus.NOT_REQUESTED
    organization_id: UUID | None = None
    suborganization_id: UUID | None = None

    @property
    def is_published(self) -> bool:
        return self.status == ApplicationTemplateStatus.PUBLISHED

    def confirm_upload(self, variables: set[str]) -> None:
        if self.status != ApplicationTemplateStatus.NOT_UPLOADED:
            raise ApplicationTemplateInInvalidState
        if CONTENT_TEMPLATE_VARIABLE not in variables:
            raise InvalidApplicationTemplate(f"Template must contain {CONTENT_TEMPLATE_VARIABLE} variable!")

        self.fields = [
            ApplicationTemplateField(name=name, label=name) for name in sorted(variables - RESERVED_TEMPLATE_VARIABLES)
        ]
        self.status = ApplicationTemplateStatus.DRAFT

    def update_details(self, details: ApplicationTemplateDetails) -> None:
        self._check_draft()
        self._check_fields_config(details.fields)

        self.name = details.name
        self.instructions = details.instructions
        self.fields = details.fields
        self.description = details.description
        self.organization_id = details.organization_id
        self.suborganization_id = details.suborganization_id

    def publish(self) -> None:
        self._check_draft()
        if not (self.instructions or "").strip():
            raise ApplicationTemplateInInvalidState
        self.status = ApplicationTemplateStatus.PUBLISHED

    def unpublish(self) -> None:
        if not self.is_published:
            raise ApplicationTemplateInInvalidState
        self.status = ApplicationTemplateStatus.DRAFT

    def request_description(self) -> None:
        self._check_draft()
        super().request_description()

    def create_description_source(self, content: str) -> ApplicationTemplateDescriptionSource:
        return ApplicationTemplateDescriptionSource(
            name=self.name,
            instructions=(self.instructions or "").strip()[:MAX_DESCRIPTION_INSTRUCTIONS_CHARS],
            field_labels=[template_field.label for template_field in self.fields],
            content=content.strip()[:MAX_DESCRIPTION_CONTENT_CHARS],
        )

    def validate_field_values(self, values: dict[str, str]) -> dict[str, str]:
        unknown_field_names = sorted(values.keys() - {template_field.name for template_field in self.fields})
        if unknown_field_names:
            raise InvalidApplicationFieldValues(unknown_field_names)

        validated_values = {}
        invalid_field_names = []
        for template_field in self.fields:
            value = values.get(template_field.name, "").strip()
            if not value:
                if template_field.required:
                    invalid_field_names.append(template_field.name)
                validated_values[template_field.name] = ""
                continue

            if not template_field.accepts(value):
                invalid_field_names.append(template_field.name)
                continue

            validated_values[template_field.name] = value

        if invalid_field_names:
            raise InvalidApplicationFieldValues(invalid_field_names)

        return validated_values

    def get_ai_field_values(self, values: dict[str, str]) -> list[tuple[str, str]]:
        return [
            (template_field.label, values[template_field.name])
            for template_field in self.fields
            if template_field.pass_to_ai and values.get(template_field.name)
        ]

    def _check_draft(self) -> None:
        if self.status != ApplicationTemplateStatus.DRAFT:
            raise ApplicationTemplateInInvalidState

    def _check_fields_config(self, fields: list[ApplicationTemplateField]) -> None:
        new_field_names = [template_field.name for template_field in fields]
        current_field_names = {template_field.name for template_field in self.fields}
        if len(new_field_names) != len(set(new_field_names)) or set(new_field_names) != current_field_names:
            raise InvalidApplicationFieldsConfig("Fields must match template variables!")

        for template_field in fields:
            template_field.check_config()
