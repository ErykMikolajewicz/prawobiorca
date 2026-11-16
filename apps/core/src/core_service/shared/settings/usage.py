from decimal import Decimal
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class UsageSettings(BaseSettings):
    SEMANTIC_SEARCH_PRICE_PLN: Decimal = Field(default=Decimal("0.03"), ge=0)
    APPLICATION_GENERATION_PRICE_PLN: Decimal = Field(default=Decimal("0.50"), ge=0)
    REGULATION_PREPARATION_PRICE_PLN: Decimal = Field(default=Decimal("1.00"), ge=0)

    ACCOUNT_DAILY_LIMIT_PLN: Decimal = Field(default=Decimal("5.00"), ge=0)
    ANONYMOUS_IP_DAILY_LIMIT_PLN: Decimal = Field(default=Decimal("2.00"), ge=0)
    ANONYMOUS_TOTAL_DAILY_LIMIT_PLN: Decimal = Field(default=Decimal("50.00"), ge=0)

    model_config = SettingsConfigDict(
        env_file=Path(".env"),
        extra="forbid",
        dotenv_filtering="match_prefix",
        case_sensitive=True,
        frozen=True,
        env_prefix="USAGE_",
    )


usage_settings = UsageSettings()
