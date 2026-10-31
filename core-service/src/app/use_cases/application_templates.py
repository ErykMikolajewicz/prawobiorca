import logging
from dataclasses import dataclass
from uuid import UUID

from src.app.dtos.application_templates import (
    ApplicationTemplateData,
    ApplicationTemplateDetailsData,
    ApplicationTemplateRepresentation,
    ApplicationTemplateUploadTarget,
    PublishedApplicationField,
    PublishedApplicationTemplate,
    PublishedApplicationTemplateSearchResult,
)
from src.app.interfaces.application_templates import ApplicationTemplatesRepository, ApplicationTemplatesStorage
from src.app.interfaces.relational import SessionMaker
from src.app.ports.application_templates import (
    ApplicationTemplateDescriptionWriter,
    ApplicationTemplateInspector,
    ApplicationTemplateInstructionsProvider,
)
from src.app.ports.tasks import ApplicationTemplateDescriptionGenerationScheduler
from src.app.ports.texts import TextsEmbedder
from src.domain.exceptions.application_templates import (
    ApplicationTemplateContentNotFound,
    ApplicationTemplateDescriptionGenerationInProgress,
    ApplicationTemplateInInvalidState,
    ApplicationTemplateNotFound,
    InvalidApplicationTemplate,
)
from src.domain.exceptions.organizations import OrganizationNotFound
from src.domain.services.application_fields import create_default_fields, validate_fields_config
from src.domain.services.application_template_access import (
    check_can_manage_application_templates,
    check_can_read_published_application_templates,
)
from src.domain.services.application_template_description import create_description_source
from src.domain.services.application_templates import is_ready_to_publish
from src.domain.value_objects.application_templates import (
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateDetails,
    ApplicationTemplateStatus,
)
from src.domain.value_objects.organizations import OrganizationFilter
from src.domain.value_objects.users import Caller
from src.shared.consts import MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES
from src.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)


def _to_published_template(template: ApplicationTemplateRepresentation) -> PublishedApplicationTemplate:
    return PublishedApplicationTemplate(
        id=template.id,
        name=template.name,
        description=template.description,
        fields=[
            PublishedApplicationField(
                name=field.name,
                label=field.label,
                field_type=field.field_type,
                required=field.required,
                default_value=field.default_value,
                pattern=field.pattern,
                options=field.options,
            )
            for field in template.fields
        ],
    )


@dataclass
class ListApplicationTemplates:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, caller: Caller) -> list[ApplicationTemplateRepresentation]:
        check_can_manage_application_templates(caller)

        async with self.session_maker() as session:
            return await self.application_templates_repo.list_templates(session)


@dataclass
class GetApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, caller: Caller, template_id: UUID) -> ApplicationTemplateRepresentation:
        check_can_manage_application_templates(caller)

        async with self.session_maker() as session:
            template = await self.application_templates_repo.get(session, template_id)

        if template is None:
            logger.warning("Application template not found! template id: %s", template_id)
            raise ApplicationTemplateNotFound

        return template


@dataclass
class ListPublishedApplicationTemplates:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(
        self, caller: Caller, organization_filter: OrganizationFilter | None
    ) -> list[PublishedApplicationTemplate]:
        check_can_read_published_application_templates(caller)

        async with self.session_maker() as session:
            templates = await self.application_templates_repo.list_templates(
                session, ApplicationTemplateStatus.PUBLISHED, organization_filter
            )

        return [_to_published_template(template) for template in templates]


@dataclass
class SearchPublishedApplicationTemplates:
    session_maker: SessionMaker
    embedding_port: TextsEmbedder
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(
        self, caller: Caller, organization_filter: OrganizationFilter | None, query: str, threshold: float
    ) -> list[PublishedApplicationTemplateSearchResult]:
        check_can_read_published_application_templates(caller)

        embeddings = await self.embedding_port.embed_queries([query])
        query_vector = embeddings[0]

        async with self.session_maker() as session:
            results = await self.application_templates_repo.search_templates(
                session, ApplicationTemplateStatus.PUBLISHED, organization_filter, query_vector, threshold
            )

        return [
            PublishedApplicationTemplateSearchResult(template=_to_published_template(template), score=score)
            for template, score in results
        ]


