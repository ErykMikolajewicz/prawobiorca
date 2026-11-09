from datetime import UTC, datetime
from uuid import UUID

import pytest

from core_service.application.dtos.application_templates import ApplicationTemplateRepresentation
from core_service.application.dtos.applications import ApplicationRepresentation, NewApplication
from core_service.application.dtos.cases import CaseDocument
from core_service.application.use_cases.applications import (
    MAX_APPLICATION_GENERATION_DELIVERIES,
    AddApplication,
    DeleteApplication,
    FailApplicationGeneration,
    GenerateApplication,
    GetApplicationDownloadUrl,
)
from core_service.domain.exceptions.application_templates import ApplicationTemplateNotFound
from core_service.domain.exceptions.applications import ApplicationNotFound, ApplicationNotGenerated
from core_service.domain.value_objects.application_templates import ApplicationTemplateField, ApplicationTemplateStatus
from core_service.domain.value_objects.applications import ApplicationGenerationStatus
from core_service.domain.value_objects.users import Caller
from core_service.shared.exceptions import ServiceUnavailable
from tests.consts import USER_ID
from tests.mocks import get_awaited_argument, get_awaited_arguments

USER = Caller(user_id=USER_ID)

TEMPLATE_ID = UUID("00000000-0000-0000-0000-0000000000aa")
CASE_ID = UUID("4b5c6d7e-8f9a-4b0c-9d1e-2f3a4b5c6d7e")
OTHER_CASE_ID = UUID("9e8d7c6b-5a4f-4e3d-8c2b-1a0f9e8d7c6b")
APPLICATION_ID = UUID("2c3d4e5f-6a7b-4c8d-9e0f-1a2b3c4d5e6f")

NEW_APPLICATION = NewApplication(
    templateId=TEMPLATE_ID,
    description="Proszę o urlop dziekański.",
    fieldValues={"student_id": " 123456 "},
)


def create_template(
    status: ApplicationTemplateStatus = ApplicationTemplateStatus.PUBLISHED,
    fields: list[ApplicationTemplateField] | None = None,
) -> ApplicationTemplateRepresentation:
    return ApplicationTemplateRepresentation(
        id=TEMPLATE_ID,
        createDate=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
        name="Wniosek o urlop",
        status=status,
        fields=fields or [ApplicationTemplateField(name="student_id", label="Numer albumu", pattern=r"\d{6}")],
        instructions="Instrukcje",
    )


def create_application(
    generation_status: ApplicationGenerationStatus = ApplicationGenerationStatus.IN_PROGRESS,
    case_id: UUID = CASE_ID,
) -> ApplicationRepresentation:
    return ApplicationRepresentation(
        id=APPLICATION_ID,
        caseId=case_id,
        createDate=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
        templateName="Wniosek o urlop",
        generationStatus=generation_status,
        name=None,
    )


def get_generation_statuses(applications_repository) -> list[ApplicationGenerationStatus]:
    return get_awaited_arguments(applications_repository.set_generation_status, "status")


@pytest.fixture
def applications_repository(mock_applications_repo):
    mock_applications_repo.get.return_value = create_application()
    mock_applications_repo.add.return_value = APPLICATION_ID
    return mock_applications_repo


@pytest.fixture
def application_templates_repository(mock_application_templates_repo):
    mock_application_templates_repo.get.return_value = create_template()
    return mock_application_templates_repo


@pytest.fixture
def add_application(
    mock_session_maker, applications_repository, application_templates_repository, mock_application_generation_scheduler
):
    return AddApplication(
        session_maker=mock_session_maker,
        applications_repo=applications_repository,
        application_templates_repo=application_templates_repository,
        application_generation_scheduler=mock_application_generation_scheduler,
    )


@pytest.fixture
def generate_application(
    mock_session_maker,
    mock_case_documents_repo,
    applications_repository,
    mock_applications_storage,
    application_templates_repository,
    mock_application_templates_storage,
    mock_application_writer,
    mock_application_renderer,
):
    return GenerateApplication(
        session_maker=mock_session_maker,
        case_documents_repo=mock_case_documents_repo,
        applications_repo=applications_repository,
        applications_storage=mock_applications_storage,
        application_templates_repo=application_templates_repository,
        application_templates_storage=mock_application_templates_storage,
        application_writer=mock_application_writer,
        application_renderer=mock_application_renderer,
    )


@pytest.fixture
def fail_application_generation(mock_session_maker, applications_repository):
    return FailApplicationGeneration(session_maker=mock_session_maker, applications_repo=applications_repository)


@pytest.fixture
def get_application_download_url(mock_session_maker, applications_repository, mock_applications_storage):
    return GetApplicationDownloadUrl(
        session_maker=mock_session_maker,
        applications_repo=applications_repository,
        applications_storage=mock_applications_storage,
    )


