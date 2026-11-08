from uuid import UUID

import pytest

from core_service.application.use_cases.cases import DeleteCase
from core_service.domain.exceptions.cases import CaseNotFound
from tests.consts import USER_ID
from tests.mocks import get_awaited_arguments

CASE_ID = UUID("4b5c6d7e-8f9a-4b0c-9d1e-2f3a4b5c6d7e")

APPLICATION_IDS = [UUID("2c3d4e5f-6a7b-4c8d-9e0f-1a2b3c4d5e6f"), UUID("8a9b0c1d-2e3f-4a5b-8c6d-7e8f9a0b1c2d")]


@pytest.fixture
def applications_repository(mock_applications_repo):
    mock_applications_repo.list_ids_by_case_id.return_value = APPLICATION_IDS
    return mock_applications_repo


@pytest.fixture
def delete_case(mock_session_maker, mock_cases_repo, applications_repository, mock_applications_storage):
    return DeleteCase(
        session_maker=mock_session_maker,
        cases_repo=mock_cases_repo,
        applications_repo=applications_repository,
        applications_storage=mock_applications_storage,
    )


async def test_delete_case_removes_application_files(delete_case, mock_cases_repo, mock_applications_storage):
    await delete_case.execute(USER_ID, CASE_ID)

    mock_cases_repo.delete.assert_awaited_once()
    assert get_awaited_arguments(mock_applications_storage.delete_application, "id_") == APPLICATION_IDS


async def test_delete_case_ignores_storage_errors(delete_case, mock_applications_storage):
    mock_applications_storage.delete_application.side_effect = Exception("Storage error")

    await delete_case.execute(USER_ID, CASE_ID)

    assert mock_applications_storage.delete_application.await_count == len(APPLICATION_IDS)


async def test_delete_case_not_found(delete_case, mock_cases_repo, mock_applications_storage):
    mock_cases_repo.delete.side_effect = CaseNotFound

    with pytest.raises(CaseNotFound):
        await delete_case.execute(USER_ID, CASE_ID)

    mock_applications_storage.delete_application.assert_not_awaited()
