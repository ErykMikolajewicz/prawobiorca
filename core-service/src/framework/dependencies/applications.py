from typing import Annotated, Any

from fastapi import Depends

from src.app.interfaces.application_templates import ApplicationTemplatesRepository
from src.app.interfaces.applications import ApplicationsRepository, ApplicationsStorage
from src.app.interfaces.relational import SessionMaker
from src.app.ports.applications import ApplicationRenderer, ApplicationWriter
from src.app.ports.tasks import ApplicationGenerationScheduler
from src.app.use_cases.applications import (
    AddApplication,
    DeleteApplication,
    GetApplicationDownloadUrl,
    ListApplications,
)
from src.framework.dependencies.ai_services import get_llm_chat
from src.framework.dependencies.application_templates import get_application_templates_repo
from src.framework.dependencies.cases import get_applications_repo, get_applications_storage
from src.framework.dependencies.regulations import get_broker
from src.framework.dependencies.relational import get_session_maker
from src.infrastructure.ai_services.application_writer import ApplicationWriter as LlmApplicationWriter
from src.infrastructure.docx.docx_renderer import DocxApplicationRenderer
from src.infrastructure.tasks.applications import PostgresApplicationGenerationScheduler


def get_application_writer() -> ApplicationWriter:
    return LlmApplicationWriter(get_llm_chat())


def get_application_renderer() -> ApplicationRenderer:
    return DocxApplicationRenderer()


def get_application_generation_scheduler(
    broker: Annotated[Any, Depends(get_broker)],
) -> ApplicationGenerationScheduler:
    return PostgresApplicationGenerationScheduler(broker)


def get_add_application(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    applications_repo: Annotated[ApplicationsRepository, Depends(get_applications_repo)],
    application_templates_repo: Annotated[ApplicationTemplatesRepository, Depends(get_application_templates_repo)],
    application_generation_scheduler: Annotated[
        ApplicationGenerationScheduler, Depends(get_application_generation_scheduler)
    ],
) -> AddApplication:
    return AddApplication(
        session_maker, applications_repo, application_templates_repo, application_generation_scheduler
    )


def get_list_applications(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    applications_repo: Annotated[ApplicationsRepository, Depends(get_applications_repo)],
) -> ListApplications:
    return ListApplications(session_maker, applications_repo)


def get_application_download_url(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    applications_repo: Annotated[ApplicationsRepository, Depends(get_applications_repo)],
    applications_storage: Annotated[ApplicationsStorage, Depends(get_applications_storage)],
) -> GetApplicationDownloadUrl:
    return GetApplicationDownloadUrl(session_maker, applications_repo, applications_storage)


def get_delete_application(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    applications_repo: Annotated[ApplicationsRepository, Depends(get_applications_repo)],
    applications_storage: Annotated[ApplicationsStorage, Depends(get_applications_storage)],
) -> DeleteApplication:
    return DeleteApplication(session_maker, applications_repo, applications_storage)
