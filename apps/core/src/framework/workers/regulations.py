from uuid import UUID

from taskiq import Context, TaskiqDepends, TaskiqEvents

from src.app.use_cases.regulations import (
    FailRegulationDescriptionGeneration,
    FailRegulationPreparation,
    GenerateRegulationDescription,
    PrepareRegulation,
)
from src.framework.dependencies.file_storage import init_file_storage_client
from src.framework.dependencies.workers import (
    get_fail_regulation_description_generation,
    get_fail_regulation_preparation,
    get_generate_regulation_description,
    get_prepare_regulation,
)
from src.infrastructure.ai_services.initialization import init_ai_services_client
from src.infrastructure.tasks.connection import broker
from src.shared.consts import (
    DELIVERY_ATTEMPT_LABEL,
    REGULATION_DESCRIPTION_GENERATION_TASK_NAME,
    REGULATION_PREPARATION_TASK_NAME,
)


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
    fail_regulation_preparation: FailRegulationPreparation = TaskiqDepends(get_fail_regulation_preparation),
    prepare_regulation: PrepareRegulation = TaskiqDepends(get_prepare_regulation),
) -> None:
    owner_id = UUID(user_id) if user_id is not None else None

    if await fail_regulation_preparation.execute(
        owner_id, UUID(regulation_id), context.message.labels.get(DELIVERY_ATTEMPT_LABEL, 1)
    ):
        return

    await prepare_regulation.execute(owner_id, UUID(regulation_id))


@broker.task(task_name=REGULATION_DESCRIPTION_GENERATION_TASK_NAME)
async def generate_regulation_description_task(
    user_id: str | None,
    regulation_id: str,
    context: Context = TaskiqDepends(),
    fail_description_generation: FailRegulationDescriptionGeneration = TaskiqDepends(
        get_fail_regulation_description_generation
    ),
    generate_description: GenerateRegulationDescription = TaskiqDepends(get_generate_regulation_description),
) -> None:
    owner_id = UUID(user_id) if user_id is not None else None

    if await fail_description_generation.execute(
        owner_id, UUID(regulation_id), context.message.labels.get(DELIVERY_ATTEMPT_LABEL, 1)
    ):
        return

    await generate_description.execute(owner_id, UUID(regulation_id))
