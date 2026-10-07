from datetime import datetime
from uuid import UUID

import pytest

from src.app.dtos.application_templates import ApplicationTemplateRepresentation
from src.app.dtos.applications import ApplicationRepresentation, NewApplication
from src.app.dtos.cases import CaseDocument
from src.app.use_cases.applications import (
    AddApplication,
    DeleteApplication,
    FailApplicationGeneration,
    GenerateApplication,
    GetApplicationDownloadUrl,
    ListApplications,
)
from src.domain.exceptions.application_templates import ApplicationTemplateNotFound, InvalidApplicationFieldValues
from src.domain.exceptions.applications import ApplicationNotFound, ApplicationNotGenerated
from src.domain.exceptions.cases import CaseNotFound
from src.domain.value_objects.application_templates import ApplicationTemplateField, ApplicationTemplateStatus
from src.domain.value_objects.applications import ApplicationGenerationStatus
from src.shared.consts import MAX_APPLICATION_GENERATION_DELIVERIES
from src.shared.exceptions import ServiceUnavailable

TEMPLATE_ID = UUID("00000000-0000-0000-0000-0000000000aa")


@pytest.fixture
def new_application():
    return NewApplication(
        templateId=TEMPLATE_ID,
        description="Proszę o urlop dziekański.",
        fieldValues={"student_id": " 123456 "},
    )


@pytest.fixture
def add_application(
    mock_session_maker, mock_applications_repo, mock_application_templates_repo, mock_application_generation_scheduler
):
    return AddApplication(
        session_maker=mock_session_maker,
        applications_repo=mock_applications_repo,
        application_templates_repo=mock_application_templates_repo,
        application_generation_scheduler=mock_application_generation_scheduler,
    )


@pytest.fixture
def generate_application(
    mock_session_maker,
    mock_case_documents_repo,
    mock_applications_repo,
    mock_applications_storage,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_application_writer,
    mock_application_renderer,
):
    return GenerateApplication(
        session_maker=mock_session_maker,
        case_documents_repo=mock_case_documents_repo,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
        application_templates_repo=mock_application_templates_repo,
        application_templates_storage=mock_application_templates_storage,
        application_writer=mock_application_writer,
        application_renderer=mock_application_renderer,
    )


def create_template(status: ApplicationTemplateStatus = ApplicationTemplateStatus.PUBLISHED):
    return ApplicationTemplateRepresentation(
        id=TEMPLATE_ID,
        createDate=datetime(2026, 1, 1, 10, 0, 0),
        name="Wniosek o urlop",
        status=status,
        fields=[ApplicationTemplateField(name="student_id", label="Numer albumu", pattern=r"\d{6}")],
        instructions="Instrukcje",
    )


def create_application(application_id, case_id, generation_status):
    return ApplicationRepresentation(
        id=application_id,
        caseId=case_id,
        createDate=datetime(2026, 1, 1, 10, 0, 0),
        templateName="Wniosek o urlop",
        generationStatus=generation_status,
        name=None,
    )


