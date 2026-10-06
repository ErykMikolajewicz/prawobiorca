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
)
from src.app.interfaces.application_templates import ApplicationTemplatesRepository, ApplicationTemplatesStorage
from src.app.interfaces.relational import SessionMaker
from src.app.ports.application_templates import ApplicationTemplateInspector
from src.domain.exceptions.application_templates import (
    ApplicationTemplateContentNotFound,
    ApplicationTemplateInInvalidState,
    ApplicationTemplateNotFound,
    InvalidApplicationTemplate,
)
from src.domain.services.application_fields import create_default_fields, validate_fields_config
from src.domain.value_objects.application_templates import ApplicationTemplateDetails, ApplicationTemplateStatus

logger = logging.getLogger(__name__)


@dataclass
class ListApplicationTemplates:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self) -> list[ApplicationTemplateRepresentation]:
        async with self.session_maker() as session:
            return await self.application_templates_repo.list_templates(session)


@dataclass
class GetApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, template_id: UUID) -> ApplicationTemplateRepresentation:
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

    async def execute(self) -> list[PublishedApplicationTemplate]:
        async with self.session_maker() as session:
            templates = await self.application_templates_repo.list_templates(
                session, ApplicationTemplateStatus.PUBLISHED
            )

        return [
            PublishedApplicationTemplate(
                id=template.id,
                name=template.name,
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
            for template in templates
        ]


@dataclass
class AddApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    application_templates_storage: ApplicationTemplatesStorage

    async def execute(self, template_data: ApplicationTemplateData) -> ApplicationTemplateUploadTarget:
        async with self.session_maker.begin() as session:
            template_id = await self.application_templates_repo.add(session, template_data.name)

        return await self.application_templates_storage.get_upload_target(template_id)


@dataclass
class ConfirmApplicationTemplateUpload:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    application_templates_storage: ApplicationTemplatesStorage
    application_template_inspector: ApplicationTemplateInspector

    async def execute(self, template_id: UUID) -> ApplicationTemplateRepresentation:
        async with self.session_maker.begin() as session:
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

            await self.application_templates_repo.set_fields(session, template_id, fields)
            return await self.application_templates_repo.set_status(
                session, template_id, ApplicationTemplateStatus.DRAFT
            )


@dataclass
class UpdateApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(
        self, template_id: UUID, details_data: ApplicationTemplateDetailsData
    ) -> ApplicationTemplateRepresentation:
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
                name=details_data.name, instructions=details_data.instructions, fields=details_data.fields
            )
            return await self.application_templates_repo.update_details(session, template_id, details)


@dataclass
class PublishApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, template_id: UUID) -> ApplicationTemplateRepresentation:
        async with self.session_maker.begin() as session:
            template = await self.application_templates_repo.get(session, template_id)
            if template is None:
                logger.warning("Application template to publish not found! template id: %s", template_id)
                raise ApplicationTemplateNotFound

            if template.status != ApplicationTemplateStatus.DRAFT or not (template.instructions or "").strip():
                logger.warning("Application template not ready to publish! template id: %s", template_id)
                raise ApplicationTemplateInInvalidState

            return await self.application_templates_repo.set_status(
                session, template_id, ApplicationTemplateStatus.PUBLISHED
            )


@dataclass
class UnpublishApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository

    async def execute(self, template_id: UUID) -> ApplicationTemplateRepresentation:
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
class DeleteApplicationTemplate:
    session_maker: SessionMaker
    application_templates_repo: ApplicationTemplatesRepository
    application_templates_storage: ApplicationTemplatesStorage

    async def execute(self, template_id: UUID) -> None:
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

    async def execute(self, template_id: UUID) -> str:
        async with self.session_maker() as session:
            template = await self.application_templates_repo.get(session, template_id)

        if template is None:
            logger.warning("Application template to download not found! template id: %s", template_id)
            raise ApplicationTemplateNotFound

        if template.status == ApplicationTemplateStatus.NOT_UPLOADED:
            logger.warning("Application template to download not uploaded! template id: %s", template_id)
            raise ApplicationTemplateInInvalidState

        return await self.application_templates_storage.get_download_url(template_id)
