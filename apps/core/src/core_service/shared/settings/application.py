from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_SECRETS_DIR = Path("/mnt/secrets-store")


class ApplicationSettings(BaseSettings):
    LOGGING_LEVEL: str

    JWT_SECRET_KEY: SecretStr = Field(..., min_length=32)

    ACCESS_TOKEN_EXPIRATION_SECONDS: int = Field(default=900, gt=0)

    REFRESH_TOKEN_EXPIRATION_SECONDS: int = Field(default=1209600, gt=0)

    COOKIE_SECURE: bool = True

    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    CORS_ORIGINS: list[str] = Field(default_factory=list)

    TRUSTED_PROXIES_COUNT: int = Field(default=0, ge=0)

    LOGIN_MAX_FAILED_ATTEMPTS: int = Field(default=5, gt=0)

    LOGIN_ATTEMPTS_WINDOW_SECONDS: int = Field(default=900, gt=0)

    REGISTRATION_MAX_ATTEMPTS: int = Field(default=20, gt=0)

    REGISTRATION_ATTEMPTS_WINDOW_SECONDS: int = Field(default=86400, gt=0)

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        secrets_dir=_SECRETS_DIR if _SECRETS_DIR.exists() else None,
        extra="forbid",
        dotenv_filtering="match_prefix",
        case_sensitive=True,
        frozen=True,
        env_prefix="APP_",
    )


app_settings = ApplicationSettings()
