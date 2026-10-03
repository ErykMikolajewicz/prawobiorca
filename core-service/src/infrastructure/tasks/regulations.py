from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from taskiq import TaskiqMessage

from src.infrastructure.tasks.broker import insert_task_message
from src.shared.consts import REGULATION_PREPARATION_TASK_NAME


@dataclass
class PostgresRegulationPreparationScheduler:
    broker: Any

    async def schedule_regulation_preparation(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID
    ) -> None:
        message = TaskiqMessage(
            task_id=self.broker.id_generator(),
            task_name=REGULATION_PREPARATION_TASK_NAME,
            labels={},
            labels_types={},
            args=[str(user_id) if user_id is not None else None, str(regulation_id)],
            kwargs={},
        )
        await insert_task_message(session, self.broker.formatter.dumps(message))
