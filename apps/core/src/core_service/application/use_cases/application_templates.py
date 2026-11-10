import logging
from dataclasses import dataclass
from uuid import UUID

from core_service.application.dtos.application_templates import (
    ApplicationTemplateData,
    ApplicationTemplateDetailsData,
    ApplicationTemplateRepresentation,
    ApplicationTemplateUploadTarget,
    PublishedApplicationField,
    PublishedApplicationTemplate,
)
from core_service.application.ports.application_templates import (
    ApplicationTemplateDescriptionWriter,
    ApplicationTemplateInspector,
    ApplicationTemplateInstructionsProvider,
    ApplicationTemplatesRepository,
    ApplicationTemplatesStorage,
)
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.tasks import ApplicationTemplateDescriptionGenerationScheduler
from core_service.application.ports.texts import TextsEmbedder
from core_service.application.services.embedding import embed_description
from core_service.domain.exceptions.application_templates import (
    ApplicationTemplateContentNotFound,
    ApplicationTemplateInInvalidState,
    ApplicationTemplateNotFound,
    InvalidApplicationTemplate,
)
from core_service.domain.exceptions.descriptions import DescriptionGenerationInProgress
from core_service.domain.exceptions.organizations import OrganizationNotFound
from core_service.domain.services.application_template_access import (
    check_can_manage_application_templates,
    check_can_read_published_application_templates,
)
from core_service.domain.services.application_templates import is_semantic_search_query
from core_service.domain.value_objects.application_templates import (
    ApplicationTemplateDetails,
    ApplicationTemplateStatus,
)
from core_service.domain.value_objects.organizations import OrganizationFilter
from core_service.domain.value_objects.users import Caller
from core_service.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)

MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES = 3


