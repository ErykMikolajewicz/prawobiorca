from datetime import datetime

import pytest

from src.app.dtos.applications import ApplicationRepresentation, NewApplication
from src.app.dtos.cases import CaseDocument
from src.app.use_cases.applications import (
    DeleteApplication,
    GenerateApplication,
    GetApplicationDownloadUrl,
    ListApplications,
)
from src.domain.exceptions.applications import ApplicationNotFound
from src.domain.exceptions.cases import CaseNotFound
from src.domain.value_objects.applications import ApplicationType


@pytest.fixture
def new_application():
    return NewApplication(
        description="Proszę o urlop dziekański.",
        userName="Jan Kowalski",
        studentId="123456",
        department="Wydział Informatyki i Telekomunikacji",
        semester="4",
        title="inż.",
    )


async def test_generate_application_success(
    mock_session_maker,
    mock_opened_session,
    mock_case_documents_repo,
    mock_applications_repo,
    mock_applications_storage,
    mock_application_writer,
    mock_application_renderer,
    new_application,
    uuid_generator,
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    application_id = next(uuid_generator)
    document = CaseDocument(id=next(uuid_generator), caseId=case_id, presentationName="doc.pdf", content="text")
    mock_case_documents_repo.list_by_case_id.return_value = [document]
    mock_application_writer.write.return_value = "Szanowny Panie Dziekanie"
    mock_application_renderer.render.return_value = b"PK"
    mock_applications_repo.add.return_value = application_id

    use_case = GenerateApplication(
        session_maker=mock_session_maker,
        case_documents_repo=mock_case_documents_repo,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
        application_writer=mock_application_writer,
        application_renderer=mock_application_renderer,
    )
    result = await use_case.execute(user_id, case_id, new_application)

    assert result == b"PK"
    mock_case_documents_repo.list_by_case_id.assert_awaited_once_with(mock_opened_session, user_id, case_id)
    mock_application_writer.write.assert_awaited_once_with(new_application, [document])
    mock_application_renderer.render.assert_awaited_once_with(new_application, "Szanowny Panie Dziekanie")
    mock_applications_repo.add.assert_awaited_once_with(mock_opened_session, user_id, case_id, ApplicationType.OTHER)
    mock_applications_storage.upload_application.assert_awaited_once_with(application_id, b"PK")


async def test_generate_application_case_not_found(
    mock_session_maker,
    mock_case_documents_repo,
    mock_applications_repo,
    mock_applications_storage,
    mock_application_writer,
    mock_application_renderer,
    new_application,
    uuid_generator,
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    mock_case_documents_repo.list_by_case_id.return_value = []
    mock_application_writer.write.return_value = "Szanowny Panie Dziekanie"
    mock_application_renderer.render.return_value = b"PK"
    mock_applications_repo.add.side_effect = CaseNotFound()

    use_case = GenerateApplication(
        session_maker=mock_session_maker,
        case_documents_repo=mock_case_documents_repo,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
        application_writer=mock_application_writer,
        application_renderer=mock_application_renderer,
    )

    with pytest.raises(CaseNotFound):
        await use_case.execute(user_id, case_id, new_application)

    mock_applications_storage.upload_application.assert_not_awaited()


async def test_list_applications_success(
    mock_session_maker, mock_opened_session, mock_applications_repo, uuid_generator
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    application = ApplicationRepresentation(
        id=next(uuid_generator),
        caseId=case_id,
        createDate=datetime(2026, 1, 1, 10, 0, 0),
        applicationType=ApplicationType.OTHER,
    )
    mock_applications_repo.list_by_case_id.return_value = [application]

    use_case = ListApplications(session_maker=mock_session_maker, applications_repo=mock_applications_repo)
    result = await use_case.execute(user_id, case_id)

    assert result == [application]
    mock_applications_repo.list_by_case_id.assert_awaited_once_with(mock_opened_session, user_id, case_id)


async def test_get_application_download_url_success(
    mock_session_maker, mock_opened_session, mock_applications_repo, mock_applications_storage, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.get.return_value = ApplicationRepresentation(
        id=application_id,
        caseId=next(uuid_generator),
        createDate=datetime(2026, 1, 1, 10, 0, 0),
        applicationType=ApplicationType.OTHER,
    )
    mock_applications_storage.get_download_url.return_value = "http://storage.local/bucket/application"

    use_case = GetApplicationDownloadUrl(
        session_maker=mock_session_maker,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
    )
    result = await use_case.execute(user_id, application_id)

    assert result == "http://storage.local/bucket/application"
    mock_applications_repo.get.assert_awaited_once_with(mock_opened_session, user_id, application_id)
    mock_applications_storage.get_download_url.assert_awaited_once_with(application_id)


async def test_get_application_download_url_not_found(
    mock_session_maker, mock_applications_repo, mock_applications_storage, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.get.return_value = None

    use_case = GetApplicationDownloadUrl(
        session_maker=mock_session_maker,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
    )

    with pytest.raises(ApplicationNotFound):
        await use_case.execute(user_id, application_id)

    mock_applications_storage.get_download_url.assert_not_awaited()


async def test_delete_application_success(
    mock_session_maker, mock_opened_session, mock_applications_repo, mock_applications_storage, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)

    use_case = DeleteApplication(
        session_maker=mock_session_maker,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
    )
    await use_case.execute(user_id, application_id)

    mock_applications_repo.delete.assert_awaited_once_with(mock_opened_session, user_id, application_id)
    mock_applications_storage.delete_application.assert_awaited_once_with(application_id)


async def test_delete_application_storage_failure_ignored(
    mock_session_maker, mock_applications_repo, mock_applications_storage, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_storage.delete_application.side_effect = Exception()

    use_case = DeleteApplication(
        session_maker=mock_session_maker,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
    )
    await use_case.execute(user_id, application_id)

    mock_applications_storage.delete_application.assert_awaited_once_with(application_id)


async def test_delete_application_not_found(
    mock_session_maker, mock_applications_repo, mock_applications_storage, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.delete.side_effect = ApplicationNotFound()

    use_case = DeleteApplication(
        session_maker=mock_session_maker,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
    )

    with pytest.raises(ApplicationNotFound):
        await use_case.execute(user_id, application_id)

    mock_applications_storage.delete_application.assert_not_awaited()
