from src.app.dtos.applications import NewApplication
from src.app.dtos.cases import CaseDocument
from src.app.use_cases.applications import GenerateApplication


async def test_generate_application_success(
    mock_session_maker,
    mock_opened_session,
    mock_case_documents_repo,
    mock_application_writer,
    mock_application_renderer,
    uuid_generator,
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    new_application = NewApplication(
        description="Proszę o urlop dziekański.",
        userName="Jan Kowalski",
        studentId="123456",
        department="Wydział Informatyki i Telekomunikacji",
        semester="4",
        title="inż.",
    )
    document = CaseDocument(id=next(uuid_generator), caseId=case_id, presentationName="doc.pdf", content="text")
    mock_case_documents_repo.list_by_case_id.return_value = [document]
    mock_application_writer.write.return_value = "Szanowny Panie Dziekanie"
    mock_application_renderer.render.return_value = b"PK"

    use_case = GenerateApplication(
        session_maker=mock_session_maker,
        case_documents_repo=mock_case_documents_repo,
        application_writer=mock_application_writer,
        application_renderer=mock_application_renderer,
    )
    result = await use_case.execute(user_id, case_id, new_application)

    assert result == b"PK"
    mock_case_documents_repo.list_by_case_id.assert_awaited_once_with(mock_opened_session, user_id, case_id)
    mock_application_writer.write.assert_awaited_once_with(new_application, [document])
    mock_application_renderer.render.assert_awaited_once_with(new_application, "Szanowny Panie Dziekanie")
