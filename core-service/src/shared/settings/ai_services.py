from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingServiceSettings(BaseSettings):
    URL: str = ...
    BATCH_SIZE: int = Field(default=10, gt=0)

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        extra="forbid",
        dotenv_filtering="match_prefix",
        case_sensitive=True,
        frozen=True,
        env_prefix="EMBEDDING_SERVICE_",
    )


class ExtractionServiceSettings(BaseSettings):
    URL: str = ...

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        extra="forbid",
        dotenv_filtering="match_prefix",
        case_sensitive=True,
        frozen=True,
        env_prefix="EXTRACTION_SERVICE_",
    )


class LlmServiceSettings(BaseSettings):
    URL: str = ...
    MODEL_NAME: str = "qwen-2.5-7b-it"
    TEMPERATURE: float = 0.7
    TOP_P: float = 0.9
    MAX_TOKENS: int = Field(default=1000, gt=0)

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        extra="forbid",
        dotenv_filtering="match_prefix",
        case_sensitive=True,
        frozen=True,
        env_prefix="LLM_SERVICE_",
    )


embedding_service_settings = EmbeddingServiceSettings()
extraction_service_settings = ExtractionServiceSettings()
llm_service_settings = LlmServiceSettings()
