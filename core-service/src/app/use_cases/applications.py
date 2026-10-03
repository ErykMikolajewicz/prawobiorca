import logging
from dataclasses import dataclass
from uuid import UUID

from src.app.dtos.applications import ApplicationRepresentation, NewApplication
from src.app.interfaces.applications import ApplicationsRepository, ApplicationsStorage
from src.app.interfaces.cases import CaseDocumentsRepository
from src.app.interfaces.relational import SessionMaker
from src.app.ports.applications import ApplicationRenderer, ApplicationWriter
from src.domain.exceptions.applications import ApplicationNotFound
from src.domain.exceptions.cases import CaseNotFound

logger = logging.getLogger(__name__)


@dataclass
class GenerateApplication:
    session_maker: SessionMaker
    case_documents_repo: CaseDocumentsRepository
    applications_repo: ApplicationsRepository
    applications_storage: ApplicationsStorage
    application_writer: ApplicationWriter
    application_renderer: ApplicationRenderer

    async def execute(self, user_id: UUID, case_id: UUID, new_application: NewApplication) -> bytes:
        async with self.session_maker() as session:
            legal_basis = await self.case_documents_repo.list_by_case_id(session, user_id, case_id)
        content = await self.application_writer.write(new_application, legal_basis)
        document = await self.application_renderer.render(new_application, content)

        async with self.session_maker.begin() as session:
            try:
                application_id = await self.applications_repo.add(
                    session, user_id, case_id, new_application.application_type
                )
            except CaseNotFound:
                logger.warning("No case with that id!")
                raise
            await self.applications_storage.upload_application(application_id, document)

        return document


@dataclass
class ListApplications:
    session_maker: SessionMaker
    applications_repo: ApplicationsRepository

    async def execute(self, user_id: UUID, case_id: UUID) -> list[ApplicationRepresentation]:
        async with self.session_maker() as session:
            applications = await self.applications_repo.list_by_case_id(session, user_id, case_id)
        return applications


@dataclass
class GetApplicationDownloadUrl:
    session_maker: SessionMaker
    applications_repo: ApplicationsRepository
    applications_storage: ApplicationsStorage

    async def execute(self, user_id: UUID, application_id: UUID) -> str:
        async with self.session_maker() as session:
            application = await self.applications_repo.get(session, user_id, application_id)

        if application is None:
            logger.warning("Application to download not found! application id: %s", application_id)
            raise ApplicationNotFound

        return await self.applications_storage.get_download_url(application_id)


@dataclass
class DeleteApplication:
    session_maker: SessionMaker
    applications_repo: ApplicationsRepository
    applications_storage: ApplicationsStorage

    async def execute(self, user_id: UUID, application_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            try:
                await self.applications_repo.delete(session, user_id, application_id)
            except ApplicationNotFound:
                logger.warning("Application not found! application id: %s", application_id)
                raise

        try:
            await self.applications_storage.delete_application(application_id)
        except Exception:
            logger.error("Failed to remove from storage application: %s", application_id)
