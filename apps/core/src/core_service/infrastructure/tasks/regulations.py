from dataclasses import dataclass
from uuid import UUID

from taskiq import AsyncBroker, TaskiqMessage

from core_service.application.ports.relational import AsyncSession
from core_service.infrastructure.relational_db.session import sqla_session
from core_service.infrastructure.tasks.broker import insert_task_message

REGULATION_PREPARATION_TASK_NAME = "prepare_regulation"

REGULATION_DESCRIPTION_GENERATION_TASK_NAME = "generate_regulation_description"


@dataclass
class PostgresRegulationPreparationScheduler:
    broker: AsyncBroker

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
        await insert_task_message(sqla_session(session), self.broker.formatter.dumps(message))


@dataclass
class PostgresRegulationDescriptionGenerationScheduler:
    broker: AsyncBroker

    async def schedule_regulation_description_generation(
        self, session: AsyncSession, user_id: UUID | None, regulation_id: UUID
    ) -> None:
        message = TaskiqMessage(
            task_id=self.broker.id_generator(),
            task_name=REGULATION_DESCRIPTION_GENERATION_TASK_NAME,
            labels={},
            labels_types={},
            args=[str(user_id) if user_id is not None else None, str(regulation_id)],
            kwargs={},
        )
        await insert_task_message(sqla_session(session), self.broker.formatter.dumps(message))
