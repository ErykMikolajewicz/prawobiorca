from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

from docxtpl import DocxTemplate
from fastapi.concurrency import run_in_threadpool
from jinja2.sandbox import SandboxedEnvironment

from core_service.application.dtos.applications import NewApplication
from core_service.domain.value_objects.application_templates import (
    CONTENT_TEMPLATE_VARIABLE,
    CURRENT_DATE_TEMPLATE_VARIABLE,
    DATE_FORMAT,
)

APPLICATION_TIMEZONE = ZoneInfo("Europe/Warsaw")


class DocxApplicationRenderer:
    async def render(self, template_content: bytes, new_application: NewApplication, content: str) -> bytes:
        return await run_in_threadpool(self._render, template_content, new_application, content)

    @staticmethod
    def _render(template_content: bytes, new_application: NewApplication, content: str) -> bytes:
        document = DocxTemplate(BytesIO(template_content))
        document.render(
            {
                **new_application.field_values,
                CURRENT_DATE_TEMPLATE_VARIABLE: datetime.now(APPLICATION_TIMEZONE).strftime(DATE_FORMAT),
                CONTENT_TEMPLATE_VARIABLE: [line.strip() for line in content.splitlines() if line.strip()],
            },
            jinja_env=SandboxedEnvironment(),
            autoescape=True,
        )
        buffer = BytesIO()
        document.save(buffer)
        return buffer.getvalue()
