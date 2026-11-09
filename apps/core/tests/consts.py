from uuid import UUID

from pydantic import SecretStr

from core_service.application.use_cases.auth import AuthTokensConfig
from core_service.domain.services.security import create_access_token
from core_service.domain.value_objects.auth import AccessTokenClaims
from core_service.shared.consts import JWT_ALGORITHM

STRONG_PASSWORD = "StrongPassword12;"

VALID_USERNAME = "username123"
ADMIN_USERNAME = "admin123"

USER_ID = UUID("edcd61d8-5026-4f71-850d-b5e072601fb3")
ADMIN_ID = UUID("1a12354a-0f96-4dad-aaf1-b777a5596381")

SESSION_ID = UUID("6e5a5b3c-1f1b-4f6a-9a4e-2c9c6f0d9b21")

ORGANIZATION_ID = UUID("1b4a1b7a-dbd6-4be4-a52e-80fdd9ddbfb0")
SUBORGANIZATION_ID = UUID("a3f54f36-9653-4ccf-b9f4-81bf885d02ee")

UNKNOWN_ID = UUID("8f7a6b5c-4d3e-4f1a-9b8c-7d6e5f4a3b2c")

REFRESH_TOKEN = "O8KwTwMvXTSn3VdWl6iZlNqmw39UvFRvIbeHfo-mykY"

AUTH_TOKENS_CONFIG = AuthTokensConfig(
    jwt_secret_key=SecretStr("test-jwt-secret-key-with-32-chars"),
    access_token_expiration_seconds=900,
    refresh_token_expiration_seconds=1209600,
)


def build_access_token(
    user_id: UUID = USER_ID,
    session_id: UUID = SESSION_ID,
    is_admin: bool = False,
    expires_in: int = AUTH_TOKENS_CONFIG.access_token_expiration_seconds,
) -> str:
    claims = AccessTokenClaims(user_id=user_id, session_id=session_id, is_admin=is_admin)

    return create_access_token(claims, AUTH_TOKENS_CONFIG.jwt_secret_key, JWT_ALGORITHM, expires_in)


ACCESS_TOKEN = build_access_token()
ADMIN_ACCESS_TOKEN = build_access_token(ADMIN_ID, is_admin=True)
