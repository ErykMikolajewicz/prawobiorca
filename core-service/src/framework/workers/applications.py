from typing import Any
from uuid import UUID

from pydantic import TypeAdapter
from taskiq import Context, TaskiqDepends

from src.app.dtos.applications import NewApplication
from src.app.use_cases.application_templates import (
    FailApplicationTemplateDescriptionGeneration,
    GenerateApplicationTemplateDescription,
)
from src.app.use_cases.applications import FailApplicationGeneration, GenerateApplication
from src.framework.dependencies.workers import (
    get_fail_application_generation,
    get_fail_application_template_description_generation,
    get_generate_application,
    get_generate_application_template_description,
)
from src.infrastructure.tasks.connection import broker
from src.shared.consts import (
    APPLICATION_GENERATION_TASK_NAME,
    APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_TASK_NAME,
    DELIVERY_ATTEMPT_LABEL,
)


@broker.task(task_name=APPLICATION_GENERATION_TASK_NAME)
async def generate_application_task(
    user_id: str,
    application_id: str,
    new_application: dict[str, Any],
    context: Context = TaskiqDepends(),
    fail_application_generation: FailApplicationGeneration = TaskiqDepends(get_fail_application_generation),
    generate_application: GenerateApplication = TaskiqDepends(get_generate_application),
) -> None:
    if await fail_application_generation.execute(
        UUID(user_id), UUID(application_id), context.message.labels.get(DELIVERY_ATTEMPT_LABEL, 1)
    ):
        return

    await generate_application.execute(
        UUID(user_id), UUID(application_id), TypeAdapter(NewApplication).validate_python(new_application)
    )


@broker.task(task_name=APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_TASK_NAME)
async def generate_application_template_description_task(
    template_id: str,
    context: Context = TaskiqDepends(),
    fail_description_generation: FailApplicationTemplateDescriptionGeneration = TaskiqDepends(
        get_fail_application_template_description_generation
    ),
    generate_description: GenerateApplicationTemplateDescription = TaskiqDepends(
        get_generate_application_template_description
    ),
) -> None:
    if await fail_description_generation.execute(
        UUID(template_id), context.message.labels.get(DELIVERY_ATTEMPT_LABEL, 1)
    ):
        return

    await generate_description.execute(UUID(template_id))
