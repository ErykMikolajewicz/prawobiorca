from datetime import UTC, datetime
from uuid import UUID

import pytest

from core_service.application.dtos.application_templates import (
    ApplicationTemplateDetailsData,
    ApplicationTemplateRepresentation,
    PublishedApplicationField,
    PublishedApplicationTemplate,
)
from core_service.application.use_cases.application_templates import (
    ConfirmApplicationTemplateUpload,
    DeleteApplicationTemplate,
    FailApplicationTemplateDescriptionGeneration,
    GenerateApplicationTemplateDescription,
    GetApplicationTemplateDownloadUrl,
    PublishApplicationTemplate,
    RegenerateApplicationTemplateDescription,
    SearchPublishedApplicationTemplates,
    UnpublishApplicationTemplate,
    UpdateApplicationTemplate,
)
from core_service.domain.exceptions.application_templates import (
    ApplicationTemplateContentNotFound,
    ApplicationTemplateDescriptionGenerationInProgress,
    ApplicationTemplateInInvalidState,
    ApplicationTemplateNotFound,
)
from core_service.domain.services.application_fields import create_default_fields
from core_service.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateDescriptionStatus,
    ApplicationTemplateDetails,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from core_service.domain.value_objects.users import Caller
from core_service.shared.consts import MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES
from core_service.shared.exceptions import ServiceUnavailable
from tests.consts import ADMIN_ID, ORGANIZATION_ID, SUBORGANIZATION_ID, USER_ID
from tests.mocks import get_awaited_argument, get_awaited_arguments

ADMIN = Caller(user_id=ADMIN_ID, is_admin=True)
USER = Caller(user_id=USER_ID)

TEMPLATE_ID = UUID("7d2e3f4a-5b6c-4d7e-8f9a-0b1c2d3e4f5a")

STUDENT_ID_FIELD = ApplicationTemplateField(name="student_id", label="Numer albumu")

TEMPLATE_TEXT = "Dziekan Wydziału\n{{ student_id }}"

PUBLISHED_TEMPLATE = PublishedApplicationTemplate(
    id=TEMPLATE_ID,
    name="Wniosek o urlop",
    description="Wniosek o urlop dziekański.",
    fields=[
        PublishedApplicationField(
            name="student_id", label="Numer albumu", field_type=ApplicationFieldType.TEXT, required=True
        )
    ],
)


def create_template(
    status: ApplicationTemplateStatus = ApplicationTemplateStatus.DRAFT,
    instructions: str | None = "Sporządź wniosek o urlop dziekański.",
    description: str | None = None,
    description_status: ApplicationTemplateDescriptionStatus = ApplicationTemplateDescriptionStatus.NOT_REQUESTED,
) -> ApplicationTemplateRepresentation:
    return ApplicationTemplateRepresentation(
        id=TEMPLATE_ID,
        createDate=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
        name="Wniosek o urlop",
        status=status,
        fields=[STUDENT_ID_FIELD],
        instructions=instructions,
        description=description,
        descriptionStatus=description_status,
    )


def create_published_template() -> ApplicationTemplateRepresentation:
    return create_template(ApplicationTemplateStatus.PUBLISHED, description="Wniosek o urlop dziekański.")


def store_template(application_templates_repository, template: ApplicationTemplateRepresentation | None) -> None:
    application_templates_repository.get.return_value = template


def get_description_statuses(application_templates_repository) -> list[ApplicationTemplateDescriptionStatus]:
    return get_awaited_arguments(application_templates_repository.set_description_status, "status")


@pytest.fixture
def application_templates_repository(mock_application_templates_repo):
    store_template(mock_application_templates_repo, create_template())
    return mock_application_templates_repo


@pytest.fixture
def template_inspector(mock_application_template_inspector):
    mock_application_template_inspector.get_text.return_value = TEMPLATE_TEXT
    return mock_application_template_inspector


@pytest.fixture
def search_published_templates(mock_session_maker, mock_texts_embedder, application_templates_repository):
    return SearchPublishedApplicationTemplates(
        session_maker=mock_session_maker,
        embedding_port=mock_texts_embedder,
        application_templates_repo=application_templates_repository,
    )


