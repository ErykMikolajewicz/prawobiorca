from datetime import UTC, datetime
from uuid import UUID

from fastapi import status
from sqlalchemy import select

from src.infrastructure.relational_db.schemas.applications import applications_table
from src.infrastructure.relational_db.schemas.cases import cases_table
from tests.consts import ADMIN_ID, USER_ID
from tests.integration.fixtures.cases import insert_application, insert_case


async def test_get_cases_list(user_client, session_maker, admin):
    async with session_maker.begin() as session:
        first_case_id = await insert_case(session, name="First case", create_date=datetime(2026, 1, 1, tzinfo=UTC))
        second_case_id = await insert_case(session, name="Second case", create_date=datetime(2026, 1, 2, tzinfo=UTC))
        await insert_case(session, ADMIN_ID, "Other user case", create_date=datetime(2026, 1, 3, tzinfo=UTC))

    response = await user_client.get("/api/cases")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"id": str(second_case_id), "name": "Second case"},
        {"id": str(first_case_id), "name": "First case"},
    ]


async def test_add_case(user_client, session_maker):
    response = await user_client.post("/api/cases", data={"caseName": "New case"})

    assert response.status_code == status.HTTP_200_OK
    case_id = UUID(response.json())

    async with session_maker() as session:
        result = await session.execute(select(cases_table).where(cases_table.c.id == case_id))
    case = result.one()

    assert case.user_id == USER_ID
    assert case.name == "New case"


async def test_delete_case_removes_its_applications(user_client, session_maker, mock_applications_storage):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        application_id = await insert_application(session, case_id)

    response = await user_client.delete(f"/api/cases/{case_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_applications_storage.delete_application.assert_awaited_once_with(application_id)

    async with session_maker() as session:
        case = await session.scalar(select(cases_table.c.id).where(cases_table.c.id == case_id))
        application = await session.scalar(
            select(applications_table.c.id).where(applications_table.c.id == application_id)
        )

    assert case is None
    assert application is None
