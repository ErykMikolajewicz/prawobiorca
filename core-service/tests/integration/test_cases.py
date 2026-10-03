from datetime import datetime
from uuid import UUID

from fastapi import status
from sqlalchemy import insert, select

from src.infrastructure.relational_db.schemas.cases import cases_table
from src.shared.consts import ACCESS_COOKIE_NAME
from tests.consts import ACCESS_TOKEN, ADMIN_ID, USER_ID


async def test_get_cases_list(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    set_user,
    clean_user,
    set_admin_user,
    clean_admin_user,
):
    async with session_maker.begin() as session:
        statement = (
            insert(cases_table)
            .values(
                [
                    {"user_id": USER_ID, "name": "First case", "create_date": datetime(2026, 1, 1, 10, 0, 0)},
                    {"user_id": USER_ID, "name": "Second case", "create_date": datetime(2026, 1, 2, 10, 0, 0)},
                    {"user_id": ADMIN_ID, "name": "Other user case", "create_date": datetime(2026, 1, 3, 10, 0, 0)},
                ]
            )
            .returning(cases_table.c.id)
        )

        result = await session.scalars(statement)

    ids = result.all()

    first_case_id, second_case_id, _ = ids

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.get("/api/user/cases")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {"id": str(second_case_id), "name": "Second case"},
        {"id": str(first_case_id), "name": "First case"},
    ]


async def test_add_case(
    client, override_session_maker, session_maker, override_authorize_normal_user, set_user, clean_user
):
    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post("/api/user/cases", data={"caseName": "New case"})

    assert response.status_code == status.HTTP_200_OK

    case_id = UUID(response.json())

    async with session_maker() as session:
        statement = select(cases_table).where(cases_table.c.id == case_id)
        result = await session.execute(statement)
    case = result.one_or_none()

    assert case is not None
    assert case.id == case_id
    assert case.user_id == USER_ID
    assert case.name == "New case"


async def test_delete_case(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    override_get_applications_storage,
    set_user,
    clean_user,
):
    async with session_maker.begin() as session:
        statement = (
            insert(cases_table)
            .values(
                {"user_id": USER_ID, "name": "Case to delete"},
            )
            .returning(cases_table.c.id)
        )
        case_id = await session.scalar(statement)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.delete(f"/api/user/cases/{case_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    async with session_maker() as session:
        statement = select(cases_table).where(cases_table.c.id == case_id)
        result = await session.execute(statement)
    case = result.one_or_none()

    assert case is None
