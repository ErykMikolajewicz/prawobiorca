from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqMessage

from src.app.dtos.applications import NewApplication
from src.infrastructure.tasks.broker import insert_task_message
from src.shared.consts import APPLICATION_GENERATION_TASK_NAME


@dataclass
class PostgresApplicationGenerationScheduler:
    broker: Any

    async def schedule_application_generation(
        self, session: AsyncSession, user_id: UUID, application_id: UUID, new_application: NewApplication
    ) -> None:
        message = TaskiqMessage(
            task_id=self.broker.id_generator(),
            task_name=APPLICATION_GENERATION_TASK_NAME,
            labels={},
            labels_types={},
            args=[
                str(user_id),
                str(application_id),
                TypeAdapter(NewApplication).dump_python(new_application, mode="json", by_alias=True),
            ],
            kwargs={},
        )
        await insert_task_message(session, self.broker.formatter.dumps(message))