@pytest.fixture
def confirm_template_upload(
    mock_session_maker,
    application_templates_repository,
    mock_application_templates_storage,
    mock_application_template_inspector,
):
    return ConfirmApplicationTemplateUpload(
        session_maker=mock_session_maker,
        application_templates_repo=application_templates_repository,
        application_templates_storage=mock_application_templates_storage,
        application_template_inspector=mock_application_template_inspector,
    )


@pytest.fixture
def update_template(mock_session_maker, application_templates_repository, mock_texts_embedder):
    return UpdateApplicationTemplate(
        session_maker=mock_session_maker,
        application_templates_repo=application_templates_repository,
        texts_embedder=mock_texts_embedder,
    )


@pytest.fixture
def publish_template(mock_session_maker, application_templates_repository):
    return PublishApplicationTemplate(
        session_maker=mock_session_maker, application_templates_repo=application_templates_repository
    )


@pytest.fixture
def unpublish_template(mock_session_maker, application_templates_repository):
    return UnpublishApplicationTemplate(
        session_maker=mock_session_maker, application_templates_repo=application_templates_repository
    )


@pytest.fixture
def regenerate_template_description(
    mock_session_maker, application_templates_repository, mock_application_template_description_generation_scheduler
):
    return RegenerateApplicationTemplateDescription(
        session_maker=mock_session_maker,
        application_templates_repo=application_templates_repository,
        description_generation_scheduler=mock_application_template_description_generation_scheduler,
    )


@pytest.fixture
def generate_template_description(
    mock_session_maker,
    application_templates_repository,
    mock_application_templates_storage,
    template_inspector,
    mock_application_template_description_writer,
    mock_texts_embedder,
):
    return GenerateApplicationTemplateDescription(
        session_maker=mock_session_maker,
        application_templates_repo=application_templates_repository,
        application_templates_storage=mock_application_templates_storage,
        application_template_inspector=template_inspector,
        description_writer=mock_application_template_description_writer,
        texts_embedder=mock_texts_embedder,
    )


@pytest.fixture
def fail_template_description_generation(mock_session_maker, application_templates_repository):
    return FailApplicationTemplateDescriptionGeneration(
        session_maker=mock_session_maker, application_templates_repo=application_templates_repository
    )


@pytest.fixture
def delete_template(mock_session_maker, application_templates_repository, mock_application_templates_storage):
    return DeleteApplicationTemplate(
        session_maker=mock_session_maker,
        application_templates_repo=application_templates_repository,
        application_templates_storage=mock_application_templates_storage,
    )


@pytest.fixture
def get_template_download_url(mock_session_maker, application_templates_repository, mock_application_templates_storage):
    return GetApplicationTemplateDownloadUrl(
        session_maker=mock_session_maker,
        application_templates_repo=application_templates_repository,
        application_templates_storage=mock_application_templates_storage,
    )


@pytest.mark.parametrize(
    ("query", "ai_assisted"),
    [(" urlop dziekański ", False), ("urlop", True)],
    ids=("ai not requested", "not semantic query"),
)
async def test_search_published_application_templates_by_name(
    search_published_templates, application_templates_repository, mock_texts_embedder, query, ai_assisted
):
    application_templates_repository.fuzzy_search_templates.return_value = [create_published_template()]

    results = await search_published_templates.execute(USER, None, query, ai_assisted)

    assert results == [PUBLISHED_TEMPLATE]
    assert get_awaited_argument(application_templates_repository.fuzzy_search_templates, "query") == query.strip()
    mock_texts_embedder.embed_queries.assert_not_awaited()


