from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqMessage

from core_service.infrastructure.tasks.broker import insert_task_message

APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_TASK_NAME = "generate_application_template_description"


@dataclass
class PostgresApplicationTemplateDescriptionGenerationScheduler:
    broker: Any

    async def schedule_application_template_description_generation(
        self, session: AsyncSession, template_id: UUID
    ) -> None:
        message = TaskiqMessage(
            task_id=self.broker.id_generator(),
            task_name=APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_TASK_NAME,
            labels={},
            labels_types={},
            args=[str(template_id)],
            kwargs={},
        )
        await insert_task_message(session, self.broker.formatter.dumps(message))