@pytest.fixture
def delete_application(mock_session_maker, applications_repository, mock_applications_storage):
    return DeleteApplication(
        session_maker=mock_session_maker,
        applications_repo=applications_repository,
        applications_storage=mock_applications_storage,
    )


async def test_add_application_schedules_generation_with_normalized_field_values(
    add_application, applications_repository, mock_application_generation_scheduler
):
    application_id = await add_application.execute(USER, CASE_ID, NEW_APPLICATION)

    assert application_id == APPLICATION_ID
    assert get_awaited_argument(applications_repository.add, "template_name") == "Wniosek o urlop"
    scheduled_application = get_awaited_argument(
        mock_application_generation_scheduler.schedule_application_generation, "new_application"
    )
    assert scheduled_application == NewApplication(
        templateId=TEMPLATE_ID, description="Proszę o urlop dziekański.", fieldValues={"student_id": "123456"}
    )


@pytest.mark.parametrize(
    "template", [None, create_template(ApplicationTemplateStatus.DRAFT)], ids=("not found", "not published")
)
async def test_add_application_without_published_template(
    add_application,
    applications_repository,
    application_templates_repository,
    mock_application_generation_scheduler,
    template,
):
    application_templates_repository.get.return_value = template

    with pytest.raises(ApplicationTemplateNotFound):
        await add_application.execute(USER, CASE_ID, NEW_APPLICATION)

    applications_repository.add.assert_not_awaited()
    mock_application_generation_scheduler.schedule_application_generation.assert_not_awaited()


async def test_generate_application_saves_generated_document(
    generate_application,
    applications_repository,
    mock_case_documents_repo,
    mock_applications_storage,
    mock_application_templates_storage,
    mock_application_writer,
    mock_application_renderer,
):
    document = CaseDocument(
        id=UUID("5d6e7f8a-9b0c-4d1e-8f2a-3b4c5d6e7f8a"), caseId=CASE_ID, presentationName="doc.pdf", content="text"
    )
    mock_case_documents_repo.list_by_case_id.return_value = [document]
    mock_application_templates_storage.get_template.return_value = b"TEMPLATE"
    mock_application_writer.write.return_value = "Szanowny Panie Dziekanie"
    mock_application_writer.write_name.return_value = "Wniosek o urlop dziekański"
    mock_application_renderer.render.return_value = b"PK"

    await generate_application.execute(USER_ID, APPLICATION_ID, NEW_APPLICATION)

    mock_application_writer.write.assert_awaited_once_with(NEW_APPLICATION, create_template(), [document])
    mock_application_renderer.render.assert_awaited_once_with(b"TEMPLATE", NEW_APPLICATION, "Szanowny Panie Dziekanie")
    mock_applications_storage.upload_application.assert_awaited_once_with(APPLICATION_ID, b"PK")
    assert get_awaited_argument(applications_repository.set_name, "name") == "Wniosek o urlop dziekański"
    assert get_generation_statuses(applications_repository) == [
        ApplicationGenerationStatus.IN_PROGRESS,
        ApplicationGenerationStatus.GENERATED,
    ]


async def test_generate_application_not_found(generate_application, applications_repository, mock_application_writer):
    applications_repository.get.return_value = None

    with pytest.raises(ApplicationNotFound):
        await generate_application.execute(USER_ID, APPLICATION_ID, NEW_APPLICATION)

    mock_application_writer.write.assert_not_awaited()


async def test_generate_application_already_generated(
    generate_application, applications_repository, mock_application_writer
):
    applications_repository.get.return_value = create_application(ApplicationGenerationStatus.GENERATED)

    await generate_application.execute(USER_ID, APPLICATION_ID, NEW_APPLICATION)

    mock_application_writer.write.assert_not_awaited()
    assert get_generation_statuses(applications_repository) == []


@pytest.mark.parametrize(
    "template",
    [
        None,
        create_template(ApplicationTemplateStatus.DRAFT),
        create_template(fields=[ApplicationTemplateField(name="faculty", label="Wydział")]),
    ],
    ids=("removed", "unpublished", "fields changed"),
)
async def test_generate_application_with_changed_template_marks_failed(
    generate_application, applications_repository, application_templates_repository, mock_application_writer, template
):
    application_templates_repository.get.return_value = template

    await generate_application.execute(USER_ID, APPLICATION_ID, NEW_APPLICATION)

    mock_application_writer.write.assert_not_awaited()
    assert get_generation_statuses(applications_repository) == [ApplicationGenerationStatus.FAILED]


@pytest.mark.parametrize("error", [ServiceUnavailable, RuntimeError])
async def test_generate_application_failure_marks_failed(
    generate_application, applications_repository, mock_applications_storage, mock_application_writer, error
):
    mock_application_writer.write.side_effect = error

    with pytest.raises(error):
        await generate_application.execute(USER_ID, APPLICATION_ID, NEW_APPLICATION)

    mock_applications_storage.upload_application.assert_not_awaited()
    assert get_generation_statuses(applications_repository) == [
        ApplicationGenerationStatus.IN_PROGRESS,
        ApplicationGenerationStatus.FAILED,
    ]