async def test_search_published_application_templates_ai_assisted(
    search_published_templates, application_templates_repository, mock_texts_embedder
):
    mock_texts_embedder.embed_queries.return_value = [[0.1, 0.2]]
    application_templates_repository.hybrid_search_templates.return_value = [create_published_template()]

    results = await search_published_templates.execute(USER, None, " urlop dziekański ", True)

    assert results == [PUBLISHED_TEMPLATE]
    mock_texts_embedder.embed_queries.assert_awaited_once_with(["urlop dziekański"])
    hybrid_search_templates = application_templates_repository.hybrid_search_templates
    assert get_awaited_argument(hybrid_search_templates, "query") == "urlop dziekański"
    assert get_awaited_argument(hybrid_search_templates, "vector") == [0.1, 0.2]


async def test_confirm_application_template_upload_creates_fields(
    confirm_template_upload,
    application_templates_repository,
    mock_application_templates_storage,
    mock_application_template_inspector,
):
    store_template(application_templates_repository, create_template(ApplicationTemplateStatus.NOT_UPLOADED))
    mock_application_templates_storage.get_template.return_value = b"docx"
    variables = {"paragraphs", "student_id"}
    mock_application_template_inspector.get_variables.return_value = variables

    result = await confirm_template_upload.execute(ADMIN, TEMPLATE_ID)

    mock_application_template_inspector.get_variables.assert_awaited_once_with(b"docx")
    confirm_upload = application_templates_repository.confirm_upload
    assert get_awaited_argument(confirm_upload, "fields") == create_default_fields(variables)
    assert result == application_templates_repository.confirm_upload.return_value


@pytest.mark.parametrize(
    ("template", "error"),
    [
        (None, ApplicationTemplateNotFound),
        (create_template(ApplicationTemplateStatus.DRAFT), ApplicationTemplateInInvalidState),
    ],
    ids=("not found", "already confirmed"),
)
async def test_confirm_application_template_upload_rejected(
    confirm_template_upload, application_templates_repository, mock_application_templates_storage, template, error
):
    store_template(application_templates_repository, template)

    with pytest.raises(error):
        await confirm_template_upload.execute(ADMIN, TEMPLATE_ID)

    mock_application_templates_storage.get_template.assert_not_awaited()


async def test_confirm_application_template_upload_changed_during_confirmation(
    confirm_template_upload, application_templates_repository, mock_application_template_inspector
):
    store_template(application_templates_repository, create_template(ApplicationTemplateStatus.NOT_UPLOADED))
    mock_application_template_inspector.get_variables.return_value = {"paragraphs"}
    application_templates_repository.confirm_upload.return_value = None

    with pytest.raises(ApplicationTemplateInInvalidState):
        await confirm_template_upload.execute(ADMIN, TEMPLATE_ID)


async def test_update_application_template_saves_details(update_template, application_templates_repository):
    fields = [ApplicationTemplateField(name="student_id", label="Numer albumu", pattern=r"\d{6}")]
    details_data = ApplicationTemplateDetailsData(
        name="Wniosek",
        instructions="Instrukcje",
        fields=fields,
        organizationId=ORGANIZATION_ID,
        suborganizationId=SUBORGANIZATION_ID,
    )

    result = await update_template.execute(ADMIN, TEMPLATE_ID, details_data)

    update_details = application_templates_repository.update_details
    assert get_awaited_argument(update_details, "details") == ApplicationTemplateDetails(
        name="Wniosek",
        instructions="Instrukcje",
        fields=fields,
        organization_id=ORGANIZATION_ID,
        suborganization_id=SUBORGANIZATION_ID,
    )
    assert result == update_details.return_value


@pytest.mark.parametrize(
    ("description", "expected_vectors"),
    [("Nowy opis.", [[0.1, 0.2]]), ("Opis.", []), (None, [None]), ("", [None]), ("   ", [None])],
    ids=("changed", "unchanged", "removed", "empty", "blank"),
)
async def test_update_application_template_description_vector(
    update_template, application_templates_repository, mock_texts_embedder, description, expected_vectors
):
    store_template(application_templates_repository, create_template(description="Opis."))
    mock_texts_embedder.embed_texts.return_value = [[0.1, 0.2]]
    details_data = ApplicationTemplateDetailsData(name="Wniosek", fields=[STUDENT_ID_FIELD], description=description)

    await update_template.execute(ADMIN, TEMPLATE_ID, details_data)

    vectors = get_awaited_arguments(application_templates_repository.set_description_vector, "vector")
    assert vectors == expected_vectors


