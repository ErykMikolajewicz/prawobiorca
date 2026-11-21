from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, WithJsonSchema
from pydantic.alias_generators import to_camel

from core_service.domain.value_objects.usage import PaidOperation, UsageTariff

Amount = Annotated[
    Decimal,
    Field(ge=0, max_digits=12, decimal_places=4),
    PlainSerializer(float, return_type=float),
    WithJsonSchema({"type": "number", "minimum": 0}),
]


class UsageTariffData(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    semantic_search_price: Amount
    application_generation_price: Amount
    regulation_preparation_price: Amount
    account_daily_limit: Amount
    anonymous_ip_daily_limit: Amount
    anonymous_total_daily_limit: Amount

    @classmethod
    def from_tariff(cls, tariff: UsageTariff) -> UsageTariffData:
        return cls(
            semantic_search_price=tariff.prices[PaidOperation.SEMANTIC_SEARCH],
            application_generation_price=tariff.prices[PaidOperation.APPLICATION_GENERATION],
            regulation_preparation_price=tariff.prices[PaidOperation.REGULATION_PREPARATION],
            account_daily_limit=tariff.account_daily_limit,
            anonymous_ip_daily_limit=tariff.anonymous_ip_daily_limit,
            anonymous_total_daily_limit=tariff.anonymous_total_daily_limit,
        )

    def to_tariff(self) -> UsageTariff:
        return UsageTariff(
            prices={
                PaidOperation.SEMANTIC_SEARCH: self.semantic_search_price,
                PaidOperation.APPLICATION_GENERATION: self.application_generation_price,
                PaidOperation.REGULATION_PREPARATION: self.regulation_preparation_price,
            },
            account_daily_limit=self.account_daily_limit,
            anonymous_ip_daily_limit=self.anonymous_ip_daily_limit,
            anonymous_total_daily_limit=self.anonymous_total_daily_limit,
        )
