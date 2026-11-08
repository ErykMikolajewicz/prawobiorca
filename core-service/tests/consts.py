from uuid import UUID

from src.domain.services.security import create_access_token
from src.domain.value_objects.auth import AccessTokenClaims
from src.shared.consts import JWT_ALGORITHM
from src.shared.settings.application import app_settings

STRONG_PASSWORD = "StrongPassword12;"

VALID_USERNAME = "username123"
ADMIN_USERNAME = "admin123"

USER_ID = UUID("edcd61d8-5026-4f71-850d-b5e072601fb3")
ADMIN_ID = UUID("1a12354a-0f96-4dad-aaf1-b777a5596381")
UNKNOWN_USER_ID = UUID("3f0c1d2e-8a4b-4c6d-9e1f-7b2a5c8d3e40")

SESSION_ID = UUID("6e5a5b3c-1f1b-4f6a-9a4e-2c9c6f0d9b21")

ORGANIZATION_ID = UUID("1b4a1b7a-dbd6-4be4-a52e-80fdd9ddbfb0")
SUBORGANIZATION_ID = UUID("a3f54f36-9653-4ccf-b9f4-81bf885d02ee")

UNKNOWN_ID = UUID("8f7a6b5c-4d3e-4f1a-9b8c-7d6e5f4a3b2c")

REFRESH_TOKEN = "O8KwTwMvXTSn3VdWl6iZlNqmw39UvFRvIbeHfo-mykY"


def build_access_token(user_id: UUID = USER_ID, session_id: UUID = SESSION_ID, is_admin: bool = False) -> str:
    claims = AccessTokenClaims(user_id=user_id, session_id=session_id, is_admin=is_admin)

    return create_access_token(
        claims, app_settings.JWT_SECRET_KEY, JWT_ALGORITHM, app_settings.ACCESS_TOKEN_EXPIRATION_SECONDS
    )


ACCESS_TOKEN = build_access_token()

UNKNOWN_ACCESS_TOKEN = build_access_token(user_id=UNKNOWN_USER_ID)
