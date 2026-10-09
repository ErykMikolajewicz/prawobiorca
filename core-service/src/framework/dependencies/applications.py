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
from src.framework.dependencies.application_templates import get_application_templates_repo
from src.framework.dependencies.cases import get_applications_repo, get_applications_storage
from src.framework.dependencies.regulations import get_broker
from src.framework.dependencies.relational import get_session_maker
from src.infrastructure.ai_services.application_writer import ApplicationWriter as LlmApplicationWriter
from src.infrastructure.ai_services.llm_chat import LlmChat
from src.infrastructure.ai_services.llm_cost_limiter import LlmCostLimiter
from src.infrastructure.ai_services.openai_client.connection import client
from src.infrastructure.docx.docx_renderer import DocxApplicationRenderer
from src.infrastructure.relational_db.connection import async_session_maker
from src.infrastructure.relational_db.repositories.llm_usage import LlmUsageRepository
from src.infrastructure.tasks.applications import PostgresApplicationGenerationScheduler
from src.shared.settings.ai_services import llm_service_settings


def get_application_writer() -> ApplicationWriter:
    cost_limiter = None
    if llm_service_settings.MONTHLY_COST_LIMIT_PLN is not None:
        cost_limiter = LlmCostLimiter(
            async_session_maker, LlmUsageRepository(), llm_service_settings.MONTHLY_COST_LIMIT_PLN
        )
    llm_chat = LlmChat(
        client=client,
        model_name=llm_service_settings.MODEL_NAME,
        temperature=llm_service_settings.TEMPERATURE,
        top_p=llm_service_settings.TOP_P,
        max_tokens=llm_service_settings.MAX_TOKENS,
        cost_limiter=cost_limiter,
    )
    return LlmApplicationWriter(llm_chat)


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
