from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class OAuthSettings(BaseSettings):
    PUBLIC_URL: str = "http://localhost:8080"
    REDIRECT_URIS: list[str] = Field(
        default_factory=lambda: [
            "https://claude.ai/api/mcp/auth_callback",
            "http://localhost/callback",
            "http://127.0.0.1/callback",
        ]
    )
    AUTHORIZATION_CODE_EXPIRATION_SECONDS: int = Field(default=60, gt=0)
    ACCESS_TOKEN_EXPIRATION_SECONDS: int = Field(default=3600, gt=0)
    REFRESH_TOKEN_EXPIRATION_SECONDS: int = Field(default=2592000, gt=0)

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        extra="forbid",
        dotenv_filtering="match_prefix",
        case_sensitive=True,
        frozen=True,
        env_prefix="OAUTH_",
    )


oauth_settings = OAuthSettings()
