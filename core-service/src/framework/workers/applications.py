from typing import Any
from uuid import UUID

from pydantic import TypeAdapter
from taskiq import Context, TaskiqDepends

from src.app.dtos.applications import NewApplication
from src.app.use_cases.applications import FailApplicationGeneration, GenerateApplication
from src.framework.dependencies.applications import get_application_renderer, get_application_writer
from src.infrastructure.object_storage.repository import S3ApplicationsStorage, S3ApplicationTemplatesStorage
from src.infrastructure.relational_db.connection import async_session_maker
from src.infrastructure.relational_db.repositories.application_templates import ApplicationTemplatesRepository
from src.infrastructure.relational_db.repositories.applications import ApplicationsRepository
from src.infrastructure.relational_db.repositories.cases import CaseDocumentsRepository
from src.infrastructure.tasks.connection import broker
from src.shared.consts import APPLICATION_GENERATION_TASK_NAME, DELIVERY_ATTEMPT_LABEL


@broker.task(task_name=APPLICATION_GENERATION_TASK_NAME)
async def generate_application_task(
    user_id: str,
    application_id: str,
    new_application: dict[str, Any],
    context: Context = TaskiqDepends(),
) -> None:
    fail_application_generation = FailApplicationGeneration(
        session_maker=async_session_maker,
        applications_repo=ApplicationsRepository(),
    )
    if await fail_application_generation.execute(
        UUID(user_id),
        UUID(application_id),
        context.message.labels.get(DELIVERY_ATTEMPT_LABEL, 1),
    ):
        return

    generate_application = GenerateApplication(
        session_maker=async_session_maker,
        case_documents_repo=CaseDocumentsRepository(),
        applications_repo=ApplicationsRepository(),
        applications_storage=S3ApplicationsStorage(
            context.state.file_storage_client, context.state.file_storage_presign_client
        ),
        application_templates_repo=ApplicationTemplatesRepository(),
        application_templates_storage=S3ApplicationTemplatesStorage(
            context.state.file_storage_client, context.state.file_storage_presign_client
        ),
        application_writer=get_application_writer(),
        application_renderer=get_application_renderer(),
    )

    await generate_application.execute(
        UUID(user_id),
        UUID(application_id),
        TypeAdapter(NewApplication).validate_python(new_application),
    )
