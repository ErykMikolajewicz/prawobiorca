from typing import Annotated

from fastapi import APIRouter, Depends, status

from core_service.application.dtos.usage import UsageTariffData
from core_service.application.use_cases.usage import GetUsageTariff, UpdateUsageTariff
from core_service.domain.value_objects.users import Caller
from core_service.framework.dependencies.authentication import get_caller
from core_service.framework.dependencies.usage import get_get_usage_tariff, get_update_usage_tariff

usage_router = APIRouter(tags=["usage"], prefix="/api")


@usage_router.get(
    "/usage-tariff",
    response_model=UsageTariffData,
)
async def get_usage_tariff(
    caller: Annotated[Caller, Depends(get_caller)],
    get_usage_tariff_: Annotated[GetUsageTariff, Depends(get_get_usage_tariff)],
) -> UsageTariffData:
    return await get_usage_tariff_.execute(caller)


@usage_router.put(
    "/usage-tariff",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_usage_tariff(
    caller: Annotated[Caller, Depends(get_caller)],
    update_usage_tariff_: Annotated[UpdateUsageTariff, Depends(get_update_usage_tariff)],
    tariff_data: UsageTariffData,
):
    await update_usage_tariff_.execute(caller, tariff_data)
