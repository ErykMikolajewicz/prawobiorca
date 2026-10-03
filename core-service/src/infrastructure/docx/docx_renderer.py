from datetime import datetime
from io import BytesIO
from pathlib import Path

import anyio
from docxtpl import DocxTemplate

from src.app.dtos.applications import NewApplication

TEMPLATES_DIR = Path(__file__).parent / "templates" / "applications"


class DocxApplicationRenderer:
    async def render(self, new_application: NewApplication, content: str) -> bytes:
        return await anyio.to_thread.run_sync(self._render, new_application, content)

    @staticmethod
    def _render(new_application: NewApplication, content: str) -> bytes:
        document = DocxTemplate(TEMPLATES_DIR / f"{new_application.application_type.lower()}.docx")
        document.render(
            {
                "current_date": datetime.now().strftime("%d.%m.%Y"),
                "application": new_application,
                "paragraphs": [line.strip() for line in content.splitlines() if line.strip()],
            },
            autoescape=True,
        )
        buffer = BytesIO()
        document.save(buffer)
        return buffer.getvalue()
