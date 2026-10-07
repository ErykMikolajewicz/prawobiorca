from typing import Protocol

from src.app.dtos.application_templates import ApplicationTemplateRepresentation
from src.app.dtos.applications import NewApplication
from src.app.dtos.cases import CaseDocument


class ApplicationWriter(Protocol):
    async def write(
        self,
        new_application: NewApplication,
        template: ApplicationTemplateRepresentation,
        legal_basis: list[CaseDocument],
    ) -> str: ...

    async def write_name(self, new_application: NewApplication) -> str: ...


class ApplicationRenderer(Protocol):
    async def render(self, template_content: bytes, new_application: NewApplication, content: str) -> bytes: ...
