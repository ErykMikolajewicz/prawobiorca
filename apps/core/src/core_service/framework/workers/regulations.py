from uuid import UUID

from taskiq import Context, TaskiqDepends

from core_service.application.use_cases.regulations import (
    FailRegulationDescriptionGeneration,
    FailRegulationPreparation,
    GenerateRegulationDescription,
    PrepareRegulation,
)
from core_service.framework.dependencies.workers import (
    get_fail_regulation_description_generation,
    get_fail_regulation_preparation,
    get_generate_regulation_description,
    get_prepare_regulation,
)
from core_service.infrastructure.tasks.broker import DELIVERY_ATTEMPT_LABEL
from core_service.infrastructure.tasks.connection import broker
from core_service.infrastructure.tasks.regulations import (
    REGULATION_DESCRIPTION_GENERATION_TASK_NAME,
    REGULATION_PREPARATION_TASK_NAME,
)


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
