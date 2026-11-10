import pytest
from fastapi import status
from sqlalchemy import select

from core_service.application.use_cases.regulations import MAX_REGULATION_PREPARATION_DELIVERIES
from core_service.domain.value_objects.descriptions import DescriptionStatus
from core_service.domain.value_objects.regulations import RegulationPreparationStatus
from core_service.infrastructure.relational_db.schemas.regulations import regulations_table
from core_service.infrastructure.tasks.connection import DEFAULT_TASK_RETRY_COUNT
from core_service.infrastructure.tasks.regulations import (
    REGULATION_DESCRIPTION_GENERATION_TASK_NAME,
    REGULATION_PREPARATION_TASK_NAME,
    PostgresRegulationPreparationScheduler,
)
from core_service.shared.exceptions import ServiceUnavailable
from tests.consts import USER_ID
from tests.fixtures.regulation_elements import load_regulation_elements
from tests.integration.fixtures.ai_services import DESCRIPTION_VECTOR, QUERY_VECTOR
from tests.integration.fixtures.regulations import insert_regulation, insert_section
from tests.integration.fixtures.tasks import execute_task, get_scheduled_task_names, get_scheduled_tasks
from tests.mocks import get_awaited_argument


async def get_regulation(session_maker, regulation_id):
    async with session_maker() as session:
        result = await session.execute(select(regulations_table).where(regulations_table.c.id == regulation_id))
    return result.one()


async def test_prepared_regulation_is_searchable(
    user_client, session_maker, broker, mock_regulations_storage, mock_regulation_splitter, mock_texts_embedder
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID, description_status=DescriptionStatus.IN_PROGRESS)
    mock_regulations_storage.check_regulation_exists.return_value = True
    mock_regulations_storage.get_regulation.return_value = b"%PDF"
    mock_regulation_splitter.split.return_value = load_regulation_elements("ustawa-nauka_slice_30-31")
    mock_texts_embedder.embed_chunks.side_effect = lambda chunks: [QUERY_VECTOR for _ in chunks]

    response = await user_client.post(f"/api/regulations/{regulation_id}/confirm-upload")
    assert response.status_code == status.HTTP_202_ACCEPTED
    (task,) = await get_scheduled_tasks(session_maker)

    await execute_task(broker, task)

    mock_regulation_splitter.split.assert_awaited_once_with(b"%PDF")
    regulation = await get_regulation(session_maker, regulation_id)
    assert regulation.preparation_status == RegulationPreparationStatus.PREPARED
    assert await get_scheduled_task_names(session_maker) == [
        REGULATION_PREPARATION_TASK_NAME,
        REGULATION_DESCRIPTION_GENERATION_TASK_NAME,
    ]

    response = await user_client.get(
        f"/api/regulations/{regulation_id}/documents", params={"threshold": 0.9, "query": "zapytanie"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert "Art. 107" in [result["header"] for result in response.json()]


async def test_regulation_preparation_over_delivery_limit_marks_regulation_failed(
    user, session_maker, broker, mock_regulation_splitter
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(
            session, USER_ID, preparation_status=RegulationPreparationStatus.IN_PROGRESS
        )
        await PostgresRegulationPreparationScheduler(broker).schedule_regulation_preparation(
            session, USER_ID, regulation_id
        )
    (task,) = await get_scheduled_tasks(session_maker)

    await execute_task(broker, task, delivery_attempt=MAX_REGULATION_PREPARATION_DELIVERIES + 1)

    regulation = await get_regulation(session_maker, regulation_id)
    assert regulation.preparation_status == RegulationPreparationStatus.FAILED
    mock_regulation_splitter.split.assert_not_awaited()


@pytest.mark.parametrize(
    ("retries", "expected_status"),
    [
        (0, RegulationPreparationStatus.IN_PROGRESS),
        (DEFAULT_TASK_RETRY_COUNT - 1, RegulationPreparationStatus.FAILED),
    ],
    ids=("retried", "last attempt"),
)
async def test_regulation_preparation_with_unavailable_service_is_marked_failed_on_last_attempt(
    user, session_maker, broker, mock_regulations_storage, mock_regulation_splitter, retries, expected_status
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(
            session, USER_ID, preparation_status=RegulationPreparationStatus.IN_PROGRESS
        )
        await PostgresRegulationPreparationScheduler(broker).schedule_regulation_preparation(
            session, USER_ID, regulation_id
        )
    (task,) = await get_scheduled_tasks(session_maker)
    mock_regulations_storage.get_regulation.return_value = b"%PDF"
    mock_regulation_splitter.split.side_effect = ServiceUnavailable

    with pytest.raises(ServiceUnavailable):
        await execute_task(broker, task, retries=retries)

    regulation = await get_regulation(session_maker, regulation_id)
    assert regulation.preparation_status == expected_status


async def test_generated_regulation_description_is_saved(
    admin_client, session_maker, broker, mock_regulation_description_writer
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(
            session, None, "Regulamin studiów.pdf", preparation_status=RegulationPreparationStatus.PREPARED
        )
        await insert_section(session, regulation_id, "Student ma prawo do urlopu.", [QUERY_VECTOR])
    mock_regulation_description_writer.write.return_value = "Prawa i obowiązki studentów."

    response = await admin_client.post(f"/api/regulations/{regulation_id}/description-generation")
    assert response.status_code == status.HTTP_202_ACCEPTED
    (task,) = await get_scheduled_tasks(session_maker)

    await execute_task(broker, task)

    description_source = get_awaited_argument(mock_regulation_description_writer.write, "description_source")
    assert description_source.presentation_name == "Regulamin studiów.pdf"
    assert description_source.beginning == "Student ma prawo do urlopu."
    regulation = await get_regulation(session_maker, regulation_id)
    assert regulation.description == "Prawa i obowiązki studentów."
    assert list(regulation.description_vector) == DESCRIPTION_VECTOR
    assert regulation.description_status == DescriptionStatus.GENERATED
