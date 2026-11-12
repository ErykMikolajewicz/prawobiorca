from http.cookies import SimpleCookie

import pytest
from fastapi import status
from sqlalchemy import select

from core_service.domain.services.security import hash_refresh_token
from core_service.framework.consts import ACCESS_COOKIE_NAME, AUTH_COOKIE_PATH, REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH
from core_service.infrastructure.relational_db.schemas.users import users_sessions_table
from core_service.shared.settings.application import app_settings
from tests.consts import AUTH_TOKENS_CONFIG, STRONG_PASSWORD, VALID_USERNAME, build_access_token
from tests.fixtures.clients import create_client

LOGIN_PAYLOAD = {"username": VALID_USERNAME, "password": STRONG_PASSWORD}


def read_auth_cookies(response) -> SimpleCookie:
    cookies = SimpleCookie()
    for set_cookie_header in response.headers.get_list("set-cookie"):
        cookies.load(set_cookie_header)

    return cookies


async def log_in(client) -> SimpleCookie:
    response = await client.post("/api/auth/login", data=LOGIN_PAYLOAD)
    assert response.status_code == status.HTTP_200_OK

    return read_auth_cookies(response)


async def count_user_sessions(session_maker) -> int:
    async with session_maker() as session:
        result = await session.execute(select(users_sessions_table))
        return len(result.all())


async def test_login_sets_both_cookies(client, session_maker, user):
    cookies = await log_in(client)

    access_cookie = cookies[ACCESS_COOKIE_NAME]
    refresh_cookie = cookies[REFRESH_COOKIE_NAME]

    assert int(access_cookie["max-age"]) == AUTH_TOKENS_CONFIG.access_token_expiration_seconds
    assert int(refresh_cookie["max-age"]) == AUTH_TOKENS_CONFIG.refresh_token_expiration_seconds
    assert access_cookie["path"] == AUTH_COOKIE_PATH
    assert refresh_cookie["path"] == REFRESH_COOKIE_PATH
    assert access_cookie["httponly"]
    assert refresh_cookie["httponly"]
    assert access_cookie["samesite"].lower() == app_settings.COOKIE_SAMESITE

    async with session_maker() as session:
        statement = select(users_sessions_table).where(
            users_sessions_table.c.refresh_token_hash == hash_refresh_token(refresh_cookie.value)
        )
        result = await session.execute(statement)
        stored_session = result.one_or_none()

    assert stored_session is not None
    assert stored_session.refresh_token_hash != refresh_cookie.value


@pytest.mark.parametrize("password", ["WrongPassword123!", "x", "nouppercase1!", "Aa1!" + "😀" * 20])
async def test_login_failure_wrong_password(client, session_maker, user, password):
    payload = {"username": VALID_USERNAME, "password": password}

    response = await client.post("/api/auth/login", data=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "incorrect logging data!"}
    assert await count_user_sessions(session_maker) == 0


async def test_logged_user_is_recognized(client, user):
    await log_in(client)

    response = await client.get("/api/auth/me")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"isAdmin": False}


async def test_refresh_rotates_tokens(client, session_maker, user):
    login_cookies = await log_in(client)
    old_refresh_token = login_cookies[REFRESH_COOKIE_NAME].value

    response = await client.post("/api/auth/refresh")

    assert response.status_code == status.HTTP_200_OK
    refreshed_cookies = read_auth_cookies(response)
    new_refresh_token = refreshed_cookies[REFRESH_COOKIE_NAME].value

    assert new_refresh_token != old_refresh_token
    assert refreshed_cookies[ACCESS_COOKIE_NAME].value != login_cookies[ACCESS_COOKIE_NAME].value
    auth_response = await client.get("/api/auth/me")
    assert auth_response.status_code == status.HTTP_200_OK
    assert await count_user_sessions(session_maker) == 1

    client.cookies.clear()
    client.cookies.set(REFRESH_COOKIE_NAME, old_refresh_token, path=REFRESH_COOKIE_PATH)
    replayed_response = await client.post("/api/auth/refresh")

    assert replayed_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_refresh_without_cookie(client):
    response = await client.post("/api/auth/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_logout_deletes_session(client, session_maker, user):
    await log_in(client)

    response = await client.post("/api/auth/logout")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"ok": True}
    assert await count_user_sessions(session_maker) == 0

    cleared_cookies = read_auth_cookies(response)
    assert cleared_cookies[ACCESS_COOKIE_NAME].value == ""
    assert cleared_cookies[REFRESH_COOKIE_NAME].value == ""

    refresh_response = await client.post("/api/auth/refresh")
    assert refresh_response.status_code == status.HTTP_401_UNAUTHORIZED

    auth_response = await client.get("/api/auth/me")
    assert auth_response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_expired_access_token_is_rejected(user):
    async with create_client(build_access_token(expires_in=-1)) as client:
        response = await client.get("/api/auth/me")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