async def test_update_application_template_not_saved_when_embedding_unavailable(
    update_template, application_templates_repository, mock_texts_embedder
):
    mock_texts_embedder.embed_texts.side_effect = ServiceUnavailable
    details_data = ApplicationTemplateDetailsData(name="Wniosek", fields=[STUDENT_ID_FIELD], description="Opis.")

    with pytest.raises(ServiceUnavailable):
        await update_template.execute(ADMIN, TEMPLATE_ID, details_data)

    application_templates_repository.update_details.assert_not_awaited()


@pytest.mark.parametrize(
    ("template", "error"),
    [
        (None, ApplicationTemplateNotFound),
        (create_template(ApplicationTemplateStatus.NOT_UPLOADED), ApplicationTemplateInInvalidState),
        (create_template(ApplicationTemplateStatus.PUBLISHED), ApplicationTemplateInInvalidState),
    ],
    ids=("not found", "not uploaded", "published"),
)
async def test_update_application_template_rejected(update_template, application_templates_repository, template, error):
    store_template(application_templates_repository, template)

    with pytest.raises(error):
        await update_template.execute(ADMIN, TEMPLATE_ID, ApplicationTemplateDetailsData(name="Wniosek", fields=[]))

    application_templates_repository.update_details.assert_not_awaited()


async def test_update_application_template_published_during_embedding(
    update_template, application_templates_repository, mock_texts_embedder
):
    application_templates_repository.get.side_effect = [
        create_template(ApplicationTemplateStatus.DRAFT),
        create_template(ApplicationTemplateStatus.PUBLISHED),
    ]
    mock_texts_embedder.embed_texts.return_value = [[0.1, 0.2]]
    details_data = ApplicationTemplateDetailsData(name="Wniosek", fields=[STUDENT_ID_FIELD], description="Opis.")

    with pytest.raises(ApplicationTemplateInInvalidState):
        await update_template.execute(ADMIN, TEMPLATE_ID, details_data)

    application_templates_repository.update_details.assert_not_awaited()


async def test_publish_application_template(publish_template, application_templates_repository):
    await publish_template.execute(ADMIN, TEMPLATE_ID)

    set_status = application_templates_repository.set_status
    assert get_awaited_argument(set_status, "status") == ApplicationTemplateStatus.PUBLISHED


@pytest.mark.parametrize(
    ("template", "error"),
    [
        (None, ApplicationTemplateNotFound),
        (create_template(instructions=None), ApplicationTemplateInInvalidState),
    ],
    ids=("not found", "not ready"),
)
async def test_publish_application_template_rejected(
    publish_template, application_templates_repository, template, error
):
    store_template(application_templates_repository, template)

    with pytest.raises(error):
        await publish_template.execute(ADMIN, TEMPLATE_ID)

    application_templates_repository.set_status.assert_not_awaited()


async def test_unpublish_application_template(unpublish_template, application_templates_repository):
    store_template(application_templates_repository, create_template(ApplicationTemplateStatus.PUBLISHED))

    await unpublish_template.execute(ADMIN, TEMPLATE_ID)

    set_status = application_templates_repository.set_status
    assert get_awaited_argument(set_status, "status") == ApplicationTemplateStatus.DRAFT


@pytest.mark.parametrize(
    ("template", "error"),
    [
        (None, ApplicationTemplateNotFound),
        (create_template(ApplicationTemplateStatus.DRAFT), ApplicationTemplateInInvalidState),
    ],
    ids=("not found", "not published"),
)
async def test_unpublish_application_template_rejected(
    unpublish_template, application_templates_repository, template, error
):
    store_template(application_templates_repository, template)

    with pytest.raises(error):
        await unpublish_template.execute(ADMIN, TEMPLATE_ID)

    application_templates_repository.set_status.assert_not_awaited()