async def _fail_description_generation(
    session_maker: SessionMaker, application_templates_repo: ApplicationTemplatesRepository, template_id: UUID
) -> None:
    async with session_maker.begin() as session:
        template = await application_templates_repo.get_for_update(session, template_id)
        if template is None:
            logger.warning("Application template removed during description generation! template id: %s", template_id)
            return

        template.fail_description_generation()
        await application_templates_repo.save(session, template)


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
        self, caller: Caller, organization_filter: OrganizationFilter | None, query: str, ai_assisted: bool
    ) -> list[PublishedApplicationTemplate]:
        check_can_read_published_application_templates(caller)

        stripped_query = query.strip()

        if ai_assisted and is_semantic_search_query(query):
            embeddings = await self.embedding_port.embed_queries([stripped_query])
            async with self.session_maker() as session:
                templates = await self.application_templates_repo.hybrid_search_templates(
                    session, ApplicationTemplateStatus.PUBLISHED, organization_filter, stripped_query, embeddings[0]
                )
        else:
            async with self.session_maker() as session:
                templates = await self.application_templates_repo.fuzzy_search_templates(
                    session, ApplicationTemplateStatus.PUBLISHED, organization_filter, stripped_query
                )

        return [_to_published_template(template) for template in templates]


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
            template_representation = await self.application_templates_repo.get(session, template_id)

        if template_representation is None:
            logger.warning("Application template to confirm upload not found! template id: %s", template_id)
            raise ApplicationTemplateNotFound

        try:
            content = await self.application_templates_storage.get_template(template_id)
        except ApplicationTemplateContentNotFound:
            logger.error("Application template content not found in storage! template id: %s", template_id)
            raise

        try:
            variables = await self.application_template_inspector.get_variables(content)
        except InvalidApplicationTemplate:
            logger.warning("Invalid application template uploaded! template id: %s", template_id)
            raise

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get_for_update(session, template_id)
            if template is None:
                logger.warning("Application template removed during upload confirmation! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            try:
                template.confirm_upload(variables)
            except (ApplicationTemplateInInvalidState, InvalidApplicationTemplate) as error:
                logger.warning(
                    "Can't confirm application template upload! template id: %s, reason: %s",
                    template_id,
                    type(error).__name__,
                )
                raise

            return await self.application_templates_repo.save(session, template)


@dataclass
class UpdateApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    texts_embedder: TextsEmbedder

    async def execute(
        self, caller: Caller, template_id: UUID, details_data: ApplicationTemplateDetailsData
    ) -> ApplicationTemplateRepresentation:
        check_can_manage_application_templates(caller)

        async with self.session_maker() as session:
            template_representation = await self.application_templates_repo.get(session, template_id)

        if template_representation is None:
            logger.warning("Application template to update not found! template id: %s", template_id)
            raise ApplicationTemplateNotFound

        details = ApplicationTemplateDetails(
            name=details_data.name,
            instructions=details_data.instructions,
            fields=details_data.fields,
            description=details_data.description,
            organization_id=details_data.organization_id,
            suborganization_id=details_data.suborganization_id,
        )

        description_changed = details.description != template_representation.description
        description_vector = (
            await embed_description(self.texts_embedder, details.description) if description_changed else None
        )

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get_for_update(session, template_id)
            if template is None:
                logger.warning("Application template removed during update! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            try:
                template.update_details(details)
            except ApplicationTemplateInInvalidState:
                logger.warning("Tried to update not draft application template! template id: %s", template_id)
                raise

            try:
                updated_template = await self.application_templates_repo.save(session, template)
            except OrganizationNotFound:
                logger.warning("Organization for application template not found! template id: %s", template_id)
                raise

            if description_changed:
                await self.application_templates_repo.set_description_vector(session, template_id, description_vector)
            return updated_template


@dataclass
class PublishApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, caller: Caller, template_id: UUID) -> ApplicationTemplateRepresentation:
        check_can_manage_application_templates(caller)

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get_for_update(session, template_id)
            if template is None:
                logger.warning("Application template to publish not found! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            try:
                template.publish()
            except ApplicationTemplateInInvalidState:
                logger.warning("Application template not ready to publish! template id: %s", template_id)
                raise

            return await self.application_templates_repo.save(session, template)


@dataclass
class UnpublishApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, caller: Caller, template_id: UUID) -> ApplicationTemplateRepresentation:
        check_can_manage_application_templates(caller)

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get_for_update(session, template_id)
            if template is None:
                logger.warning("Application template to unpublish not found! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            try:
                template.unpublish()
            except ApplicationTemplateInInvalidState:
                logger.warning("Tried to unpublish not published application template! template id: %s", template_id)
                raise

            return await self.application_templates_repo.save(session, template)


@dataclass
class RegenerateApplicationTemplateDescription:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    description_generation_scheduler: ApplicationTemplateDescriptionGenerationScheduler

    async def execute(self, caller: Caller, template_id: UUID) -> None:
        check_can_manage_application_templates(caller)

        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get_for_update(session, template_id)
            if template is None:
                logger.warning("Application template to generate description not found! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            try:
                template.request_description()
            except (ApplicationTemplateInInvalidState, DescriptionGenerationInProgress) as error:
                logger.warning(
                    "Can't generate application template description! template id: %s, reason: %s",
                    template_id,
                    type(error).__name__,
                )
                raise

            await self.application_templates_repo.save(session, template)
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
            template = await self.application_templates_repo.get_for_update(session, template_id)
            if template is None:
                logger.warning("Application template to generate description not found! template id: %s", template_id)
                return

            if template.is_description_generated:
                logger.warning("Application template description already generated! template id: %s", template_id)
                return

            template.start_description_generation()
            await self.application_templates_repo.save(session, template)

        try:
            content = await self.application_templates_storage.get_template(template_id)
            text = await self.application_template_inspector.get_text(content)
            description = await self.description_writer.write(template.create_description_source(text))
            vectors = await self.texts_embedder.embed_texts([description])
        except ServiceUnavailable:
            logger.error("Service to generate application template description not working!")
            await _fail_description_generation(self.session_maker, self.application_templates_repo, template_id)
            raise
        except Exception as e:
            logger.error("Unexpected error during application template description generation! %s", e)
            await _fail_description_generation(self.session_maker, self.application_templates_repo, template_id)
            raise

        try:
            async with self.session_maker.begin() as session:
                template = await self.application_templates_repo.get_for_update(session, template_id)
                if template is None:
                    logger.warning(
                        "Application template removed during description generation! template id: %s", template_id
                    )
                    return

                template.complete_description_generation(description)
                await self.application_templates_repo.save(session, template)
                await self.application_templates_repo.set_description_vector(session, template_id, vectors[0])
        except Exception as e:
            logger.error("Failed to save generated application template description! %s", e)
            await _fail_description_generation(self.session_maker, self.application_templates_repo, template_id)
            raise


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
        await _fail_description_generation(self.session_maker, self.application_templates_repo, template_id)
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
            logger.exception("Failed to remove from storage application template: %s", template_id)


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
