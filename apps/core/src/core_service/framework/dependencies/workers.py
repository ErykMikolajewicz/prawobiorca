from typing import Any

from httpx2 import AsyncClient
from taskiq import Context, TaskiqDepends, TaskiqState

from core_service.application.interfaces.application_templates import (
    ApplicationTemplatesRepository,
    ApplicationTemplatesStorage,
)
from core_service.application.interfaces.applications import ApplicationsRepository, ApplicationsStorage
from core_service.application.interfaces.cases import CaseDocumentsRepository
from core_service.application.interfaces.regulations import RegulationsRepository, RegulationsStorage
from core_service.application.interfaces.relational import SessionMaker
from core_service.application.interfaces.sections import SectionsRepository
from core_service.application.ports.application_templates import (
    ApplicationTemplateDescriptionWriter,
    ApplicationTemplateInspector,
)
from core_service.application.ports.applications import ApplicationRenderer, ApplicationWriter
from core_service.application.ports.regulations import RegulationDescriptionWriter, RegulationSplitter
from core_service.application.ports.tasks import RegulationDescriptionGenerationScheduler
from core_service.application.ports.texts import TextsEmbedder
from core_service.application.ports.tokenizer import Tokenizer
from core_service.application.services.embedding import SectionsEmbedder
from core_service.application.services.regulations import RegulationPreparator
from core_service.application.use_cases.application_templates import (
    FailApplicationTemplateDescriptionGeneration,
    GenerateApplicationTemplateDescription,
)
from core_service.application.use_cases.applications import FailApplicationGeneration, GenerateApplication
from core_service.application.use_cases.regulations import (
    FailRegulationDescriptionGeneration,
    FailRegulationPreparation,
    GenerateRegulationDescription,
    PrepareRegulation,
)
from core_service.framework.dependencies.application_templates import (
    get_application_template_inspector,
    get_application_templates_repo,
)
from core_service.framework.dependencies.cases import get_applications_repo, get_case_documents_repo
from core_service.framework.dependencies.regulations import get_regulation_repository, get_sections_repository
from core_service.framework.dependencies.relational import get_session_maker
from core_service.framework.dependencies.tokenizer import get_tokenizer
from core_service.infrastructure.ai_services.application_template_description_writer import (
    ApplicationTemplateDescriptionWriter as LlmApplicationTemplateDescriptionWriter,
)
from core_service.infrastructure.ai_services.application_writer import ApplicationWriter as LlmApplicationWriter
from core_service.infrastructure.ai_services.llm_chat import LlmChat
from core_service.infrastructure.ai_services.llm_cost_limiter import LlmCostLimiter
from core_service.infrastructure.ai_services.openai_client.connection import client as llm_client
from core_service.infrastructure.ai_services.regulation_description_writer import (
    RegulationDescriptionWriter as LlmRegulationDescriptionWriter,
)
from core_service.infrastructure.ai_services.regulation_splitter import RegulationSplitter as HttpRegulationSplitter
from core_service.infrastructure.ai_services.text_embedder import TextsEmbedder as HttpTextsEmbedder
from core_service.infrastructure.docx.docx_renderer import DocxApplicationRenderer
from core_service.infrastructure.object_storage.repository import (
    S3ApplicationsStorage,
    S3ApplicationTemplatesStorage,
    S3RegulationsStorage,
)
from core_service.infrastructure.relational_db.repositories.llm_usage import LlmUsageRepository
from core_service.infrastructure.tasks.regulations import PostgresRegulationDescriptionGenerationScheduler
from core_service.shared.settings.ai_services import (
    embedding_service_settings,
    extraction_service_settings,
    llm_service_settings,
)


def get_ai_services_client(state: TaskiqState = TaskiqDepends()) -> AsyncClient:
    return state.ai_services_client


def get_texts_embedder(client: AsyncClient = TaskiqDepends(get_ai_services_client)) -> TextsEmbedder:
    return HttpTextsEmbedder(client=client, embedding_service_url=embedding_service_settings.URL)


