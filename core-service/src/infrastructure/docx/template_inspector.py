from io import BytesIO

import anyio
from docxtpl import DocxTemplate
from jinja2.sandbox import SandboxedEnvironment

from src.domain.exceptions.application_templates import InvalidApplicationTemplate


class DocxTemplateInspector:
    async def get_variables(self, template: bytes) -> set[str]:
        return await anyio.to_thread.run_sync(self._get_variables, template)

    @staticmethod
    def _get_variables(template: bytes) -> set[str]:
        try:
            document = DocxTemplate(BytesIO(template))
            return document.get_undeclared_template_variables(jinja_env=SandboxedEnvironment())
        except Exception:
            raise InvalidApplicationTemplate("Invalid DOCX template!")
