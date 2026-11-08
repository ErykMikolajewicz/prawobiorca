from typing import Annotated, Any

from fastapi import Depends

from core_service.application.interfaces.application_templates import ApplicationTemplatesRepository
from core_service.application.interfaces.applications import ApplicationsRepository, ApplicationsStorage
from core_service.application.interfaces.relational import SessionMaker
from core_service.application.ports.tasks import ApplicationGenerationScheduler
from core_service.application.use_cases.applications import (
    AddApplication,
    DeleteApplication,
    GetApplicationDownloadUrl,
    ListApplications,
)
from core_service.framework.dependencies.application_templates import get_application_templates_repo
from core_service.framework.dependencies.cases import get_applications_repo, get_applications_storage
from core_service.framework.dependencies.regulations import get_broker
from core_service.framework.dependencies.relational import get_session_maker
from core_service.infrastructure.tasks.applications import PostgresApplicationGenerationScheduler


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
