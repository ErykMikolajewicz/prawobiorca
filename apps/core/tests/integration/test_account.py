from fastapi import status
from sqlalchemy import select

from src.infrastructure.relational_db.schemas.users import users_table
from tests.consts import STRONG_PASSWORD, VALID_USERNAME


async def test_create_account(client, session_maker):
    payload = {"username": VALID_USERNAME, "password": STRONG_PASSWORD}
    response = await client.post("/api/accounts/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    async with session_maker() as session:
        usernames = await session.scalars(select(users_table.c.username))

    assert usernames.all() == [VALID_USERNAME]
