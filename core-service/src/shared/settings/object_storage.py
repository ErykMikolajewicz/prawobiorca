from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_SECRETS_DIR = Path("/mnt/secrets-store")


class ObjectStorageSettings(BaseSettings):
    ENDPOINT_URL: str = ...
    PUBLIC_ENDPOINT_URL: str = ""
    REGION: str = ...
    ACCESS_KEY: str = ...
    SECRET_KEY: str = ...
    BUCKET: str = ...
    SIGNED_URL_EXPIRATION_SECONDS: int = 3600
    MAX_FILE_SIZE_BYTES: int = 10485760

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        secrets_dir=_SECRETS_DIR if _SECRETS_DIR.exists() else None,
        extra="forbid",
        dotenv_filtering="match_prefix",
        case_sensitive=True,
        frozen=True,
        env_prefix="OBJECT_STORAGE_",
    )


object_storage_settings = ObjectStorageSettings()