async def test_regenerate_application_template_description_schedules_generation(
    regenerate_template_description,
    application_templates_repository,
    mock_application_template_description_generation_scheduler,
):
    await regenerate_template_description.execute(ADMIN, TEMPLATE_ID)

    assert get_description_statuses(application_templates_repository) == [
        ApplicationTemplateDescriptionStatus.IN_PROGRESS
    ]
    scheduler = mock_application_template_description_generation_scheduler
    scheduler.schedule_application_template_description_generation.assert_awaited_once()


@pytest.mark.parametrize(
    ("template", "error"),
    [
        (None, ApplicationTemplateNotFound),
        (create_template(ApplicationTemplateStatus.PUBLISHED), ApplicationTemplateInInvalidState),
        (
            create_template(description_status=ApplicationTemplateDescriptionStatus.IN_PROGRESS),
            ApplicationTemplateDescriptionGenerationInProgress,
        ),
    ],
    ids=("not found", "not draft", "generation in progress"),
)
async def test_regenerate_application_template_description_rejected(
    regenerate_template_description,
    application_templates_repository,
    mock_application_template_description_generation_scheduler,
    template,
    error,
):
    store_template(application_templates_repository, template)

    with pytest.raises(error):
        await regenerate_template_description.execute(ADMIN, TEMPLATE_ID)

    assert get_description_statuses(application_templates_repository) == []
    scheduler = mock_application_template_description_generation_scheduler
    scheduler.schedule_application_template_description_generation.assert_not_awaited()


async def test_generate_application_template_description_saves_description_with_vector(
    generate_template_description,
    application_templates_repository,
    mock_application_template_description_writer,
    mock_texts_embedder,
):
    mock_application_template_description_writer.write.return_value = "Wniosek o urlop dziekański."
    mock_texts_embedder.embed_texts.return_value = [[0.1, 0.2]]

    await generate_template_description.execute(TEMPLATE_ID)

    description_source = get_awaited_argument(mock_application_template_description_writer.write, "description_source")
    assert description_source.name == "Wniosek o urlop"
    assert description_source.content == TEMPLATE_TEXT
    mock_texts_embedder.embed_texts.assert_awaited_once_with(["Wniosek o urlop dziekański."])
    set_generated_description = application_templates_repository.set_generated_description
    assert get_awaited_argument(set_generated_description, "description") == "Wniosek o urlop dziekański."
    assert get_awaited_argument(set_generated_description, "vector") == [0.1, 0.2]


@pytest.mark.parametrize(
    "template",
    [None, create_template(description_status=ApplicationTemplateDescriptionStatus.GENERATED)],
    ids=("not found", "already generated"),
)
async def test_generate_application_template_description_skipped(
    generate_template_description,
    application_templates_repository,
    mock_application_template_description_writer,
    template,
):
    store_template(application_templates_repository, template)

    await generate_template_description.execute(TEMPLATE_ID)

    mock_application_template_description_writer.write.assert_not_awaited()
    assert get_description_statuses(application_templates_repository) == []


async def test_generate_application_template_description_without_content_marks_failed(
    generate_template_description, application_templates_repository, mock_application_templates_storage
):
    mock_application_templates_storage.get_template.side_effect = ApplicationTemplateContentNotFound

    with pytest.raises(ApplicationTemplateContentNotFound):
        await generate_template_description.execute(TEMPLATE_ID)

    assert get_description_statuses(application_templates_repository) == [
        ApplicationTemplateDescriptionStatus.IN_PROGRESS,
        ApplicationTemplateDescriptionStatus.FAILED,
    ]


@pytest.mark.parametrize("error", [ServiceUnavailable, RuntimeError])
async def test_generate_application_template_description_failure_marks_failed(
    generate_template_description, application_templates_repository, mock_application_template_description_writer, error
):
    mock_application_template_description_writer.write.side_effect = error

    with pytest.raises(error):
        await generate_template_description.execute(TEMPLATE_ID)

    application_templates_repository.set_generated_description.assert_not_awaited()
    assert get_description_statuses(application_templates_repository) == [
        ApplicationTemplateDescriptionStatus.IN_PROGRESS,
        ApplicationTemplateDescriptionStatus.FAILED,
    ]


