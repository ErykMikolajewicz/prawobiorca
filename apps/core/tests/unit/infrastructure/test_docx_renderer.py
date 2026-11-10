from datetime import datetime
from io import BytesIO
from uuid import UUID

import pytest
from docx import Document

from core_service.application.dtos.applications import NewApplication
from core_service.domain.value_objects.application_templates import DATE_FORMAT
from core_service.infrastructure.docx.docx_renderer import APPLICATION_TIMEZONE, DocxApplicationRenderer

TEMPLATE_ID = UUID("6f7a8b9c-0d1e-4f2a-8b3c-4d5e6f7a8b9c")


def create_template() -> bytes:
    document = Document()
    document.add_paragraph("{{ student_name }}, {{ current_date }}")
    document.add_paragraph("{%p for paragraph in paragraphs %}")
    document.add_paragraph("{{ paragraph }}")
    document.add_paragraph("{%p endfor %}")
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


async def render(student_name: str, content: str) -> list[str]:
    new_application = NewApplication(
        template_id=TEMPLATE_ID, description="Opis sytuacji.", field_values={"student_name": student_name}
    )

    rendered = await DocxApplicationRenderer().render(create_template(), new_application, content)

    return [paragraph.text for paragraph in Document(BytesIO(rendered)).paragraphs]


async def test_render_fills_fields_date_and_content_paragraphs():
    paragraphs = await render("Jan Kowalski", "Szanowni Państwo,\n\n   proszę o urlop dziekański.  \n")

    today = datetime.now(APPLICATION_TIMEZONE).strftime(DATE_FORMAT)
    assert paragraphs == [f"Jan Kowalski, {today}", "Szanowni Państwo,", "proszę o urlop dziekański."]


@pytest.mark.parametrize("text", ["Kowalski & <Syn>", "{{ 7 * 7 }}"], ids=("xml characters", "template syntax"))
async def test_render_keeps_user_text_literally(text):
    paragraphs = await render(text, text)

    assert paragraphs[0].startswith(f"{text}, ")
    assert paragraphs[1:] == [text]
