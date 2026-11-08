from io import BytesIO
from uuid import UUID

from docx import Document
from fastapi import status
from sqlalchemy import select

from core_service.domain.value_objects.application_templates import (
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from core_service.domain.value_objects.applications import ApplicationGenerationStatus
from core_service.infrastructure.relational_db.schemas.application_templates import application_templates_table
from core_service.infrastructure.relational_db.schemas.applications import applications_table
from tests.integration.fixtures.ai_services import DESCRIPTION_VECTOR
from tests.integration.fixtures.application_templates import create_docx_template, insert_application_template
from tests.integration.fixtures.cases import insert_case, insert_case_document
from tests.integration.fixtures.tasks import execute_task, get_scheduled_tasks
from tests.mocks import get_awaited_argument

FIELDS = [
    ApplicationTemplateField(name="department", label="Wydział"),
    ApplicationTemplateField(name="student_id", label="Numer albumu"),
]


async def test_generated_application_is_saved(
    user_client,
    session_maker,
    broker,
    mock_application_templates_storage,
    mock_applications_storage,
    mock_application_writer,
):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        await insert_case_document(session, case_id, presentation_name="Ustawa", content="Art. 1. Student ma prawo.")
        template_id = await insert_application_template(
            session, "Wniosek o urlop", ApplicationTemplateStatus.PUBLISHED, fields=FIELDS, instructions="Instrukcje"
        )
    mock_application_templates_storage.get_template.return_value = create_docx_template()
    mock_application_writer.write.return_value = "Szanowni Państwo,\n\nproszę o urlop dziekański."
    mock_application_writer.write_name.return_value = "Wniosek o urlop dziekański"

    response = await user_client.post(
        f"/api/cases/{case_id}/applications",
        json={
            "templateId": str(template_id),
            "description": "Proszę o urlop dziekański.",
            "fieldValues": {"department": "W4", "student_id": "123456"},
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    application_id = UUID(response.json())
    (task,) = await get_scheduled_tasks(session_maker)

    await execute_task(broker, task)

    legal_basis = get_awaited_argument(mock_application_writer.write, "legal_basis")
    assert [document.content for document in legal_basis] == ["Art. 1. Student ma prawo."]
    assert get_awaited_argument(mock_applications_storage.upload_application, "id_") == application_id
    document = Document(BytesIO(get_awaited_argument(mock_applications_storage.upload_application, "file_data")))
    paragraphs = [paragraph.text for paragraph in document.paragraphs]
    assert paragraphs[0].startswith("123456, W4, ")
    assert paragraphs[1:] == ["Szanowni Państwo,", "proszę o urlop dziekański."]

    async with session_maker() as session:
        result = await session.execute(select(applications_table).where(applications_table.c.id == application_id))
    application = result.one()
    assert application.generation_status == ApplicationGenerationStatus.GENERATED
    assert application.name == "Wniosek o urlop dziekański"


async def test_generated_application_template_description_is_saved(
    admin_client,
    session_maker,
    broker,
    mock_application_templates_storage,
    mock_application_template_description_writer,
):
    async with session_maker.begin() as session:
        template_id = await insert_application_template(
            session, "Wniosek o urlop", fields=FIELDS, instructions="Instrukcje"
        )
    mock_application_templates_storage.get_template.return_value = create_docx_template()
    mock_application_template_description_writer.write.return_value = "Wniosek o urlop dziekański."

    response = await admin_client.post(f"/api/application-templates/{template_id}/description-generation")
    assert response.status_code == status.HTTP_202_ACCEPTED
    (task,) = await get_scheduled_tasks(session_maker)

    await execute_task(broker, task)

    description_source = get_awaited_argument(mock_application_template_description_writer.write, "description_source")
    assert description_source.field_labels == ["Wydział", "Numer albumu"]
    assert "{{ student_id }}" in description_source.content

    async with session_maker() as session:
        result = await session.execute(
            select(application_templates_table).where(application_templates_table.c.id == template_id)
        )
    template = result.one()
    assert template.description == "Wniosek o urlop dziekański."
    assert list(template.description_vector) == DESCRIPTION_VECTOR
    assert template.description_status == ApplicationTemplateDescriptionStatus.GENERATED
