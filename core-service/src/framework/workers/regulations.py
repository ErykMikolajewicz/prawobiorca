from uuid import UUID

from taskiq import Context, TaskiqDepends, TaskiqEvents

from src.app.services.embedding import SectionsEmbedder
from src.app.services.regulations import RegulationPreparator
from src.app.use_cases.regulations import FailRegulationPreparation, PrepareRegulation
from src.framework.dependencies.file_storage import init_file_storage_client
from src.framework.dependencies.tokenizer import get_tokenizer
from src.infrastructure.ai_services.initialization import init_ai_services_client
from src.infrastructure.ai_services.regulation_splitter import RegulationSplitter
from src.infrastructure.ai_services.text_embedder import TextsEmbedder
from src.infrastructure.object_storage.repository import S3RegulationsStorage
from src.infrastructure.relational_db.connection import async_session_maker
from src.infrastructure.relational_db.repositories.regulations import RegulationsManagerRepository
from src.infrastructure.relational_db.repositories.sections import RegulationsSectionsRepository
from src.infrastructure.tasks.connection import broker
from src.shared.consts import DELIVERY_ATTEMPT_LABEL, REGULATION_PREPARATION_TASK_NAME
from src.shared.settings.ai_services import embedding_service_settings, extraction_service_settings


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def on_worker_startup(state) -> None:
    state.closing_callbacks = []

    ai_services_client, close_ai_services_client = await init_ai_services_client()
    state.ai_services_client = ai_services_client
    state.closing_callbacks.insert(0, close_ai_services_client)

    file_storage_client, file_storage_presign_client, close_file_storage_client = await init_file_storage_client()
    state.file_storage_client = file_storage_client
    state.file_storage_presign_client = file_storage_presign_client
    state.closing_callbacks.insert(0, close_file_storage_client)


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def on_worker_shutdown(state) -> None:
    for callback in state.closing_callbacks:
        await callback()


@broker.task(task_name=REGULATION_PREPARATION_TASK_NAME)
async def prepare_regulation_task(
    user_id: str | None,
    regulation_id: str,
    context: Context = TaskiqDepends(),
) -> None:
    fail_regulation_preparation = FailRegulationPreparation(
        session_maker=async_session_maker,
        regulations_repository=RegulationsManagerRepository(),
    )
    if await fail_regulation_preparation.execute(
        UUID(user_id) if user_id is not None else None,
        UUID(regulation_id),
        context.message.labels.get(DELIVERY_ATTEMPT_LABEL, 1),
    ):
        return

    ai_services_client = context.state.ai_services_client
    file_storage_client = context.state.file_storage_client
    file_storage_presign_client = context.state.file_storage_presign_client

    texts_embedder = TextsEmbedder(client=ai_services_client, embedding_service_url=embedding_service_settings.URL)
    regulations_splitter = RegulationSplitter(
        client=ai_services_client, extraction_service_url=extraction_service_settings.URL
    )

    prepare_regulation = PrepareRegulation(
        session_maker=async_session_maker,
        regulations_storage=S3RegulationsStorage(file_storage_client, file_storage_presign_client),
        sections_repository=RegulationsSectionsRepository(),
        regulations_repository=RegulationsManagerRepository(),
        regulation_preparator=RegulationPreparator(
            regulations_splitter,
            SectionsEmbedder(texts_embedder, embedding_service_settings.BATCH_SIZE),
            get_tokenizer(),
        ),
    )

    await prepare_regulation.execute(
        UUID(user_id) if user_id is not None else None,
        UUID(regulation_id),
    )