async def test_generate_application_removed_during_generation(
    generate_application, applications_repository, mock_applications_storage
):
    applications_repository.set_name.side_effect = ApplicationNotFound

    await generate_application.execute(USER_ID, APPLICATION_ID, NEW_APPLICATION)

    mock_applications_storage.upload_application.assert_not_awaited()
    assert get_generation_statuses(applications_repository) == [ApplicationGenerationStatus.IN_PROGRESS]


async def test_generate_application_failure_of_removed_application(
    generate_application, applications_repository, mock_application_writer
):
    applications_repository.set_generation_status.side_effect = [None, ApplicationNotFound()]
    mock_application_writer.write.side_effect = ServiceUnavailable

    with pytest.raises(ServiceUnavailable):
        await generate_application.execute(USER_ID, APPLICATION_ID, NEW_APPLICATION)


async def test_generate_application_upload_failure_marks_failed(
    generate_application, applications_repository, mock_applications_storage
):
    mock_applications_storage.upload_application.side_effect = RuntimeError

    with pytest.raises(RuntimeError):
        await generate_application.execute(USER_ID, APPLICATION_ID, NEW_APPLICATION)

    assert get_generation_statuses(applications_repository)[-1] == ApplicationGenerationStatus.FAILED


@pytest.mark.parametrize(
    ("delivery_attempt", "expected_failed", "expected_statuses"),
    [
        (MAX_APPLICATION_GENERATION_DELIVERIES, False, []),
        (MAX_APPLICATION_GENERATION_DELIVERIES + 1, True, [ApplicationGenerationStatus.FAILED]),
    ],
    ids=("within limit", "limit exceeded"),
)
async def test_fail_application_generation(
    fail_application_generation, applications_repository, delivery_attempt, expected_failed, expected_statuses
):
    failed = await fail_application_generation.execute(USER_ID, APPLICATION_ID, delivery_attempt)

    assert failed is expected_failed
    assert get_generation_statuses(applications_repository) == expected_statuses


async def test_fail_application_generation_of_removed_application(fail_application_generation, applications_repository):
    applications_repository.set_generation_status.side_effect = ApplicationNotFound

    failed = await fail_application_generation.execute(
        USER_ID, APPLICATION_ID, MAX_APPLICATION_GENERATION_DELIVERIES + 1
    )

    assert failed is True


async def test_get_application_download_url(
    get_application_download_url, applications_repository, mock_applications_storage
):
    applications_repository.get.return_value = create_application(ApplicationGenerationStatus.GENERATED)
    mock_applications_storage.get_download_url.return_value = "http://storage.local/bucket/application"

    result = await get_application_download_url.execute(USER, CASE_ID, APPLICATION_ID)

    assert result == "http://storage.local/bucket/application"
    mock_applications_storage.get_download_url.assert_awaited_once_with(APPLICATION_ID)


@pytest.mark.parametrize(
    ("application", "error"),
    [
        (None, ApplicationNotFound),
        (create_application(ApplicationGenerationStatus.GENERATED, OTHER_CASE_ID), ApplicationNotFound),
        (create_application(ApplicationGenerationStatus.IN_PROGRESS), ApplicationNotGenerated),
    ],
    ids=("not found", "other case", "not generated"),
)
async def test_get_application_download_url_rejected(
    get_application_download_url, applications_repository, mock_applications_storage, application, error
):
    applications_repository.get.return_value = application

    with pytest.raises(error):
        await get_application_download_url.execute(USER, CASE_ID, APPLICATION_ID)

    mock_applications_storage.get_download_url.assert_not_awaited()


async def test_delete_application(delete_application, applications_repository, mock_applications_storage):
    await delete_application.execute(USER, CASE_ID, APPLICATION_ID)

    applications_repository.delete.assert_awaited_once()
    mock_applications_storage.delete_application.assert_awaited_once_with(APPLICATION_ID)


async def test_delete_application_not_found(delete_application, applications_repository, mock_applications_storage):
    applications_repository.delete.side_effect = ApplicationNotFound

    with pytest.raises(ApplicationNotFound):
        await delete_application.execute(USER, CASE_ID, APPLICATION_ID)

    mock_applications_storage.delete_application.assert_not_awaited()


async def test_delete_application_ignores_storage_error(
    delete_application, applications_repository, mock_applications_storage
):
    mock_applications_storage.delete_application.side_effect = Exception("Storage error")

    await delete_application.execute(USER, CASE_ID, APPLICATION_ID)

    applications_repository.delete.assert_awaited_once()
