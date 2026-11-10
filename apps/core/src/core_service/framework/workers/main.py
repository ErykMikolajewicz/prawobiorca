from taskiq import TaskiqEvents, TaskiqState

from core_service.framework.dependencies.file_storage import init_file_storage_client
from core_service.infrastructure.ai_services.initialization import init_ai_services_client
from core_service.infrastructure.ai_services.openai_client.connection import init_llm_client
from core_service.infrastructure.tasks.connection import broker


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def on_worker_startup(state: TaskiqState) -> None:
    state.closing_callbacks = []

    ai_services_client, close_ai_services_client = await init_ai_services_client()
    state.ai_services_client = ai_services_client
    state.closing_callbacks.insert(0, close_ai_services_client)

    llm_client, close_llm_client = await init_llm_client()
    state.llm_client = llm_client
    state.closing_callbacks.insert(0, close_llm_client)

    file_storage_client, file_storage_presign_client, close_file_storage_client = await init_file_storage_client()
    state.file_storage_client = file_storage_client
    state.file_storage_presign_client = file_storage_presign_client
    state.closing_callbacks.insert(0, close_file_storage_client)


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def on_worker_shutdown(state: TaskiqState) -> None:
    for callback in state.closing_callbacks:
        await callback()