async def test_add_application_success(
    add_application,
    mock_opened_session,
    mock_applications_repo,
    mock_application_templates_repo,
    mock_application_generation_scheduler,
    new_application,
    uuid_generator,
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template()
    mock_applications_repo.add.return_value = application_id

    result = await add_application.execute(user_id, case_id, new_application)

    assert result == application_id
    mock_application_templates_repo.get.assert_awaited_once_with(mock_opened_session, TEMPLATE_ID)
    mock_applications_repo.add.assert_awaited_once_with(
        mock_opened_session, user_id, case_id, TEMPLATE_ID, "Wniosek o urlop"
    )
    mock_application_generation_scheduler.schedule_application_generation.assert_awaited_once_with(
        mock_opened_session,
        user_id,
        application_id,
        NewApplication(
            templateId=TEMPLATE_ID, description="Proszę o urlop dziekański.", fieldValues={"student_id": "123456"}
        ),
    )


@pytest.mark.parametrize("template", [None, create_template(ApplicationTemplateStatus.DRAFT)])
async def test_add_application_template_not_found(
    add_application,
    mock_applications_repo,
    mock_application_templates_repo,
    mock_application_generation_scheduler,
    new_application,
    uuid_generator,
    template,
):
    mock_application_templates_repo.get.return_value = template

    with pytest.raises(ApplicationTemplateNotFound):
        await add_application.execute(next(uuid_generator), next(uuid_generator), new_application)

    mock_applications_repo.add.assert_not_awaited()
    mock_application_generation_scheduler.schedule_application_generation.assert_not_awaited()


async def test_add_application_invalid_field_values(
    add_application,
    mock_applications_repo,
    mock_application_templates_repo,
    mock_application_generation_scheduler,
    uuid_generator,
):
    mock_application_templates_repo.get.return_value = create_template()
    new_application = NewApplication(
        templateId=TEMPLATE_ID, description="Opis", fieldValues={"student_id": "abc", "unknown": "x"}
    )

    with pytest.raises(InvalidApplicationFieldValues):
        await add_application.execute(next(uuid_generator), next(uuid_generator), new_application)

    mock_applications_repo.add.assert_not_awaited()
    mock_application_generation_scheduler.schedule_application_generation.assert_not_awaited()


async def test_add_application_case_not_found(
    add_application,
    mock_applications_repo,
    mock_application_templates_repo,
    mock_application_generation_scheduler,
    new_application,
    uuid_generator,
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    mock_application_templates_repo.get.return_value = create_template()
    mock_applications_repo.add.side_effect = CaseNotFound()

    with pytest.raises(CaseNotFound):
        await add_application.execute(user_id, case_id, new_application)

    mock_application_generation_scheduler.schedule_application_generation.assert_not_awaited()


async def test_generate_application_success(
    generate_application,
    mock_opened_session,
    mock_case_documents_repo,
    mock_applications_repo,
    mock_applications_storage,
    mock_application_templates_repo,
    mock_application_templates_storage,
    mock_application_writer,
    mock_application_renderer,
    new_application,
    uuid_generator,
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    application_id = next(uuid_generator)
    template = create_template()
    document = CaseDocument(id=next(uuid_generator), caseId=case_id, presentationName="doc.pdf", content="text")
    mock_applications_repo.get.return_value = create_application(
        application_id, case_id, ApplicationGenerationStatus.IN_PROGRESS
    )
    mock_application_templates_repo.get.return_value = template
    mock_application_templates_storage.get_template.return_value = b"TEMPLATE"
    mock_case_documents_repo.list_by_case_id.return_value = [document]
    mock_application_writer.write.return_value = "Szanowny Panie Dziekanie"
    mock_application_writer.write_name.return_value = "Wniosek o urlop dziekański"
    mock_application_renderer.render.return_value = b"PK"

    await generate_application.execute(user_id, application_id, new_application)

    mock_application_templates_repo.get.assert_awaited_once_with(mock_opened_session, TEMPLATE_ID)
    mock_application_templates_storage.get_template.assert_awaited_once_with(TEMPLATE_ID)
    mock_case_documents_repo.list_by_case_id.assert_awaited_once_with(mock_opened_session, user_id, case_id)
    mock_application_writer.write.assert_awaited_once_with(new_application, template, [document])
    mock_application_writer.write_name.assert_awaited_once_with(new_application)
    mock_applications_repo.set_name.assert_awaited_once_with(
        mock_opened_session, user_id, application_id, "Wniosek o urlop dziekański"
    )
    mock_application_renderer.render.assert_awaited_once_with(b"TEMPLATE", new_application, "Szanowny Panie Dziekanie")
    mock_applications_storage.upload_application.assert_awaited_once_with(application_id, b"PK")
    assert mock_applications_repo.set_generation_status.await_args_list[-1].args == (
        mock_opened_session,
        user_id,
        application_id,
        ApplicationGenerationStatus.GENERATED,
    )


async def test_generate_application_not_found(
    generate_application, mock_applications_repo, mock_application_writer, new_application, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.get.return_value = None

    with pytest.raises(ApplicationNotFound):
        await generate_application.execute(user_id, application_id, new_application)

    mock_application_writer.write.assert_not_awaited()


async def test_generate_application_already_generated(
    generate_application, mock_applications_repo, mock_application_writer, new_application, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.get.return_value = create_application(
        application_id, next(uuid_generator), ApplicationGenerationStatus.GENERATED
    )

    await generate_application.execute(user_id, application_id, new_application)

    mock_application_writer.write.assert_not_awaited()
    mock_applications_repo.set_generation_status.assert_not_awaited()


async def test_generate_application_template_removed(
    generate_application,
    mock_opened_session,
    mock_applications_repo,
    mock_application_templates_repo,
    mock_application_writer,
    new_application,
    uuid_generator,
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.get.return_value = create_application(
        application_id, next(uuid_generator), ApplicationGenerationStatus.IN_PROGRESS
    )
    mock_application_templates_repo.get.return_value = None

    await generate_application.execute(user_id, application_id, new_application)

    mock_application_writer.write.assert_not_awaited()
    mock_applications_repo.set_generation_status.assert_awaited_once_with(
        mock_opened_session, user_id, application_id, ApplicationGenerationStatus.FAILED
    )


async def test_generate_application_service_unavailable(
    generate_application,
    mock_opened_session,
    mock_applications_repo,
    mock_applications_storage,
    mock_application_templates_repo,
    mock_application_writer,
    new_application,
    uuid_generator,
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.get.return_value = create_application(
        application_id, next(uuid_generator), ApplicationGenerationStatus.IN_PROGRESS
    )
    mock_application_templates_repo.get.return_value = create_template()
    mock_application_writer.write.side_effect = ServiceUnavailable()

    with pytest.raises(ServiceUnavailable):
        await generate_application.execute(user_id, application_id, new_application)

    mock_applications_storage.upload_application.assert_not_awaited()
    mock_applications_repo.set_generation_status.assert_awaited_with(
        mock_opened_session, user_id, application_id, ApplicationGenerationStatus.FAILED
    )


async def test_generate_application_removed_during_generation(
    generate_application,
    mock_applications_repo,
    mock_applications_storage,
    mock_application_templates_repo,
    mock_application_writer,
    mock_application_renderer,
    new_application,
    uuid_generator,
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.get.return_value = create_application(
        application_id, next(uuid_generator), ApplicationGenerationStatus.IN_PROGRESS
    )
    mock_application_templates_repo.get.return_value = create_template()
    mock_application_writer.write.return_value = "Szanowny Panie Dziekanie"
    mock_application_renderer.render.return_value = b"PK"
    mock_applications_repo.set_generation_status.side_effect = [None, ApplicationNotFound()]

    await generate_application.execute(user_id, application_id, new_application)

    mock_applications_storage.upload_application.assert_not_awaited()


async def test_generate_application_upload_failure(
    generate_application,
    mock_opened_session,
    mock_applications_repo,
    mock_applications_storage,
    mock_application_templates_repo,
    mock_application_writer,
    mock_application_renderer,
    new_application,
    uuid_generator,
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.get.return_value = create_application(
        application_id, next(uuid_generator), ApplicationGenerationStatus.IN_PROGRESS
    )
    mock_application_templates_repo.get.return_value = create_template()
    mock_application_writer.write.return_value = "Szanowny Panie Dziekanie"
    mock_application_renderer.render.return_value = b"PK"
    mock_applications_storage.upload_application.side_effect = RuntimeError()

    with pytest.raises(RuntimeError):
        await generate_application.execute(user_id, application_id, new_application)

    mock_applications_repo.set_generation_status.assert_awaited_with(
        mock_opened_session, user_id, application_id, ApplicationGenerationStatus.FAILED
    )


async def test_fail_application_generation_deliveries_limit_exceeded(
    mock_session_maker, mock_opened_session, mock_applications_repo, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)

    use_case = FailApplicationGeneration(session_maker=mock_session_maker, applications_repo=mock_applications_repo)

    failed = await use_case.execute(user_id, application_id, MAX_APPLICATION_GENERATION_DELIVERIES + 1)

    assert failed is True
    mock_applications_repo.set_generation_status.assert_awaited_once_with(
        mock_opened_session, user_id, application_id, ApplicationGenerationStatus.FAILED
    )


async def test_fail_application_generation_deliveries_limit_not_exceeded(
    mock_session_maker, mock_applications_repo, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)

    use_case = FailApplicationGeneration(session_maker=mock_session_maker, applications_repo=mock_applications_repo)

    failed = await use_case.execute(user_id, application_id, MAX_APPLICATION_GENERATION_DELIVERIES)

    assert failed is False
    mock_applications_repo.set_generation_status.assert_not_awaited()


async def test_list_applications_success(
    mock_session_maker, mock_opened_session, mock_applications_repo, uuid_generator
):
    user_id = next(uuid_generator)
    case_id = next(uuid_generator)
    application = create_application(next(uuid_generator), case_id, ApplicationGenerationStatus.GENERATED)
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
    mock_applications_repo.get.return_value = create_application(
        application_id, next(uuid_generator), ApplicationGenerationStatus.GENERATED
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


async def test_get_application_download_url_not_generated(
    mock_session_maker, mock_applications_repo, mock_applications_storage, uuid_generator
):
    user_id = next(uuid_generator)
    application_id = next(uuid_generator)
    mock_applications_repo.get.return_value = create_application(
        application_id, next(uuid_generator), ApplicationGenerationStatus.IN_PROGRESS
    )

    use_case = GetApplicationDownloadUrl(
        session_maker=mock_session_maker,
        applications_repo=mock_applications_repo,
        applications_storage=mock_applications_storage,
    )

    with pytest.raises(ApplicationNotGenerated):
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
