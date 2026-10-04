import logging
from dataclasses import dataclass
from uuid import UUID

from src.app.dtos.applications import ApplicationRepresentation, NewApplication
from src.app.interfaces.applications import ApplicationsRepository, ApplicationsStorage
from src.app.interfaces.cases import CaseDocumentsRepository
from src.app.interfaces.relational import SessionMaker
from src.app.ports.applications import ApplicationRenderer, ApplicationWriter
from src.app.ports.tasks import ApplicationGenerationScheduler
from src.domain.exceptions.applications import ApplicationNotFound, ApplicationNotGenerated
from src.domain.exceptions.cases import CaseNotFound
from src.domain.value_objects.applications import ApplicationGenerationStatus
from src.shared.consts import MAX_APPLICATION_GENERATION_DELIVERIES
from src.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


@dataclass
class AddApplication:
    session_maker: SessionMaker
    applications_repo: ApplicationsRepository
    application_generation_scheduler: ApplicationGenerationScheduler

    async def execute(self, user_id: UUID, case_id: UUID, new_application: NewApplication) -> UUID:
        async with self.session_maker.begin() as session:
            try:
                application_id = await self.applications_repo.add(
                    session, user_id, case_id, new_application.application_type
                )
            except CaseNotFound:
                logger.warning("No case with that id!")
                raise
            await self.application_generation_scheduler.schedule_application_generation(
                session, user_id, application_id, new_application
            )
        return application_id


@dataclass
class GenerateApplication:
    session_maker: SessionMaker
    case_documents_repo: CaseDocumentsRepository
    applications_repo: ApplicationsRepository
    applications_storage: ApplicationsStorage
    application_writer: ApplicationWriter
    application_renderer: ApplicationRenderer

    async def execute(self, user_id: UUID, application_id: UUID, new_application: NewApplication) -> None:
        async with self.session_maker.begin() as session:
            application = await self.applications_repo.get(session, user_id, application_id)
            if application is None:
                logger.warning("Application to generate not found! application id: %s", application_id)
                raise ApplicationNotFound

            if application.generation_status == ApplicationGenerationStatus.GENERATED:
                logger.warning("Tried generate already generated application! application id: %s", application_id)
                return

            await self.applications_repo.set_generation_status(
                session, user_id, application_id, ApplicationGenerationStatus.IN_PROGRESS
            )
            legal_basis = await self.case_documents_repo.list_by_case_id(session, user_id, application.case_id)

        try:
            content = await self.application_writer.write(new_application, legal_basis)
            name = await self.application_writer.write_name(new_application)
            document = await self.application_renderer.render(new_application, content)
        except ServiceUnavailable:
            logger.error("Service to generate application not working!")
            await self._set_failed(user_id, application_id)
            raise
        except Exception as e:
            logger.error("Unexpected error during application generation! %s", e)
            await self._set_failed(user_id, application_id)
            raise

        try:
            async with self.session_maker.begin() as session:
                await self.applications_repo.set_name(session, user_id, application_id, name)
                await self.applications_repo.set_generation_status(
                    session, user_id, application_id, ApplicationGenerationStatus.GENERATED
                )
                await self.applications_storage.upload_application(application_id, document)
        except ApplicationNotFound:
            logger.warning("Application removed during generation! application id: %s", application_id)
        except Exception as e:
            logger.error("Failed to save generated application! %s", e)
            await self._set_failed(user_id, application_id)
            raise

    async def _set_failed(self, user_id: UUID, application_id: UUID) -> None:
        try:
            async with self.session_maker.begin() as session:
                await self.applications_repo.set_generation_status(
                    session, user_id, application_id, ApplicationGenerationStatus.FAILED
                )
        except ApplicationNotFound:
            logger.warning("Application removed during generation! application id: %s", application_id)


@dataclass
class FailApplicationGeneration:
    session_maker: SessionMaker
    applications_repo: ApplicationsRepository

    async def execute(self, user_id: UUID, application_id: UUID, delivery_attempt: int) -> bool:
        if delivery_attempt <= MAX_APPLICATION_GENERATION_DELIVERIES:
            return False

        logger.error("Application generation exceeded deliveries limit! application id: %s", application_id)
        try:
            async with self.session_maker.begin() as session:
                await self.applications_repo.set_generation_status(
                    session, user_id, application_id, ApplicationGenerationStatus.FAILED
                )
        except ApplicationNotFound:
            logger.warning("Application removed during generation! application id: %s", application_id)
        return True


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

        if application.generation_status != ApplicationGenerationStatus.GENERATED:
            logger.warning("Application to download not generated! application id: %s", application_id)
            raise ApplicationNotGenerated

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
