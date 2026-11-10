from io import BytesIO

from docxtpl import DocxTemplate
from fastapi.concurrency import run_in_threadpool
from jinja2.sandbox import SandboxedEnvironment

from core_service.domain.exceptions.application_templates import InvalidApplicationTemplate


class DocxTemplateInspector:
    async def get_variables(self, template: bytes) -> set[str]:
        return await run_in_threadpool(self._get_variables, template)

    @staticmethod
    def _get_variables(template: bytes) -> set[str]:
        try:
            document = DocxTemplate(BytesIO(template))
            return document.get_undeclared_template_variables(jinja_env=SandboxedEnvironment())
        except Exception as e:
            raise InvalidApplicationTemplate("Invalid DOCX template!") from e

    async def get_text(self, template: bytes) -> str:
        return await run_in_threadpool(self._get_text, template)

    @staticmethod
    def _get_text(template: bytes) -> str:
        try:
            document = DocxTemplate(BytesIO(template)).get_docx()
        except Exception as e:
            raise InvalidApplicationTemplate("Invalid DOCX template!") from e

        lines = [paragraph.text for paragraph in document.paragraphs]
        for table in document.tables:
            for row in table.rows:
                lines.extend(cell.text for cell in row.cells)

        return "\n".join(line for line in lines if line.strip())
