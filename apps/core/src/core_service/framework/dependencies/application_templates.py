from typing import Annotated, Any

from fastapi import Depends
from taskiq import AsyncBroker

from core_service.application.ports.application_templates import (
    ApplicationTemplateInspector,
    ApplicationTemplateInstructionsProvider,
    ApplicationTemplatesRepository,
    ApplicationTemplatesStorage,
)
from core_service.application.ports.relational import SessionMaker
from core_service.application.ports.tasks import ApplicationTemplateDescriptionGenerationScheduler
from core_service.application.ports.texts import TextsEmbedder
from core_service.application.use_cases.application_templates import (
    AddApplicationTemplate,
    ConfirmApplicationTemplateUpload,
    DeleteApplicationTemplate,
    GetApplicationTemplate,
    GetApplicationTemplateDownloadUrl,
    ListApplicationTemplates,
    ListPublishedApplicationTemplates,
    PublishApplicationTemplate,
    RegenerateApplicationTemplateDescription,
    SearchPublishedApplicationTemplates,
    UnpublishApplicationTemplate,
    UpdateApplicationTemplate,
)
from core_service.framework.dependencies.ai_services import get_texts_embedder
from core_service.framework.dependencies.file_storage import (
    create_application_templates_storage,
    get_file_storage_client,
    get_file_storage_presign_client,
)
from core_service.framework.dependencies.regulations import get_broker
from core_service.framework.dependencies.relational import get_session_maker
from core_service.infrastructure.ai_services.application_template_instructions import (
    PromptsApplicationTemplateInstructionsProvider,
)
from core_service.infrastructure.docx.template_inspector import DocxTemplateInspector
from core_service.infrastructure.relational_db.repositories.application_templates import (
    SqlaApplicationTemplatesRepository,
)
from core_service.infrastructure.tasks.application_templates import (
    PostgresApplicationTemplateDescriptionGenerationScheduler,
)


def get_application_templates_repo() -> ApplicationTemplatesRepository:
    return SqlaApplicationTemplatesRepository()


def get_application_templates_storage(
    client: Annotated[Any, Depends(get_file_storage_client)],
    presign_client: Annotated[Any, Depends(get_file_storage_presign_client)],
) -> ApplicationTemplatesStorage:
    return create_application_templates_storage(client, presign_client)


def get_application_template_inspector() -> ApplicationTemplateInspector:
    return DocxTemplateInspector()


def get_application_template_instructions_provider() -> ApplicationTemplateInstructionsProvider:
    return PromptsApplicationTemplateInstructionsProvider()


def get_application_template_description_generation_scheduler(
    broker: Annotated[AsyncBroker, Depends(get_broker)],
) -> ApplicationTemplateDescriptionGenerationScheduler:
    return PostgresApplicationTemplateDescriptionGenerationScheduler(broker)


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


def get_search_published_application_templates(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    texts_embedder: Annotated[TextsEmbedder, Depends(get_texts_embedder)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
) -> SearchPublishedApplicationTemplates:
    return SearchPublishedApplicationTemplates(session_maker, texts_embedder, application_templates_repo)


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
    texts_embedder: Annotated[TextsEmbedder, Depends(get_texts_embedder)],
) -> UpdateApplicationTemplate:
    return UpdateApplicationTemplate(session_maker, application_templates_repo, texts_embedder)


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


def get_regenerate_application_template_description(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
    description_generation_scheduler: Annotated[
        ApplicationTemplateDescriptionGenerationScheduler,
        Depends(get_application_template_description_generation_scheduler),
    ],
) -> RegenerateApplicationTemplateDescription:
    return RegenerateApplicationTemplateDescription(
        session_maker, application_templates_repo, description_generation_scheduler
    )


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
