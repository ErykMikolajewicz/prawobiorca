from typing import Protocol

from src.domain.value_objects.application_templates import ApplicationTemplateDescriptionSource


class ApplicationTemplateInspector(Protocol):
    async def get_variables(self, template: bytes) -> set[str]: ...

    async def get_text(self, template: bytes) -> str: ...


class ApplicationTemplateInstructionsProvider(Protocol):
    async def get_default_instructions(self) -> str: ...


class ApplicationTemplateDescriptionWriter(Protocol):
    async def write(self, description_source: ApplicationTemplateDescriptionSource) -> str: ...
