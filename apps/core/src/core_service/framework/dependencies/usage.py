from typing import Annotated

from fastapi import Depends

from core_service.application.ports.usage import UsageBudgetsRepository
from core_service.application.services.usage import UsageCharger
from core_service.domain.value_objects.usage import PaidOperation, UsageTariff
from core_service.infrastructure.relational_db.repositories.usage_budgets import SqlaUsageBudgetsRepository
from core_service.shared.settings.usage import usage_settings


def get_usage_tariff() -> UsageTariff:
    return UsageTariff(
        prices={
            PaidOperation.SEMANTIC_SEARCH: usage_settings.SEMANTIC_SEARCH_PRICE_PLN,
            PaidOperation.APPLICATION_GENERATION: usage_settings.APPLICATION_GENERATION_PRICE_PLN,
            PaidOperation.REGULATION_PREPARATION: usage_settings.REGULATION_PREPARATION_PRICE_PLN,
        },
        account_daily_limit=usage_settings.ACCOUNT_DAILY_LIMIT_PLN,
        anonymous_ip_daily_limit=usage_settings.ANONYMOUS_IP_DAILY_LIMIT_PLN,
        anonymous_total_daily_limit=usage_settings.ANONYMOUS_TOTAL_DAILY_LIMIT_PLN,
    )


def get_usage_budgets_repo() -> UsageBudgetsRepository:
    return SqlaUsageBudgetsRepository()


def get_usage_charger(
    usage_budgets_repo: Annotated[UsageBudgetsRepository, Depends(get_usage_budgets_repo)],
    tariff: Annotated[UsageTariff, Depends(get_usage_tariff)],
) -> UsageCharger:
    return UsageCharger(usage_budgets_repo, tariff)
