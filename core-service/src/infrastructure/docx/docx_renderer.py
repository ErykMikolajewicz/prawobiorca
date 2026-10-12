from datetime import datetime
from io import BytesIO

import anyio
from docxtpl import DocxTemplate
from jinja2.sandbox import SandboxedEnvironment

from src.app.dtos.applications import NewApplication
from src.domain.services.application_fields import DATE_FORMAT
from src.domain.value_objects.application_templates import CONTENT_TEMPLATE_VARIABLE, CURRENT_DATE_TEMPLATE_VARIABLE


class DocxApplicationRenderer:
    async def render(self, template_content: bytes, new_application: NewApplication, content: str) -> bytes:
        return await anyio.to_thread.run_sync(self._render, template_content, new_application, content)

    @staticmethod
    def _render(template_content: bytes, new_application: NewApplication, content: str) -> bytes:
        document = DocxTemplate(BytesIO(template_content))
        document.render(
            {
                **new_application.field_values,
                CURRENT_DATE_TEMPLATE_VARIABLE: datetime.now().strftime(DATE_FORMAT),
                CONTENT_TEMPLATE_VARIABLE: [line.strip() for line in content.splitlines() if line.strip()],
            },
            jinja_env=SandboxedEnvironment(),
            autoescape=True,
        )
        buffer = BytesIO()
        document.save(buffer)
        return buffer.getvalue()
