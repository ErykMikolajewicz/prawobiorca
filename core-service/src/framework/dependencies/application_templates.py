from typing import Annotated, Any

from fastapi import Depends

from src.app.interfaces.application_templates import ApplicationTemplatesRepository, ApplicationTemplatesStorage
from src.app.interfaces.relational import SessionMaker
from src.app.ports.application_templates import (
    ApplicationTemplateInspector,
    ApplicationTemplateInstructionsProvider,
)
from src.app.use_cases.application_templates import (
    AddApplicationTemplate,
    ConfirmApplicationTemplateUpload,
    DeleteApplicationTemplate,
    GetApplicationTemplate,
    GetApplicationTemplateDownloadUrl,
    ListApplicationTemplates,
    ListPublishedApplicationTemplates,
    PublishApplicationTemplate,
    UnpublishApplicationTemplate,
    UpdateApplicationTemplate,
)
from src.framework.dependencies.regulations import get_file_storage_client, get_file_storage_presign_client
from src.framework.dependencies.relational import get_session_maker
from src.infrastructure.ai_services.application_template_instructions import (
    PromptsApplicationTemplateInstructionsProvider,
)
from src.infrastructure.docx.template_inspector import DocxTemplateInspector
from src.infrastructure.object_storage.repository import S3ApplicationTemplatesStorage
from src.infrastructure.relational_db.repositories.application_templates import (
    ApplicationTemplatesRepository as SqlaApplicationTemplatesRepository,
)


def get_application_templates_repo() -> ApplicationTemplatesRepository:
    return SqlaApplicationTemplatesRepository()


def get_application_templates_storage(
    client: Annotated[Any, Depends(get_file_storage_client)],
    presign_client: Annotated[Any, Depends(get_file_storage_presign_client)],
) -> ApplicationTemplatesStorage:
    return S3ApplicationTemplatesStorage(client, presign_client)


def get_application_template_inspector() -> ApplicationTemplateInspector:
    return DocxTemplateInspector()


def get_application_template_instructions_provider() -> ApplicationTemplateInstructionsProvider:
    return PromptsApplicationTemplateInstructionsProvider()


def get_list_application_templates(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
) -> ListApplicationTemplates:
    return ListApplicationTemplates(session_maker, application_templates_repo)


def get_application_template(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
) -> GetApplicationTemplate:
    return GetApplicationTemplate(session_maker, application_templates_repo)


def get_list_published_application_templates(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
) -> ListPublishedApplicationTemplates:
    return ListPublishedApplicationTemplates(session_maker, application_templates_repo)


def get_add_application_template(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
    application_templates_storage: Annotated[ApplicationTemplatesStorage, Depends(get_application_templates_storage)],
    application_template_instructions_provider: Annotated[
        ApplicationTemplateInstructionsProvider, Depends(get_application_template_instructions_provider)
    ],
) -> AddApplicationTemplate:
    return AddApplicationTemplate(
        session_maker,
        application_templates_repo,
        application_templates_storage,
        application_template_instructions_provider,
    )


def get_confirm_application_template_upload(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
    application_templates_storage: Annotated[ApplicationTemplatesStorage, Depends(get_application_templates_storage)],
    application_template_inspector: Annotated[
        ApplicationTemplateInspector, Depends(get_application_template_inspector)
    ],
) -> ConfirmApplicationTemplateUpload:
    return ConfirmApplicationTemplateUpload(
        session_maker, application_templates_repo, application_templates_storage, application_template_inspector
    )


def get_update_application_template(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
) -> UpdateApplicationTemplate:
    return UpdateApplicationTemplate(session_maker, application_templates_repo)


def get_publish_application_template(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
) -> PublishApplicationTemplate:
    return PublishApplicationTemplate(session_maker, application_templates_repo)


def get_unpublish_application_template(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
) -> UnpublishApplicationTemplate:
    return UnpublishApplicationTemplate(session_maker, application_templates_repo)


def get_delete_application_template(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
    application_templates_storage: Annotated[ApplicationTemplatesStorage, Depends(get_application_templates_storage)],
) -> DeleteApplicationTemplate:
    return DeleteApplicationTemplate(session_maker, application_templates_repo, application_templates_storage)


def get_application_template_download_url(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
    application_templates_storage: Annotated[ApplicationTemplatesStorage, Depends(get_application_templates_storage)],
) -> GetApplicationTemplateDownloadUrl:
    return GetApplicationTemplateDownloadUrl(session_maker, application_templates_repo, application_templates_storage)
