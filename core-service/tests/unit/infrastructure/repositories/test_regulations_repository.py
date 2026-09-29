from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.domain.exceptions.regulations import RegulationNotFound
from src.domain.value_objects.regulations import RegulationDetails, RegulationPreparationStatus
from src.infrastructure.relational_db.repositories.regulations import RegulationsManagerRepository


@pytest.mark.parametrize("status", list(RegulationPreparationStatus))
async def test_set_preparation_status_callable_from_instance(status):
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = uuid4()
    session.execute.return_value = mock_result

    repo = RegulationsManagerRepository()
    user_id = uuid4()
    regulation_id = uuid4()

    await repo.set_preparation_status(session, user_id, regulation_id, status)

    session.execute.assert_awaited_once()


async def test_update_regulation_details_not_found():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.one_or_none.return_value = None
    session.scalars.return_value = mock_result

    repo = RegulationsManagerRepository()

    with pytest.raises(RegulationNotFound):
        await repo.update_regulation_details(session, uuid4(), uuid4(), RegulationDetails(presentation_name="Name"))
