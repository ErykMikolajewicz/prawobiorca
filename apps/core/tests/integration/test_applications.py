from datetime import UTC, datetime

from fastapi import status
from pydantic import TypeAdapter
from sqlalchemy import select

from core_service.application.dtos.applications import NewApplication
from core_service.domain.value_objects.application_templates import ApplicationTemplateField, ApplicationTemplateStatus
from core_service.domain.value_objects.applications import ApplicationGenerationStatus
from core_service.infrastructure.relational_db.schemas.applications import applications_table
from core_service.shared.consts import APPLICATION_GENERATION_TASK_NAME
from tests.consts import ADMIN_ID, UNKNOWN_ID, USER_ID
from tests.integration.fixtures.application_templates import insert_application_template
from tests.integration.fixtures.cases import insert_application, insert_case
from tests.integration.fixtures.tasks import get_scheduled_tasks

FIELDS = [ApplicationTemplateField(name="student_id", label="Numer albumu", pattern=r"\d{6}")]


def create_new_application(template_id, field_values: dict[str, str] | None = None):
    return {
        "templateId": str(template_id),
        "description": "Proszę o urlop dziekański.",
        "fieldValues": field_values or {"student_id": "123456"},
    }


async def insert_template(session, template_status: ApplicationTemplateStatus = ApplicationTemplateStatus.PUBLISHED):
    return await insert_application_template(
        session, "Wniosek o urlop", template_status, fields=FIELDS, instructions="Instrukcje"
    )


async def test_get_case_applications(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        other_case_id = await insert_case(session, name="Other case")
        first_application_id = await insert_application(
            session, case_id, create_date=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC)
        )
        second_application_id = await insert_application(
            session, case_id, create_date=datetime(2026, 1, 2, 10, 0, 0, tzinfo=UTC)
        )
        await insert_application(session, other_case_id)

    response = await user_client.get(f"/api/cases/{case_id}/applications")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": str(second_application_id),
            "caseId": str(case_id),
            "createDate": "2026-01-02T10:00:00Z",
            "templateName": "Wniosek o urlop",
            "generationStatus": "GENERATED",
            "name": None,
        },
        {
            "id": str(first_application_id),
            "caseId": str(case_id),
            "createDate": "2026-01-01T10:00:00Z",
            "templateName": "Wniosek o urlop",
            "generationStatus": "GENERATED",
            "name": None,
        },
    ]


async def test_get_application_download_url(user_client, session_maker, mock_applications_storage):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        application_id = await insert_application(session, case_id)
    mock_applications_storage.get_download_url.return_value = "http://storage.local/bucket/applications"

    response = await user_client.get(f"/api/cases/{case_id}/applications/{application_id}/download-url")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "http://storage.local/bucket/applications"


async def test_get_application_download_url_not_found(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)

    response = await user_client.get(f"/api/cases/{case_id}/applications/{UNKNOWN_ID}/download-url")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_application_download_url_not_generated(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        application_id = await insert_application(session, case_id, ApplicationGenerationStatus.IN_PROGRESS)

    response = await user_client.get(f"/api/cases/{case_id}/applications/{application_id}/download-url")

    assert response.status_code == status.HTTP_409_CONFLICT


async def test_delete_application(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        application_id = await insert_application(session, case_id)

    response = await user_client.delete(f"/api/cases/{case_id}/applications/{application_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    async with session_maker() as session:
        application = await session.scalar(
            select(applications_table.c.id).where(applications_table.c.id == application_id)
        )

    assert application is None


async def test_delete_application_of_other_case(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        other_case_id = await insert_case(session)
        application_id = await insert_application(session, case_id)

    response = await user_client.delete(f"/api/cases/{other_case_id}/applications/{application_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_generate_application_schedules_task(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        template_id = await insert_template(session)

    response = await user_client.post(f"/api/cases/{case_id}/applications", json=create_new_application(template_id))

    assert response.status_code == status.HTTP_202_ACCEPTED
    application_id = response.json()

    async with session_maker() as session:
        result = await session.execute(select(applications_table).where(applications_table.c.id == application_id))
    application = result.one()

    assert application.case_id == case_id
    assert application.template_name == "Wniosek o urlop"
    assert application.generation_status == ApplicationGenerationStatus.IN_PROGRESS

    (task,) = await get_scheduled_tasks(session_maker)
    user_id, scheduled_application_id, new_application = task.args

    assert task.task_name == APPLICATION_GENERATION_TASK_NAME
    assert user_id == str(USER_ID)
    assert scheduled_application_id == application_id
    assert TypeAdapter(NewApplication).validate_python(new_application) == NewApplication(
        **create_new_application(template_id)
    )


async def test_generate_application_case_not_found(user_client, session_maker):
    async with session_maker.begin() as session:
        template_id = await insert_template(session)

    response = await user_client.post(f"/api/cases/{UNKNOWN_ID}/applications", json=create_new_application(template_id))

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_generate_application_in_other_user_case(user_client, session_maker, admin):
    async with session_maker.begin() as session:
        case_id = await insert_case(session, ADMIN_ID)
        template_id = await insert_template(session)

    response = await user_client.post(f"/api/cases/{case_id}/applications", json=create_new_application(template_id))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert await get_scheduled_tasks(session_maker) == []


async def test_generate_application_template_not_published(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        template_id = await insert_template(session, ApplicationTemplateStatus.DRAFT)

    response = await user_client.post(f"/api/cases/{case_id}/applications", json=create_new_application(template_id))

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_generate_application_invalid_field_values(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        template_id = await insert_template(session)

    response = await user_client.post(
        f"/api/cases/{case_id}/applications", json=create_new_application(template_id, {"student_id": "abc"})
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"] == ["student_id"]