async def test_generate_application_template_description_of_removed_template(
    generate_template_description, application_templates_repository
):
    application_templates_repository.set_generated_description.side_effect = ApplicationTemplateNotFound

    await generate_template_description.execute(TEMPLATE_ID)

    assert get_description_statuses(application_templates_repository) == [
        ApplicationTemplateDescriptionStatus.IN_PROGRESS
    ]


async def test_generate_application_template_description_failure_of_removed_template(
    generate_template_description, application_templates_repository, mock_application_template_description_writer
):
    application_templates_repository.set_description_status.side_effect = [None, ApplicationTemplateNotFound()]
    mock_application_template_description_writer.write.side_effect = ServiceUnavailable

    with pytest.raises(ServiceUnavailable):
        await generate_template_description.execute(TEMPLATE_ID)


@pytest.mark.parametrize(
    ("delivery_attempt", "expected_failed", "expected_statuses"),
    [
        (MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES, False, []),
        (
            MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES + 1,
            True,
            [ApplicationTemplateDescriptionStatus.FAILED],
        ),
    ],
    ids=("within limit", "limit exceeded"),
)
async def test_fail_application_template_description_generation(
    fail_template_description_generation,
    application_templates_repository,
    delivery_attempt,
    expected_failed,
    expected_statuses,
):
    failed = await fail_template_description_generation.execute(TEMPLATE_ID, delivery_attempt)

    assert failed is expected_failed
    assert get_description_statuses(application_templates_repository) == expected_statuses


async def test_fail_application_template_description_generation_of_removed_template(
    fail_template_description_generation, application_templates_repository
):
    application_templates_repository.set_description_status.side_effect = ApplicationTemplateNotFound

    failed = await fail_template_description_generation.execute(
        TEMPLATE_ID, MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES + 1
    )

    assert failed is True


async def test_delete_application_template(
    delete_template, application_templates_repository, mock_application_templates_storage
):
    await delete_template.execute(ADMIN, TEMPLATE_ID)

    application_templates_repository.delete.assert_awaited_once()
    mock_application_templates_storage.delete_template.assert_awaited_once_with(TEMPLATE_ID)


async def test_delete_application_template_not_found(
    delete_template, application_templates_repository, mock_application_templates_storage
):
    application_templates_repository.delete.side_effect = ApplicationTemplateNotFound

    with pytest.raises(ApplicationTemplateNotFound):
        await delete_template.execute(ADMIN, TEMPLATE_ID)

    mock_application_templates_storage.delete_template.assert_not_awaited()


async def test_delete_application_template_ignores_storage_error(
    delete_template, application_templates_repository, mock_application_templates_storage
):
    mock_application_templates_storage.delete_template.side_effect = Exception("Storage error")

    await delete_template.execute(ADMIN, TEMPLATE_ID)

    application_templates_repository.delete.assert_awaited_once()


async def test_get_application_template_download_url(get_template_download_url, mock_application_templates_storage):
    mock_application_templates_storage.get_download_url.return_value = "http://storage.local/bucket/template"

    result = await get_template_download_url.execute(ADMIN, TEMPLATE_ID)

    assert result == "http://storage.local/bucket/template"
    mock_application_templates_storage.get_download_url.assert_awaited_once_with(TEMPLATE_ID)


@pytest.mark.parametrize(
    ("template", "error"),
    [
        (None, ApplicationTemplateNotFound),
        (create_template(ApplicationTemplateStatus.NOT_UPLOADED), ApplicationTemplateInInvalidState),
    ],
    ids=("not found", "not uploaded"),
)
async def test_get_application_template_download_url_rejected(
    get_template_download_url, application_templates_repository, mock_application_templates_storage, template, error
):
    store_template(application_templates_repository, template)

    with pytest.raises(error):
        await get_template_download_url.execute(ADMIN, TEMPLATE_ID)

    mock_application_templates_storage.get_download_url.assert_not_awaited()
