from http.cookies import SimpleCookie

from fastapi import status
from sqlalchemy import select

from src.domain.services.security import hash_refresh_token
from src.infrastructure.relational_db.schemas.users import users_sessions_table
from src.shared.consts import ACCESS_COOKIE_NAME, AUTH_COOKIE_PATH, REFRESH_COOKIE_NAME, REFRESH_COOKIE_PATH
from src.shared.settings.application import app_settings
from tests.consts import STRONG_PASSWORD, VALID_USERNAME

LOGIN_PAYLOAD = {"username": VALID_USERNAME, "password": STRONG_PASSWORD}


def read_auth_cookies(response) -> SimpleCookie:
    cookies = SimpleCookie()
    for set_cookie_header in response.headers.get_list("set-cookie"):
        cookies.load(set_cookie_header)

    return cookies


async def log_in(client) -> SimpleCookie:
    client.cookies.clear()
    response = await client.post("/api/auth/login", data=LOGIN_PAYLOAD)
    assert response.status_code == status.HTTP_200_OK

    return read_auth_cookies(response)


async def count_user_sessions(session_maker) -> int:
    async with session_maker() as session:
        result = await session.execute(select(users_sessions_table))
        return len(result.all())


async def test_login_sets_both_cookies(client, override_session_maker, session_maker, set_user, clean_user):
    cookies = await log_in(client)

    access_cookie = cookies[ACCESS_COOKIE_NAME]
    refresh_cookie = cookies[REFRESH_COOKIE_NAME]

    assert int(access_cookie["max-age"]) == app_settings.ACCESS_TOKEN_EXPIRATION_SECONDS
    assert int(refresh_cookie["max-age"]) == app_settings.REFRESH_TOKEN_EXPIRATION_SECONDS
    assert access_cookie["path"] == AUTH_COOKIE_PATH
    assert refresh_cookie["path"] == REFRESH_COOKIE_PATH
    assert access_cookie["httponly"] and refresh_cookie["httponly"]
    assert access_cookie["samesite"].lower() == app_settings.COOKIE_SAMESITE

    async with session_maker() as session:
        statement = select(users_sessions_table).where(
            users_sessions_table.c.refresh_token_hash == hash_refresh_token(refresh_cookie.value)
        )
        result = await session.execute(statement)
        stored_session = result.one_or_none()

    assert stored_session is not None
    assert stored_session.refresh_token_hash != refresh_cookie.value


async def test_login_failure_wrong_password(client, override_session_maker, session_maker, set_user, clean_user):
    client.cookies.clear()
    payload = {"username": VALID_USERNAME, "password": "WrongPassword123!"}

    response = await client.post("/api/auth/login", data=payload)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "incorrect logging data!"}
    assert await count_user_sessions(session_maker) == 0


async def test_logged_user_is_recognized(client, override_session_maker, session_maker, set_user, clean_user):
    await log_in(client)

    response = await client.get("/api/auth/me")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"isAdmin": False}


async def test_refresh_rotates_tokens(client, override_session_maker, session_maker, set_user, clean_user):
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


async def test_refresh_without_cookie(client, override_session_maker, session_maker, set_user, clean_user):
    client.cookies.clear()

    response = await client.post("/api/auth/refresh")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_logout_deletes_session(client, override_session_maker, session_maker, set_user, clean_user):
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
