from dataclasses import dataclass
from uuid import UUID

from taskiq import AsyncBroker, TaskiqMessage

from core_service.application.ports.relational import AsyncSession
from core_service.infrastructure.relational_db.session import sqla_session
from core_service.infrastructure.tasks.broker import insert_task_message

APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_TASK_NAME = "generate_application_template_description"


@dataclass
class PostgresApplicationTemplateDescriptionGenerationScheduler:
    broker: AsyncBroker

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
        await insert_task_message(sqla_session(session), self.broker.formatter.dumps(message))
