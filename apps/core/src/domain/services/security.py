import asyncio
import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from math import ceil
from uuid import UUID

import bcrypt
import jwt
from pydantic import SecretStr

from src.domain.exceptions.users import InvalidAccessToken
from src.domain.value_objects.auth import AccessTokenClaims
from src.shared.consts import AUTHORIZATION_TOKEN_LENGTH, SECURITY_MIN_RESPONSE_TIME

url_safe_authorization_token_length = ceil(AUTHORIZATION_TOKEN_LENGTH * 4 / 3)

_required_access_token_claims = ["sub", "sid", "adm", "iat", "exp"]


def hash_password(password: SecretStr) -> bytes:
    password_bytes = password.get_secret_value().encode("utf-8")
    hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed_password


def generate_authorization_token(authorization_token_length: int = AUTHORIZATION_TOKEN_LENGTH) -> str:
    authorization_token = secrets.token_urlsafe(authorization_token_length)
    return authorization_token


def verify_password(password: SecretStr, hashed_password: bytes) -> bool:
    password_bytes = password.get_secret_value().encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_password)


def hash_refresh_token(refresh_token: str) -> str:
    return hashlib.sha256(refresh_token.encode("utf-8")).hexdigest()


def create_access_token(claims: AccessTokenClaims, secret: SecretStr, algorithm: str, expires_in: int) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "sub": str(claims.user_id),
        "sid": str(claims.session_id),
        "adm": claims.is_admin,
        "iat": issued_at,
        "exp": issued_at + timedelta(seconds=expires_in),
        "jti": secrets.token_urlsafe(AUTHORIZATION_TOKEN_LENGTH),
    }
    return jwt.encode(payload, secret.get_secret_value(), algorithm=algorithm)


def decode_access_token(access_token: str, secret: SecretStr, algorithm: str) -> AccessTokenClaims:
    try:
        payload = jwt.decode(
            access_token,
            secret.get_secret_value(),
            algorithms=[algorithm],
            options={"require": _required_access_token_claims},
        )
        claims = AccessTokenClaims(
            user_id=UUID(payload["sub"]), session_id=UUID(payload["sid"]), is_admin=bool(payload["adm"])
        )
    except jwt.InvalidTokenError, ValueError, TypeError:
        raise InvalidAccessToken

    return claims


async def prevent_timing_attack(execution_start_time: float):
    elapsed_execution_time = asyncio.get_event_loop().time() - execution_start_time
    delay = max(0.0, SECURITY_MIN_RESPONSE_TIME - elapsed_execution_time)
    await asyncio.sleep(delay)