def get_regulation_splitter(client: AsyncClient = TaskiqDepends(get_ai_services_client)) -> RegulationSplitter:
    return HttpRegulationSplitter(client=client, extraction_service_url=extraction_service_settings.URL)


def get_regulations_storage(state: TaskiqState = TaskiqDepends()) -> RegulationsStorage:
    return S3RegulationsStorage(state.file_storage_client, state.file_storage_presign_client)


def get_applications_storage(state: TaskiqState = TaskiqDepends()) -> ApplicationsStorage:
    return S3ApplicationsStorage(state.file_storage_client, state.file_storage_presign_client)


def get_application_templates_storage(state: TaskiqState = TaskiqDepends()) -> ApplicationTemplatesStorage:
    return S3ApplicationTemplatesStorage(state.file_storage_client, state.file_storage_presign_client)


def get_broker(context: Context = TaskiqDepends()) -> Any:
    return context.broker


def get_regulation_description_generation_scheduler(
    broker: Any = TaskiqDepends(get_broker),
) -> RegulationDescriptionGenerationScheduler:
    return PostgresRegulationDescriptionGenerationScheduler(broker)


def get_llm_chat(session_maker: SessionMaker = TaskiqDepends(get_session_maker)) -> LlmChat:
    cost_limiter = None
    if llm_service_settings.MONTHLY_COST_LIMIT_PLN is not None:
        cost_limiter = LlmCostLimiter(session_maker, LlmUsageRepository(), llm_service_settings.MONTHLY_COST_LIMIT_PLN)
    return LlmChat(
        client=llm_client,
        model_name=llm_service_settings.MODEL_NAME,
        temperature=llm_service_settings.TEMPERATURE,
        top_p=llm_service_settings.TOP_P,
        max_tokens=llm_service_settings.MAX_TOKENS,
        cost_limiter=cost_limiter,
    )


def get_regulation_description_writer(llm_chat: LlmChat = TaskiqDepends(get_llm_chat)) -> RegulationDescriptionWriter:
    return LlmRegulationDescriptionWriter(llm_chat)


def get_application_template_description_writer(
    llm_chat: LlmChat = TaskiqDepends(get_llm_chat),
) -> ApplicationTemplateDescriptionWriter:
    return LlmApplicationTemplateDescriptionWriter(llm_chat)


def get_application_writer(llm_chat: LlmChat = TaskiqDepends(get_llm_chat)) -> ApplicationWriter:
    return LlmApplicationWriter(llm_chat)


def get_application_renderer() -> ApplicationRenderer:
    return DocxApplicationRenderer()


def get_regulation_preparator(
    regulation_splitter: RegulationSplitter = TaskiqDepends(get_regulation_splitter),
    texts_embedder: TextsEmbedder = TaskiqDepends(get_texts_embedder),
    tokenizer: Tokenizer = TaskiqDepends(get_tokenizer),
) -> RegulationPreparator:
    return RegulationPreparator(
        regulation_splitter, SectionsEmbedder(texts_embedder, embedding_service_settings.BATCH_SIZE), tokenizer
    )


def get_fail_regulation_preparation(
    session_maker: SessionMaker = TaskiqDepends(get_session_maker),
    regulations_repository: RegulationsRepository = TaskiqDepends(get_regulation_repository),
) -> FailRegulationPreparation:
    return FailRegulationPreparation(session_maker, regulations_repository)


def get_prepare_regulation(
    session_maker: SessionMaker = TaskiqDepends(get_session_maker),
    regulations_storage: RegulationsStorage = TaskiqDepends(get_regulations_storage),
    sections_repository: SectionsRepository = TaskiqDepends(get_sections_repository),
    regulations_repository: RegulationsRepository = TaskiqDepends(get_regulation_repository),
    regulation_preparator: RegulationPreparator = TaskiqDepends(get_regulation_preparator),
    description_generation_scheduler: RegulationDescriptionGenerationScheduler = TaskiqDepends(
        get_regulation_description_generation_scheduler
    ),
) -> PrepareRegulation:
    return PrepareRegulation(
        session_maker,
        regulations_storage,
        sections_repository,
        regulations_repository,
        regulation_preparator,
        description_generation_scheduler,
    )