@dataclass
class AddApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    application_templates_storage: ApplicationTemplatesStorage
    application_template_instructions_provider: ApplicationTemplateInstructionsProvider

    async def execute(self, caller: Caller, template_data: ApplicationTemplateData) -> ApplicationTemplateUploadTarget:
        check_can_manage_application_templates(caller)

        instructions = await self.application_template_instructions_provider.get_default_instructions()

        async with self.session_maker.begin() as session:
            template_id = await self.application_templates_repo.add(session, template_data.name, instructions)

        return await self.application_templates_storage.get_upload_target(template_id)


@dataclass
class ConfirmApplicationTemplateUpload:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    application_templates_storage: ApplicationTemplatesStorage
    application_template_inspector: ApplicationTemplateInspector

    async def execute(self, caller: Caller, template_id: UUID) -> ApplicationTemplateRepresentation:
        check_can_manage_application_templates(caller)

        async with self.session_maker() as session:
            template = await self.application_templates_repo.get(session, template_id)

        if template is None:
            logger.warning("Application template to confirm upload not found! template id: %s", template_id)
            raise ApplicationTemplateNotFound

        if template.status != ApplicationTemplateStatus.NOT_UPLOADED:
            logger.warning("Application template upload already confirmed! template id: %s", template_id)
            raise ApplicationTemplateInInvalidState

        try:
            content = await self.application_templates_storage.get_template(template_id)
        except ApplicationTemplateContentNotFound:
            logger.error("Application template content not found in storage! template id: %s", template_id)
            raise

        try:
            variables = await self.application_template_inspector.get_variables(content)
            fields = create_default_fields(variables)
        except InvalidApplicationTemplate:
            logger.warning("Invalid application template uploaded! template id: %s", template_id)
            raise

        async with self.session_maker.begin() as session:
            confirmed_template = await self.application_templates_repo.confirm_upload(session, template_id, fields)

        if confirmed_template is None:
            logger.warning("Application template changed during upload confirmation! template id: %s", template_id)
            raise ApplicationTemplateInInvalidState

        return confirmed_template


