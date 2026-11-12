from fastapi import status
from sqlalchemy import select

from core_service.framework.consts import ACCESS_COOKIE_NAME
from core_service.infrastructure.relational_db.schemas.users import users_table
from tests.consts import STRONG_PASSWORD, VALID_USERNAME


async def test_create_account(client, session_maker):
    payload = {"username": VALID_USERNAME, "password": STRONG_PASSWORD}
    response = await client.post("/api/accounts/register", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    async with session_maker() as session:
        usernames = await session.scalars(select(users_table.c.username))

    assert usernames.all() == [VALID_USERNAME]


async def test_register_and_login_with_password_at_utf8_byte_limit(client):
    payload = {"username": VALID_USERNAME, "password": "Aa1!" + "😀" * 17}

    registered = await client.post("/api/accounts/register", json=payload)
    logged_in = await client.post("/api/auth/login", data=payload)

    assert registered.status_code == status.HTTP_201_CREATED
    assert logged_in.status_code == status.HTTP_200_OK
    assert ACCESS_COOKIE_NAME in logged_in.cookies

    longer_password = await client.post("/api/auth/login", data={**payload, "password": payload["password"] + "a"})

    assert longer_password.status_code == status.HTTP_401_UNAUTHORIZED
