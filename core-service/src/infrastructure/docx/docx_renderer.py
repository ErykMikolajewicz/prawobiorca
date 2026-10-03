from datetime import datetime
from io import BytesIO
from pathlib import Path

import anyio
from docxtpl import DocxTemplate

from src.app.dtos.applications import NewApplication

TEMPLATE_PATH = Path(__file__).parent / "templates" / "application.docx"


class DocxApplicationRenderer:
    async def render(self, new_application: NewApplication, content: str) -> bytes:
        return await anyio.to_thread.run_sync(self._render, new_application, content)

    @staticmethod
    def _render(new_application: NewApplication, content: str) -> bytes:
        document = DocxTemplate(TEMPLATE_PATH)
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
