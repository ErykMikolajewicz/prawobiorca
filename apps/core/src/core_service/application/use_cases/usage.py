from dataclasses import dataclass

from core_service.application.dtos.usage import UsageTariffData
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.usage import UsageTariffRepository
from core_service.domain.services.usage_access import check_can_manage_usage_tariff
from core_service.domain.value_objects.users import Caller


@dataclass
class GetUsageTariff:
    session_maker: SessionMaker
    usage_tariff_repo: UsageTariffRepository

    async def execute(self, caller: Caller) -> UsageTariffData:
        check_can_manage_usage_tariff(caller)

        async with self.session_maker() as session:
            tariff = await self.usage_tariff_repo.get(session)
        return UsageTariffData.from_tariff(tariff)


@dataclass
class UpdateUsageTariff:
    session_maker: SessionMaker
    usage_tariff_repo: UsageTariffRepository

    async def execute(self, caller: Caller, tariff_data: UsageTariffData) -> None:
        check_can_manage_usage_tariff(caller)

        async with self.session_maker.begin() as session:
            await self.usage_tariff_repo.update(session, tariff_data.to_tariff())
