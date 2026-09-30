from enum import StrEnum
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_SECRETS_DIR = Path("/mnt/secrets-store")


class HttpClientType(StrEnum):
    HTTPX = "HTTPX"


class ApplicationSettings(BaseSettings):
    LOGGING_LEVEL: str = ...

    JWT_SECRET_KEY: SecretStr = Field(..., min_length=32)

    ACCESS_TOKEN_EXPIRATION_SECONDS: int = Field(default=900, gt=0)

    REFRESH_TOKEN_EXPIRATION_SECONDS: int = Field(default=1209600, gt=0)

    COOKIE_SECURE: bool = True

    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"

    HTTP_CLIENT: HttpClientType = HttpClientType.HTTPX

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
