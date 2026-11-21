from typing import Annotated

from fastapi import Depends

from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.usage import UsageBudgetsRepository, UsageTariffRepository
from core_service.application.services.usage import UsageCharger
from core_service.application.use_cases.usage import GetUsageTariff, UpdateUsageTariff
from core_service.framework.dependencies.relational import get_session_maker
from core_service.infrastructure.relational_db.repositories.usage_budgets import SqlaUsageBudgetsRepository
from core_service.infrastructure.relational_db.repositories.usage_tariff import SqlaUsageTariffRepository


def get_usage_budgets_repo() -> UsageBudgetsRepository:
    return SqlaUsageBudgetsRepository()


def get_usage_tariff_repo() -> UsageTariffRepository:
    return SqlaUsageTariffRepository()


def get_usage_charger(
    usage_budgets_repo: Annotated[UsageBudgetsRepository, Depends(get_usage_budgets_repo)],
    usage_tariff_repo: Annotated[UsageTariffRepository, Depends(get_usage_tariff_repo)],
) -> UsageCharger:
    return UsageCharger(usage_budgets_repo, usage_tariff_repo)


def get_get_usage_tariff(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    usage_tariff_repo: Annotated[UsageTariffRepository, Depends(get_usage_tariff_repo)],
) -> GetUsageTariff:
    return GetUsageTariff(session_maker, usage_tariff_repo)


def get_update_usage_tariff(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    usage_tariff_repo: Annotated[UsageTariffRepository, Depends(get_usage_tariff_repo)],
) -> UpdateUsageTariff:
    return UpdateUsageTariff(session_maker, usage_tariff_repo)
