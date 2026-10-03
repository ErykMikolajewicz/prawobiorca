import pytest

from src.app.dtos.cases import CaseData, CaseDocument, NewCaseDocument
from src.app.use_cases.cases import (
    AddCase,
    AddCaseDocument,
    DeleteCase,
    DeleteCaseDocument,
    ListCaseDocuments,
    ListCases,
)
from src.domain.exceptions.cases import CaseNotFound


async def test_list_cases_success(mock_session_maker, mock_opened_session, mock_cases_repo, uuid_generator):
    user_id = next(uuid_generator)
    case_1 = CaseData(id=next(uuid_generator), name="Case 1")
    mock_cases_repo.list_by_user_id.return_value = [case_1]

    use_case = ListCases(session_maker=mock_session_maker, cases_repo=mock_cases_repo)
    result = await use_case.execute(user_id)

    assert result == [case_1]
    mock_cases_repo.list_by_user_id.assert_awaited_once_with(mock_opened_session, user_id)


async def test_delete_case_success(
    mock_session_maker,
    mock_opened_session,
    mock_cases_repo,
    mock_applications_repo,
    mock_applications_storage,
    uuid_generator,
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.list_ids_by_case_id.return_value = [application_id]

    use_case = DeleteCase(
        session_maker=mock_session_maker,
        cases_repo=mock_cases_repo,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
    )
    await use_case.execute(user_id, case_id)

    mock_applications_repo.list_ids_by_case_id.assert_awaited_once_with(mock_opened_session, user_id, case_id)
    mock_cases_repo.delete.assert_awaited_once_with(mock_opened_session, user_id, case_id)
    mock_applications_storage.delete_application.assert_awaited_once_with(application_id)


async def test_delete_case_storage_failure_ignored(
    mock_session_maker,
    mock_opened_session,
    mock_cases_repo,
    mock_applications_repo,
    mock_applications_storage,
    uuid_generator,
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    first_application_id = next(uuid_generator)
    second_application_id = next(uuid_generator)
    mock_applications_repo.list_ids_by_case_id.return_value = [first_application_id, second_application_id]
    mock_applications_storage.delete_application.side_effect = Exception()

    use_case = DeleteCase(
        session_maker=mock_session_maker,
        cases_repo=mock_cases_repo,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
    )
    await use_case.execute(user_id, case_id)

    assert mock_applications_storage.delete_application.await_count == 2


async def test_delete_case_not_found(
    mock_session_maker,
    mock_opened_session,
    mock_cases_repo,
    mock_applications_repo,
    mock_applications_storage,
    uuid_generator,
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    mock_applications_repo.list_ids_by_case_id.return_value = []
    mock_cases_repo.delete.side_effect = CaseNotFound()

    use_case = DeleteCase(
        session_maker=mock_session_maker,
        cases_repo=mock_cases_repo,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
    )

    with pytest.raises(CaseNotFound):
        await use_case.execute(user_id, case_id)

    mock_cases_repo.delete.assert_awaited_once_with(mock_opened_session, user_id, case_id)
    mock_applications_storage.delete_application.assert_not_awaited()


async def test_add_case_success(mock_session_maker, mock_opened_session, mock_cases_repo, uuid_generator):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    case_name = "New Case"
    mock_cases_repo.add.return_value = case_id

    use_case = AddCase(session_maker=mock_session_maker, cases_repo=mock_cases_repo)
    result = await use_case.execute(user_id, case_name)

    assert result == case_id
    mock_cases_repo.add.assert_awaited_once_with(mock_opened_session, user_id, case_name)


async def test_add_case_document_success(
    mock_session_maker, mock_opened_session, mock_case_documents_repo, uuid_generator
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    new_doc = NewCaseDocument(presentationName="doc.pdf", content="text")

    use_case = AddCaseDocument(session_maker=mock_session_maker, case_documents_repo=mock_case_documents_repo)
    await use_case.execute(user_id, case_id, new_doc)

    mock_case_documents_repo.add.assert_awaited_once_with(mock_opened_session, user_id, case_id, new_doc)


async def test_add_case_document_case_not_found(
    mock_session_maker, mock_opened_session, mock_case_documents_repo, uuid_generator
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    new_doc = NewCaseDocument(presentationName="doc.pdf", content="text")
    mock_case_documents_repo.add.side_effect = CaseNotFound()

    use_case = AddCaseDocument(session_maker=mock_session_maker, case_documents_repo=mock_case_documents_repo)

    with pytest.raises(CaseNotFound):
        await use_case.execute(user_id, case_id, new_doc)

    mock_case_documents_repo.add.assert_awaited_once_with(mock_opened_session, user_id, case_id, new_doc)


async def test_delete_case_document_success(
    mock_session_maker, mock_opened_session, mock_case_documents_repo, uuid_generator
):
    user_id = next(uuid_generator)
    document_id = next(uuid_generator)

    use_case = DeleteCaseDocument(session_maker=mock_session_maker, case_documents_repo=mock_case_documents_repo)
    await use_case.execute(user_id, document_id)

    mock_case_documents_repo.delete.assert_awaited_once_with(mock_opened_session, user_id, document_id)


async def test_list_case_documents_success(
    mock_session_maker, mock_opened_session, mock_case_documents_repo, uuid_generator
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    doc_1 = CaseDocument(id=next(uuid_generator), caseId=case_id, presentationName="doc.pdf", content="text")
    mock_case_documents_repo.list_by_case_id.return_value = [doc_1]

    use_case = ListCaseDocuments(session_maker=mock_session_maker, case_documents_repo=mock_case_documents_repo)
    result = await use_case.execute(user_id, case_id)

    assert result == [doc_1]
    mock_case_documents_repo.list_by_case_id.assert_awaited_once_with(mock_opened_session, user_id, case_id)
