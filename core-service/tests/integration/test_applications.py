import asyncio
from datetime import datetime

from fastapi import status
from pydantic import TypeAdapter
from sqlalchemy import insert, select

from src.app.dtos.applications import NewApplication
from src.domain.value_objects.applications import ApplicationGenerationStatus
from src.framework.dependencies.regulations import get_broker
from src.infrastructure.relational_db.schemas.applications import applications_table
from src.infrastructure.relational_db.schemas.cases import cases_table
from src.main import prawobiorca
from src.shared.consts import ACCESS_COOKIE_NAME, APPLICATION_GENERATION_TASK_NAME
from tests.consts import ACCESS_TOKEN, USER_ID

LISTEN_TIMEOUT = 3

NEW_APPLICATION = {
    "description": "Proszę o urlop dziekański.",
    "userName": "Jan Kowalski",
    "studentId": "123456",
    "department": "Wydział Informatyki i Telekomunikacji",
    "semester": "4",
    "title": "inż.",
    "applicationType": "OTHER",
}


async def insert_case(session_maker, name: str = "Case"):
    async with session_maker.begin() as session:
        statement = insert(cases_table).values(user_id=USER_ID, name=name).returning(cases_table.c.id)
        return await session.scalar(statement)


async def insert_application(
    session_maker,
    case_id,
    create_date: datetime = datetime(2026, 1, 1, 10, 0, 0),
    generation_status: ApplicationGenerationStatus = ApplicationGenerationStatus.GENERATED,
):
    async with session_maker.begin() as session:
        statement = (
            insert(applications_table)
            .values(
                case_id=case_id,
                user_id=USER_ID,
                application_type="OTHER",
                create_date=create_date,
                generation_status=generation_status,
            )
            .returning(applications_table.c.id)
        )
        return await session.scalar(statement)


async def test_get_case_applications(
    client, override_session_maker, session_maker, override_authorize_normal_user, set_user, clean_user
):
    case_id = await insert_case(session_maker)
    other_case_id = await insert_case(session_maker, "Other case")
    first_application_id = await insert_application(session_maker, case_id, datetime(2026, 1, 1, 10, 0, 0))
    second_application_id = await insert_application(session_maker, case_id, datetime(2026, 1, 2, 10, 0, 0))
    await insert_application(session_maker, other_case_id)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.get(f"/api/user/cases/{case_id}/applications")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "id": str(second_application_id),
            "caseId": str(case_id),
            "createDate": "2026-01-02T10:00:00",
            "applicationType": "OTHER",
            "generationStatus": "GENERATED",
            "name": None,
        },
        {
            "id": str(first_application_id),
            "caseId": str(case_id),
            "createDate": "2026-01-01T10:00:00",
            "applicationType": "OTHER",
            "generationStatus": "GENERATED",
            "name": None,
        },
    ]


async def test_get_application_download_url(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    override_get_applications_storage,
    mock_applications_storage,
    set_user,
    clean_user,
):
    case_id = await insert_case(session_maker)
    application_id = await insert_application(session_maker, case_id)
    mock_applications_storage.get_download_url.return_value = "http://storage.local/bucket/application"

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.get(f"/api/user/cases/applications/{application_id}/download-url")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "http://storage.local/bucket/application"
    mock_applications_storage.get_download_url.assert_awaited_once_with(application_id)


async def test_get_application_download_url_not_found(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    override_get_applications_storage,
    mock_applications_storage,
    set_user,
    clean_user,
    uuid_generator,
):
    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.get(f"/api/user/cases/applications/{next(uuid_generator)}/download-url")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    mock_applications_storage.get_download_url.assert_not_awaited()


async def test_delete_application(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    override_get_applications_storage,
    mock_applications_storage,
    set_user,
    clean_user,
):
    case_id = await insert_case(session_maker)
    application_id = await insert_application(session_maker, case_id)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.delete(f"/api/user/cases/applications/{application_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_applications_storage.delete_application.assert_awaited_once_with(application_id)

    async with session_maker() as session:
        statement = select(applications_table).where(applications_table.c.id == application_id)
        result = await session.execute(statement)

    assert result.one_or_none() is None


async def test_delete_application_not_found(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    override_get_applications_storage,
    mock_applications_storage,
    set_user,
    clean_user,
    uuid_generator,
):
    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.delete(f"/api/user/cases/applications/{next(uuid_generator)}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    mock_applications_storage.delete_application.assert_not_awaited()


async def test_delete_case_removes_application_files(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    override_get_applications_storage,
    mock_applications_storage,
    set_user,
    clean_user,
):
    case_id = await insert_case(session_maker)
    application_id = await insert_application(session_maker, case_id)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.delete(f"/api/user/cases/{case_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_applications_storage.delete_application.assert_awaited_once_with(application_id)

    async with session_maker() as session:
        statement = select(applications_table).where(applications_table.c.id == application_id)
        result = await session.execute(statement)

    assert result.one_or_none() is None


async def test_generate_application_schedules_task(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    task_broker,
    clean_task_messages,
    set_user,
    clean_user,
):
    prawobiorca.dependency_overrides[get_broker] = lambda: task_broker
    case_id = await insert_case(session_maker)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(f"/api/user/cases/{case_id}/application", json=NEW_APPLICATION)

    assert response.status_code == status.HTTP_202_ACCEPTED
    application_id = response.json()

    async with session_maker() as session:
        statement = select(applications_table).where(applications_table.c.id == application_id)
        application = (await session.execute(statement)).one()

    assert application.case_id == case_id
    assert application.generation_status == ApplicationGenerationStatus.IN_PROGRESS

    delivered = await asyncio.wait_for(anext(task_broker.listen()), LISTEN_TIMEOUT)
    taskiq_message = task_broker.formatter.loads(delivered.data)

    assert taskiq_message.task_name == APPLICATION_GENERATION_TASK_NAME
    user_id, scheduled_application_id, new_application = taskiq_message.args
    assert user_id == str(USER_ID)
    assert scheduled_application_id == application_id
    assert TypeAdapter(NewApplication).validate_python(new_application) == NewApplication(**NEW_APPLICATION)


async def test_generate_application_case_not_found(
    client,
    override_session_maker,
    override_authorize_normal_user,
    override_get_application_generation_scheduler,
    mock_application_generation_scheduler,
    set_user,
    clean_user,
    uuid_generator,
):
    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(f"/api/user/cases/{next(uuid_generator)}/application", json=NEW_APPLICATION)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    mock_application_generation_scheduler.schedule_application_generation.assert_not_awaited()


async def test_get_application_download_url_not_generated(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    override_get_applications_storage,
    mock_applications_storage,
    set_user,
    clean_user,
):
    case_id = await insert_case(session_maker)
    application_id = await insert_application(
        session_maker, case_id, generation_status=ApplicationGenerationStatus.IN_PROGRESS
    )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.get(f"/api/user/cases/applications/{application_id}/download-url")

    assert response.status_code == status.HTTP_409_CONFLICT
    mock_applications_storage.get_download_url.assert_not_awaited()