@dataclass
class UpdateApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(
        self, caller: Caller, template_id: UUID, details_data: ApplicationTemplateDetailsData
    ) -> ApplicationTemplateRepresentation:
        check_can_manage_application_templates(caller)

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get(session, template_id)
            if template is None:
                logger.warning("Application template to update not found! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            if template.status != ApplicationTemplateStatus.DRAFT:
                logger.warning("Tried to update not draft application template! template id: %s", template_id)
                raise ApplicationTemplateInInvalidState

            validate_fields_config({field.name for field in template.fields}, details_data.fields)

            details = ApplicationTemplateDetails(
                name=details_data.name,
                instructions=details_data.instructions,
                fields=details_data.fields,
                description=details_data.description,
                organization_id=details_data.organization_id,
                suborganization_id=details_data.suborganization_id,
            )
            try:
                return await self.application_templates_repo.update_details(session, template_id, details)
            except OrganizationNotFound:
                logger.warning("Organization for application template not found! template id: %s", template_id)
                raise


@dataclass
class PublishApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, caller: Caller, template_id: UUID) -> ApplicationTemplateRepresentation:
        check_can_manage_application_templates(caller)

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get(session, template_id)
            if template is None:
                logger.warning("Application template to publish not found! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            if not is_ready_to_publish(template.status, template.instructions):
                logger.warning("Application template not ready to publish! template id: %s", template_id)
                raise ApplicationTemplateInInvalidState

            return await self.application_templates_repo.set_status(
                session, template_id, ApplicationTemplateStatus.PUBLISHED
            )


@dataclass
class UnpublishApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, caller: Caller, template_id: UUID) -> ApplicationTemplateRepresentation:
        check_can_manage_application_templates(caller)

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get(session, template_id)
            if template is None:
                logger.warning("Application template to unpublish not found! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            if template.status != ApplicationTemplateStatus.PUBLISHED:
                logger.warning("Tried to unpublish not published application template! template id: %s", template_id)
                raise ApplicationTemplateInInvalidState

            return await self.application_templates_repo.set_status(
                session, template_id, ApplicationTemplateStatus.DRAFT
            )


@dataclass
class RegenerateApplicationTemplateDescription:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    description_generation_scheduler: ApplicationTemplateDescriptionGenerationScheduler

    async def execute(self, caller: Caller, template_id: UUID) -> None:
        check_can_manage_application_templates(caller)

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get(session, template_id)
            if template is None:
                logger.warning("Application template to generate description not found! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            if template.status != ApplicationTemplateStatus.DRAFT:
                logger.warning(
                    "Tried to generate description of not draft application template! template id: %s", template_id
                )
                raise ApplicationTemplateInInvalidState

            if template.description_status == ApplicationTemplateDescriptionStatus.IN_PROGRESS:
                logger.warning("Application template description generation in progress! template id: %s", template_id)
                raise ApplicationTemplateDescriptionGenerationInProgress

            await self.application_templates_repo.set_description_status(
                session, template_id, ApplicationTemplateDescriptionStatus.IN_PROGRESS
            )
            await self.description_generation_scheduler.schedule_application_template_description_generation(
                session, template_id
            )


@dataclass
class GenerateApplicationTemplateDescription:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    application_templates_storage: ApplicationTemplatesStorage
    application_template_inspector: ApplicationTemplateInspector
    description_writer: ApplicationTemplateDescriptionWriter
    texts_embedder: TextsEmbedder

    async def execute(self, template_id: UUID) -> None:
        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get(session, template_id)
            if template is None:
                logger.warning("Application template to generate description not found! template id: %s", template_id)
                return

            if template.description_status == ApplicationTemplateDescriptionStatus.GENERATED:
                logger.warning("Application template description already generated! template id: %s", template_id)
                return

            await self.application_templates_repo.set_description_status(
                session, template_id, ApplicationTemplateDescriptionStatus.IN_PROGRESS
            )

        try:
            content = await self.application_templates_storage.get_template(template_id)
            text = await self.application_template_inspector.get_text(content)
            description_source = create_description_source(template.name, template.instructions, template.fields, text)
            description = await self.description_writer.write(description_source)
            vectors = await self.texts_embedder.embed_texts([description])
        except ServiceUnavailable:
            logger.error("Service to generate application template description not working!")
            await self._set_failed(template_id)
            raise
        except Exception as e:
            logger.error("Unexpected error during application template description generation! %s", e)
            await self._set_failed(template_id)
            raise

        try:
            async with self.session_maker.begin() as session:
                await self.application_templates_repo.set_generated_description(
                    session, template_id, description, vectors[0]
                )
        except ApplicationTemplateNotFound:
            logger.warning("Application template removed during description generation! template id: %s", template_id)

    async def _set_failed(self, template_id: UUID) -> None:
        try:
            async with self.session_maker.begin() as session:
                await self.application_templates_repo.set_description_status(
                    session, template_id, ApplicationTemplateDescriptionStatus.FAILED
                )
        except ApplicationTemplateNotFound:
            logger.warning("Application template removed during description generation! template id: %s", template_id)


@dataclass
class FailApplicationTemplateDescriptionGeneration:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, template_id: UUID, delivery_attempt: int) -> bool:
        if delivery_attempt <= MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES:
            return False

        logger.error(
            "Application template description generation exceeded deliveries limit! template id: %s", template_id
        )
        try:
            async with self.session_maker.begin() as session:
                await self.application_templates_repo.set_description_status(
                    session, template_id, ApplicationTemplateDescriptionStatus.FAILED
                )
        except ApplicationTemplateNotFound:
            logger.warning("Application template removed during description generation! template id: %s", template_id)
        return True


@dataclass
class DeleteApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    application_templates_storage: ApplicationTemplatesStorage

    async def execute(self, caller: Caller, template_id: UUID) -> None:
        check_can_manage_application_templates(caller)

        async with self.session_maker.begin() as session:
            try:
                await self.application_templates_repo.delete(session, template_id)
            except ApplicationTemplateNotFound:
                logger.warning("Application template to delete not found! template id: %s", template_id)
                raise

        try:
            await self.application_templates_storage.delete_template(template_id)
        except Exception:
            logger.error("Failed to remove from storage application template: %s", template_id)


@dataclass
class GetApplicationTemplateDownloadUrl:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    application_templates_storage: ApplicationTemplatesStorage

    async def execute(self, caller: Caller, template_id: UUID) -> str:
        check_can_manage_application_templates(caller)

        async with self.session_maker() as session:
            template = await self.application_templates_repo.get(session, template_id)

        if template is None:
            logger.warning("Application template to download not found! template id: %s", template_id)
            raise ApplicationTemplateNotFound

        if template.status == ApplicationTemplateStatus.NOT_UPLOADED:
            logger.warning("Application template to download not uploaded! template id: %s", template_id)
            raise ApplicationTemplateInInvalidState

        return await self.application_templates_storage.get_download_url(template_id)
