import logging
from dataclasses import dataclass, replace
from typing import TypeGuard
from uuid import UUID

from core_service.application.dtos.applications import ApplicationRepresentation, NewApplication
from core_service.application.ports.application_templates import (
    ApplicationTemplatesRepository,
    ApplicationTemplatesStorage,
)
from core_service.application.ports.applications import (
    ApplicationRenderer,
    ApplicationsRepository,
    ApplicationsStorage,
    ApplicationWriter,
)
from core_service.application.ports.cases import CaseDocumentsRepository
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.tasks import ApplicationGenerationScheduler
from core_service.application.services.tasks import is_retried
from core_service.domain.entities.application_template import ApplicationTemplate
from core_service.domain.exceptions.application_templates import (
    ApplicationTemplateNotFound,
    InvalidApplicationFieldValues,
)
from core_service.domain.exceptions.applications import ApplicationNotFound, ApplicationNotGenerated
from core_service.domain.exceptions.cases import CaseNotFound
from core_service.domain.services.case_access import resolve_case_owner
from core_service.domain.value_objects.applications import ApplicationGenerationStatus
from core_service.domain.value_objects.users import Caller

logger = logging.getLogger(__name__)

MAX_APPLICATION_GENERATION_DELIVERIES = 3


async def _fail_generation(
    session_maker: SessionMaker, applications_repo: ApplicationsRepository, user_id: UUID, application_id: UUID
) -> None:
    async with session_maker.begin() as session:
        application = await applications_repo.get_for_update(session, user_id, application_id)
        if application is None:
            logger.warning("Application removed during generation! application id: %s", application_id)
            return
        if application.is_generated:
            logger.warning("Application already generated, skipping failure! application id: %s", application_id)
            return

        application.fail_generation()
        await applications_repo.save(session, application)


@dataclass
class AddApplication:
    session_maker: SessionMaker
    applications_repo: ApplicationsRepository
    application_templates_repo: ApplicationTemplatesRepository
    application_generation_scheduler: ApplicationGenerationScheduler

    async def execute(self, caller: Caller, case_id: UUID, new_application: NewApplication) -> UUID:
        user_id = resolve_case_owner(caller)

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get_for_update(session, new_application.template_id)
            if template is None or not template.is_published:
                logger.warning("Published application template not found! template id: %s", new_application.template_id)
                raise ApplicationTemplateNotFound

            try:
                field_values = template.validate_field_values(new_application.field_values)
            except InvalidApplicationFieldValues:
                logger.warning("Invalid application field values! template id: %s", template.id)
                raise
            new_application = replace(new_application, field_values=field_values)

            try:
                application_id = await self.applications_repo.add(session, user_id, case_id, template.id, template.name)
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
    application_templates_repo: ApplicationTemplatesRepository
    application_templates_storage: ApplicationTemplatesStorage
    application_writer: ApplicationWriter
    application_renderer: ApplicationRenderer

    async def execute(
        self, user_id: UUID, application_id: UUID, new_application: NewApplication, is_last_attempt: bool
    ) -> None:
        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get_for_update(session, new_application.template_id)
            application = await self.applications_repo.get_for_update(session, user_id, application_id)
            if application is None:
                logger.warning("Application to generate not found! application id: %s", application_id)
                raise ApplicationNotFound

            if application.is_generated:
                logger.warning("Tried generate already generated application! application id: %s", application_id)
                return

            if not self._is_template_valid(template, new_application):
                logger.warning("Application template changed before generation! application id: %s", application_id)
                application.fail_generation()
                await self.applications_repo.save(session, application)
                return

            application.start_generation()
            await self.applications_repo.save(session, application)
            legal_basis = await self.case_documents_repo.list_by_case_id(session, user_id, application.case_id)

        try:
            template_content = await self.application_templates_storage.get_template(template.id)
            content = await self.application_writer.write(new_application, template, legal_basis)
            name = await self.application_writer.write_name(new_application)
            document = await self.application_renderer.render(template_content, new_application, content)
            await self._complete_generation(user_id, application_id, name, document)
        except Exception as error:
            logger.exception("Application generation failed! application id: %s", application_id)
            if not is_retried(error, is_last_attempt):
                await _fail_generation(self.session_maker, self.applications_repo, user_id, application_id)
            raise

    async def _complete_generation(self, user_id: UUID, application_id: UUID, name: str, document: bytes) -> None:
        async with self.session_maker.begin() as session:
            application = await self.applications_repo.get_for_update(session, user_id, application_id)
            if application is None:
                logger.warning("Application removed during generation! application id: %s", application_id)
                return

            application.complete_generation(name)
            await self.applications_repo.save(session, application)
            await self.applications_storage.upload_application(application_id, document)

    @staticmethod
    def _is_template_valid(
        template: ApplicationTemplate | None, new_application: NewApplication
    ) -> TypeGuard[ApplicationTemplate]:
        if template is None or not template.is_published:
            return False

        try:
            template.validate_field_values(new_application.field_values)
        except InvalidApplicationFieldValues:
            return False

        return True


@dataclass
class FailApplicationGeneration:
    session_maker: SessionMaker
    applications_repo: ApplicationsRepository

    async def execute(self, user_id: UUID, application_id: UUID, delivery_attempt: int) -> bool:
        if delivery_attempt <= MAX_APPLICATION_GENERATION_DELIVERIES:
            return False

        logger.error("Application generation exceeded deliveries limit! application id: %s", application_id)
        await _fail_generation(self.session_maker, self.applications_repo, user_id, application_id)
        return True


@dataclass
class ListApplications:
    session_maker: SessionMaker
    applications_repo: ApplicationsRepository

    async def execute(self, caller: Caller, case_id: UUID) -> list[ApplicationRepresentation]:
        user_id = resolve_case_owner(caller)

        async with self.session_maker() as session:
            applications = await self.applications_repo.list_by_case_id(session, user_id, case_id)
        return applications


@dataclass
class GetApplicationDownloadUrl:
    session_maker: SessionMaker
    applications_repo: ApplicationsRepository
    applications_storage: ApplicationsStorage

    async def execute(self, caller: Caller, case_id: UUID, application_id: UUID) -> str:
        user_id = resolve_case_owner(caller)

        async with self.session_maker() as session:
            application = await self.applications_repo.get(session, user_id, application_id)

        if application is None or application.case_id != case_id:
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

    async def execute(self, caller: Caller, case_id: UUID, application_id: UUID) -> None:
        user_id = resolve_case_owner(caller)

        async with self.session_maker.begin() as session:
            try:
                await self.applications_repo.delete(session, user_id, case_id, application_id)
            except ApplicationNotFound:
                logger.warning("Application not found! application id: %s", application_id)
                raise

        try:
            await self.applications_storage.delete_application(application_id)
        except Exception:
            logger.exception("Failed to remove from storage application: %s", application_id)
