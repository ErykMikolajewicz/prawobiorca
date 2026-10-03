from typing import Annotated

from fastapi import Depends

from src.app.interfaces.cases import CaseDocumentsRepository
from src.app.interfaces.relational import SessionMaker
from src.app.ports.applications import ApplicationRenderer, ApplicationWriter
from src.app.use_cases.applications import GenerateApplication
from src.framework.dependencies.cases import get_case_documents_repo
from src.framework.dependencies.relational import get_session_maker
from src.infrastructure.ai_services.application_writer import ApplicationWriter as LlmApplicationWriter
from src.infrastructure.ai_services.llm_chat import LlmChat
from src.infrastructure.ai_services.openai_client.connection import client
from src.infrastructure.docx.docx_renderer import DocxApplicationRenderer
from src.shared.settings.ai_services import llm_service_settings


def get_application_writer() -> ApplicationWriter:
    llm_chat = LlmChat(
        client=client,
        model_name=llm_service_settings.MODEL_NAME,
        temperature=llm_service_settings.TEMPERATURE,
        top_p=llm_service_settings.TOP_P,
        max_tokens=llm_service_settings.MAX_TOKENS,
    )
    return LlmApplicationWriter(llm_chat)


def get_application_renderer() -> ApplicationRenderer:
    return DocxApplicationRenderer()


def get_generate_application(
    session_maker: Annotated[SessionMaker, Depends(get_session_maker)],
    case_documents_repo: Annotated[CaseDocumentsRepository, Depends(get_case_documents_repo)],
    application_writer: Annotated[ApplicationWriter, Depends(get_application_writer)],
    application_renderer: Annotated[ApplicationRenderer, Depends(get_application_renderer)],
) -> GenerateApplication:
    return GenerateApplication(session_maker, case_documents_repo, application_writer, application_renderer)
