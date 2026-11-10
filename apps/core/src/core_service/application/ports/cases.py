from typing import Protocol
from uuid import UUID

from core_service.application.dtos.cases import CaseData, CaseDocument, NewCaseDocument
from core_service.application.ports.relational import AsyncSession


class CasesRepository(Protocol):
    async def list_by_user_id(self, session: AsyncSession, user_id: UUID) -> list[CaseData]: ...

    async def add(self, session: AsyncSession, user_id: UUID, case_name: str) -> UUID: ...

    async def delete(self, session: AsyncSession, user_id: UUID, case_id: UUID) -> None: ...


class CaseDocumentsRepository(Protocol):
    async def list_by_case_id(self, session: AsyncSession, user_id: UUID, case_id: UUID) -> list[CaseDocument]: ...

    async def add(self, session: AsyncSession, user_id: UUID, case_id: UUID, new_document: NewCaseDocument) -> UUID: ...

    async def delete(self, session: AsyncSession, user_id: UUID, case_id: UUID, document_id: UUID) -> None: ...