def get_fail_regulation_description_generation(
    session_maker: SessionMaker = TaskiqDepends(get_session_maker),
    regulations_repository: RegulationsRepository = TaskiqDepends(get_regulation_repository),
) -> FailRegulationDescriptionGeneration:
    return FailRegulationDescriptionGeneration(session_maker, regulations_repository)


def get_generate_regulation_description(
    session_maker: SessionMaker = TaskiqDepends(get_session_maker),
    regulations_repository: RegulationsRepository = TaskiqDepends(get_regulation_repository),
    sections_repository: SectionsRepository = TaskiqDepends(get_sections_repository),
    description_writer: RegulationDescriptionWriter = TaskiqDepends(get_regulation_description_writer),
    texts_embedder: TextsEmbedder = TaskiqDepends(get_texts_embedder),
) -> GenerateRegulationDescription:
    return GenerateRegulationDescription(
        session_maker, regulations_repository, sections_repository, description_writer, texts_embedder
    )


def get_fail_application_generation(
    session_maker: SessionMaker = TaskiqDepends(get_session_maker),
    applications_repo: ApplicationsRepository = TaskiqDepends(get_applications_repo),
) -> FailApplicationGeneration:
    return FailApplicationGeneration(session_maker, applications_repo)


def get_generate_application(
    session_maker: SessionMaker = TaskiqDepends(get_session_maker),
    case_documents_repo: CaseDocumentsRepository = TaskiqDepends(get_case_documents_repo),
    applications_repo: ApplicationsRepository = TaskiqDepends(get_applications_repo),
    applications_storage: ApplicationsStorage = TaskiqDepends(get_applications_storage),
    application_templates_repo: ApplicationTemplatesRepository = TaskiqDepends(get_application_templates_repo),
    application_templates_storage: ApplicationTemplatesStorage = TaskiqDepends(get_application_templates_storage),
    application_writer: ApplicationWriter = TaskiqDepends(get_application_writer),
    application_renderer: ApplicationRenderer = TaskiqDepends(get_application_renderer),
) -> GenerateApplication:
    return GenerateApplication(
        session_maker,
        case_documents_repo,
        applications_repo,
        applications_storage,
        application_templates_repo,
        application_templates_storage,
        application_writer,
        application_renderer,
    )


def get_fail_application_template_description_generation(
    session_maker: SessionMaker = TaskiqDepends(get_session_maker),
    application_templates_repo: ApplicationTemplatesRepository = TaskiqDepends(get_application_templates_repo),
) -> FailApplicationTemplateDescriptionGeneration:
    return FailApplicationTemplateDescriptionGeneration(session_maker, application_templates_repo)


def get_generate_application_template_description(
    session_maker: SessionMaker = TaskiqDepends(get_session_maker),
    application_templates_repo: ApplicationTemplatesRepository = TaskiqDepends(get_application_templates_repo),
    application_templates_storage: ApplicationTemplatesStorage = TaskiqDepends(get_application_templates_storage),
    application_template_inspector: ApplicationTemplateInspector = TaskiqDepends(get_application_template_inspector),
    description_writer: ApplicationTemplateDescriptionWriter = TaskiqDepends(
        get_application_template_description_writer
    ),
    texts_embedder: TextsEmbedder = TaskiqDepends(get_texts_embedder),
) -> GenerateApplicationTemplateDescription:
    return GenerateApplicationTemplateDescription(
        session_maker,
        application_templates_repo,
        application_templates_storage,
        application_template_inspector,
        description_writer,
        texts_embedder,
    )
