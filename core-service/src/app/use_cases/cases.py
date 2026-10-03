import logging
from dataclasses import dataclass
from uuid import UUID

from src.app.dtos.cases import CaseData, CaseDocument, NewCaseDocument
from src.app.interfaces.applications import ApplicationsRepository, ApplicationsStorage
from src.app.interfaces.cases import CaseDocumentsRepository, CasesRepository
from src.app.interfaces.relational import SessionMaker
from src.domain.exceptions.cases import CaseNotFound

logger = logging.getLogger(__name__)


@dataclass
class ListCases:
    session_maker: SessionMaker
    cases_repo: CasesRepository

    async def execute(self, user_id: UUID) -> list[CaseData]:
        async with self.session_maker() as session:
            cases = await self.cases_repo.list_by_user_id(session, user_id)
        return cases


@dataclass
class DeleteCase:
    session_maker: SessionMaker
    cases_repo: CasesRepository
    applications_repo: ApplicationsRepository
    applications_storage: ApplicationsStorage

    async def execute(self, user_id: UUID, case_id: UUID) -> None:
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
                logger.error("Failed to remove from storage application: %s", application_id)


@dataclass
class AddCase:
    session_maker: SessionMaker
    cases_repo: CasesRepository

    async def execute(self, user_id: UUID, case_name: str) -> UUID:
        async with self.session_maker.begin() as session:
            case_id = await self.cases_repo.add(session, user_id, case_name)
        return case_id


@dataclass
class AddCaseDocument:
    session_maker: SessionMaker
    case_documents_repo: CaseDocumentsRepository

    async def execute(self, user_id: UUID, case_id: UUID, new_document: NewCaseDocument) -> None:
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

    async def execute(self, user_id: UUID, document_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            await self.case_documents_repo.delete(session, user_id, document_id)


@dataclass
class ListCaseDocuments:
    session_maker: SessionMaker
    case_documents_repo: CaseDocumentsRepository

    async def execute(self, user_id: UUID, case_id: UUID) -> list[CaseDocument]:
        async with self.session_maker() as session:
            case_documents = await self.case_documents_repo.list_by_case_id(session, user_id, case_id)
            return case_documents
