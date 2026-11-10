import logging
from dataclasses import dataclass
from uuid import UUID

from core_service.application.dtos.cases import CaseData, CaseDocument, NewCaseDocument
from core_service.application.ports.applications import ApplicationsRepository, ApplicationsStorage
from core_service.application.ports.cases import CaseDocumentsRepository, CasesRepository
from core_service.application.ports.relational import SessionMaker
from core_service.domain.exceptions.cases import CaseDocumentNotFound, CaseNotFound
from core_service.domain.services.case_access import resolve_case_owner
from core_service.domain.value_objects.users import Caller

logger = logging.getLogger(__name__)


@dataclass
class ListCases:
    session_maker: SessionMaker
    cases_repo: CasesRepository

    async def execute(self, caller: Caller) -> list[CaseData]:
        user_id = resolve_case_owner(caller)

        async with self.session_maker() as session:
            cases = await self.cases_repo.list_by_user_id(session, user_id)
        return cases


@dataclass
class DeleteCase:
    session_maker: SessionMaker
    cases_repo: CasesRepository
    applications_repo: ApplicationsRepository
    applications_storage: ApplicationsStorage

    async def execute(self, caller: Caller, case_id: UUID) -> None:
        user_id = resolve_case_owner(caller)

        async with self.session_maker.begin() as session:
            application_ids = await self.applications_repo.list_ids_by_case_id(session, user_id, case_id)
            try:
                await self.cases_repo.delete(session, user_id, case_id)
            except CaseNotFound:
                logger.warning("Case not found!")
                raise

        for application_id in application_ids:
            try:
                await self.applications_storage.delete_application(application_id)
            except Exception:
                logger.exception("Failed to remove from storage application: %s", application_id)


@dataclass
class AddCase:
    session_maker: SessionMaker
    cases_repo: CasesRepository

    async def execute(self, caller: Caller, case_name: str) -> UUID:
        user_id = resolve_case_owner(caller)

        async with self.session_maker.begin() as session:
            case_id = await self.cases_repo.add(session, user_id, case_name)
        return case_id


@dataclass
class AddCaseDocument:
    session_maker: SessionMaker
    case_documents_repo: CaseDocumentsRepository

    async def execute(self, caller: Caller, case_id: UUID, new_document: NewCaseDocument) -> None:
        user_id = resolve_case_owner(caller)

        async with self.session_maker.begin() as session:
            try:
                await self.case_documents_repo.add(session, user_id, case_id, new_document)
            except CaseNotFound:
                logger.warning("No case with that id!")
                raise


@dataclass
class DeleteCaseDocument:
    session_maker: SessionMaker
    case_documents_repo: CaseDocumentsRepository

    async def execute(self, caller: Caller, case_id: UUID, document_id: UUID) -> None:
        user_id = resolve_case_owner(caller)

        async with self.session_maker.begin() as session:
            try:
                await self.case_documents_repo.delete(session, user_id, case_id, document_id)
            except CaseDocumentNotFound:
                logger.warning("No case document with that id!")
                raise


@dataclass
class ListCaseDocuments:
    session_maker: SessionMaker
    case_documents_repo: CaseDocumentsRepository

    async def execute(self, caller: Caller, case_id: UUID) -> list[CaseDocument]:
        user_id = resolve_case_owner(caller)

        async with self.session_maker() as session:
            case_documents = await self.case_documents_repo.list_by_case_id(session, user_id, case_id)
            return case_documents
