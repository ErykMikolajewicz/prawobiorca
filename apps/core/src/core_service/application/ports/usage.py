from datetime import date
from decimal import Decimal
from typing import Protocol

from core_service.application.ports.relational import AsyncSession
from core_service.domain.value_objects.usage import UsageTariff


class UsageBudgetsRepository(Protocol):
    async def spend(
        self, session: AsyncSession, budget_key: str, day: date, amount: Decimal, limit: Decimal
    ) -> bool: ...

    async def refund(self, session: AsyncSession, budget_key: str, day: date, amount: Decimal) -> None: ...

    async def delete_before(self, session: AsyncSession, day: date) -> None: ...


class UsageTariffRepository(Protocol):
    async def get(self, session: AsyncSession) -> UsageTariff: ...

    async def update(self, session: AsyncSession, tariff: UsageTariff) -> None: ...
