import asyncio
import time
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID

import jwt
import pytest
from pydantic import SecretStr

from src.domain.exceptions.users import InvalidAccessToken
from src.domain.services.security import (
    create_access_token,
    decode_access_token,
    generate_authorization_token,
    hash_password,
    hash_refresh_token,
    prevent_timing_attack,
    url_safe_authorization_token_length,
    verify_password,
)
from src.domain.value_objects.auth import AccessTokenClaims
from src.shared.consts import SECURITY_MIN_RESPONSE_TIME
from tests.consts import SESSION_ID, STRONG_PASSWORD, USER_ID

SECRET = SecretStr("a" * 32)
OTHER_SECRET = SecretStr("b" * 32)
ALGORITHM = "HS256"


@pytest.fixture
def claims():
    return AccessTokenClaims(user_id=USER_ID, session_id=SESSION_ID, is_admin=True)


def test_access_token_round_trip(claims):
    access_token = create_access_token(claims, SECRET, ALGORITHM, 60)

    assert decode_access_token(access_token, SECRET, ALGORITHM) == claims


def test_access_tokens_are_unique(claims):
    first = create_access_token(claims, SECRET, ALGORITHM, 60)
    second = create_access_token(claims, SECRET, ALGORITHM, 60)

    assert first != second


def test_decode_access_token_with_wrong_secret(claims):
    access_token = create_access_token(claims, SECRET, ALGORITHM, 60)

    with pytest.raises(InvalidAccessToken):
        decode_access_token(access_token, OTHER_SECRET, ALGORITHM)


def test_decode_expired_access_token(claims):
    access_token = create_access_token(claims, SECRET, ALGORITHM, -1)
    time.sleep(0.01)

    with pytest.raises(InvalidAccessToken):
        decode_access_token(access_token, SECRET, ALGORITHM)


@pytest.mark.parametrize(
    "access_token",
    ["", "not-a-jwt", "a.b.c"],
    ids=("empty", "not a jwt", "malformed segments"),
)
def test_decode_malformed_access_token(access_token):
    with pytest.raises(InvalidAccessToken):
        decode_access_token(access_token, SECRET, ALGORITHM)


@pytest.mark.parametrize("missing_claim", ["sub", "sid", "adm", "iat", "exp"])
def test_decode_access_token_without_required_claim(missing_claim):
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(USER_ID),
        "sid": str(SESSION_ID),
        "adm": False,
        "iat": issued_at,
        "exp": issued_at + timedelta(seconds=60),
    }
    del payload[missing_claim]
    access_token = jwt.encode(payload, SECRET.get_secret_value(), algorithm=ALGORITHM)

    with pytest.raises(InvalidAccessToken):
        decode_access_token(access_token, SECRET, ALGORITHM)


async def test_prevent_timing_attack_waits_for_remaining_time():
    elapsed_time = 0.5
    execution_start_time = asyncio.get_running_loop().time() - elapsed_time

    with patch("src.domain.services.security.asyncio.sleep", new_callable=AsyncMock) as sleep:
        await prevent_timing_attack(execution_start_time)

    sleep.assert_awaited_once_with(pytest.approx(SECURITY_MIN_RESPONSE_TIME - elapsed_time, abs=0.1))


async def test_prevent_timing_attack_does_not_wait_after_min_response_time():
    execution_start_time = asyncio.get_running_loop().time() - SECURITY_MIN_RESPONSE_TIME - 1

    with patch("src.domain.services.security.asyncio.sleep", new_callable=AsyncMock) as sleep:
        await prevent_timing_attack(execution_start_time)

    sleep.assert_awaited_once_with(0.0)


def test_hash_refresh_token_is_deterministic():
    refresh_token = generate_authorization_token()

    assert hash_refresh_token(refresh_token) == hash_refresh_token(refresh_token)
    assert hash_refresh_token(refresh_token) != refresh_token
    assert len(hash_refresh_token(refresh_token)) == 64


def test_generate_authorization_token_length():
    assert len(generate_authorization_token()) == url_safe_authorization_token_length


def test_password_hashing_round_trip():
    password = SecretStr(STRONG_PASSWORD)
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password)
    assert not verify_password(SecretStr("OtherPassword12;"), hashed_password)


def test_decode_access_token_with_non_uuid_subject():
    claims = AccessTokenClaims(user_id=UUID(int=0), session_id=SESSION_ID, is_admin=False)
    access_token = create_access_token(claims, SECRET, ALGORITHM, 60)

    assert decode_access_token(access_token, SECRET, ALGORITHM).user_id == UUID(int=0)
