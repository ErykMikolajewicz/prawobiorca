from datetime import UTC, datetime
from uuid import UUID

import pytest

from src.app.dtos.regulations import RegulationData, RegulationRepresentation
from src.app.dtos.search import SearchParams
from src.app.use_cases.regulations import (
    AddRegulation,
    ConfirmRegulationUpload,
    DeleteRegulation,
    FailRegulationDescriptionGeneration,
    FailRegulationPreparation,
    GenerateRegulationDescription,
    PrepareRegulation,
    RegenerateRegulationDescription,
    RetryRegulationPreparation,
    SearchRegulation,
)
from src.domain.exceptions.documents import RegulationDocumentsNotFound
from src.domain.exceptions.regulations import (
    RegulationAlreadyInitialized,
    RegulationContentNotFound,
    RegulationDescriptionGenerationInProgress,
    RegulationInInvalidState,
    RegulationNotFound,
    RegulationPreparationInProgress,
    RegulationsNotPreparedToSearch,
)
from src.domain.value_objects.regulations import (
    RegulationDescriptionStatus,
    RegulationOwner,
    RegulationPreparationStatus,
    RegulationRegistrationData,
    RegulationScope,
    RegulationType,
)
from src.domain.value_objects.users import Caller
from src.shared.consts import (
    MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES,
    MAX_REGULATION_PREPARATION_DELIVERIES,
)
from src.shared.exceptions import ServiceUnavailable
from tests.consts import ADMIN_ID, ORGANIZATION_ID, SUBORGANIZATION_ID

ADMIN = Caller(user_id=ADMIN_ID, is_admin=True)

REGULATION_ID = UUID("5c1d2e3f-4a5b-4c6d-8e7f-9a0b1c2d3e4f")


def create_regulation(
    preparation_status: RegulationPreparationStatus = RegulationPreparationStatus.NOT_STARTED,
    description_status: RegulationDescriptionStatus = RegulationDescriptionStatus.NOT_REQUESTED,
) -> RegulationRepresentation:
    return RegulationRepresentation(
        id=REGULATION_ID,
        createDate=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
        presentationName="Regulamin studiów",
        preparationStatus=preparation_status,
        descriptionStatus=description_status,
    )


def store_regulation(regulations_repository, regulation: RegulationRepresentation | None) -> None:
    regulations_repository.get_regulation_representation.return_value = regulation


def get_preparation_statuses(regulations_repository) -> list[RegulationPreparationStatus]:
    return [call.args[-1] for call in regulations_repository.set_preparation_status.await_args_list]


def get_description_statuses(regulations_repository) -> list[RegulationDescriptionStatus]:
    return [call.args[-1] for call in regulations_repository.set_description_status.await_args_list]


@pytest.fixture
def regulations_repository(mock_regulations_repository):
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id=None)
    store_regulation(mock_regulations_repository, create_regulation())
    return mock_regulations_repository


@pytest.fixture
def sections_repository(mock_sections_repo):
    mock_sections_repo.list_sections_contents.return_value = []
    return mock_sections_repo


@pytest.fixture
def prepare_regulation(
    mock_session_maker,
    mock_regulations_storage,
    sections_repository,
    regulations_repository,
    mock_regulation_preparator,
    mock_regulation_description_generation_scheduler,
):
    return PrepareRegulation(
        session_maker=mock_session_maker,
        regulations_storage=mock_regulations_storage,
        sections_repository=sections_repository,
        regulations_repository=regulations_repository,
        regulation_preparator=mock_regulation_preparator,
        description_generation_scheduler=mock_regulation_description_generation_scheduler,
    )


@pytest.fixture
def fail_regulation_preparation(mock_session_maker, regulations_repository):
    return FailRegulationPreparation(session_maker=mock_session_maker, regulations_repository=regulations_repository)


@pytest.fixture
def retry_regulation_preparation(mock_session_maker, regulations_repository, mock_regulation_preparation_scheduler):
    return RetryRegulationPreparation(
        session_maker=mock_session_maker,
        regulations_repository=regulations_repository,
        regulation_preparation_scheduler=mock_regulation_preparation_scheduler,
    )


@pytest.fixture
def confirm_regulation_upload(
    mock_session_maker, regulations_repository, mock_regulations_storage, mock_regulation_preparation_scheduler
):
    return ConfirmRegulationUpload(
        session_maker=mock_session_maker,
        regulations_repository=regulations_repository,
        regulations_storage=mock_regulations_storage,
        regulation_preparation_scheduler=mock_regulation_preparation_scheduler,
    )


@pytest.fixture
def generate_regulation_description(
    mock_session_maker,
    regulations_repository,
    sections_repository,
    mock_regulation_description_writer,
    mock_embedding_port,
):
    return GenerateRegulationDescription(
        session_maker=mock_session_maker,
        regulations_repository=regulations_repository,
        sections_repository=sections_repository,
        description_writer=mock_regulation_description_writer,
        texts_embedder=mock_embedding_port,
    )


@pytest.fixture
def fail_regulation_description_generation(mock_session_maker, regulations_repository):
    return FailRegulationDescriptionGeneration(
        session_maker=mock_session_maker, regulations_repository=regulations_repository
    )


@pytest.fixture
def regenerate_regulation_description(
    mock_session_maker, regulations_repository, mock_regulation_description_generation_scheduler
):
    return RegenerateRegulationDescription(
        session_maker=mock_session_maker,
        regulations_repository=regulations_repository,
        description_generation_scheduler=mock_regulation_description_generation_scheduler,
    )


@pytest.fixture
def add_regulation(mock_session_maker, regulations_repository, mock_regulations_storage):
    return AddRegulation(
        session_maker=mock_session_maker,
        regulations_repository=regulations_repository,
        regulations_storage=mock_regulations_storage,
    )


@pytest.fixture
def delete_regulation(mock_session_maker, regulations_repository, sections_repository, mock_regulations_storage):
    return DeleteRegulation(
        session_maker=mock_session_maker,
        regulations_repository=regulations_repository,
        sections_repository=sections_repository,
        regulations_storage=mock_regulations_storage,
    )


@pytest.fixture
def search_regulation(mock_session_maker, mock_embedding_port, sections_repository, regulations_repository):
    return SearchRegulation(
        session_maker=mock_session_maker,
        embedding_port=mock_embedding_port,
        sections_repository=sections_repository,
        regulations_repository=regulations_repository,
    )


async def test_prepare_regulation_saves_sections(
    prepare_regulation,
    regulations_repository,
    sections_repository,
    mock_regulations_storage,
    mock_regulation_preparator,
):
    mock_regulations_storage.get_regulation.return_value = b"content"
    sections = mock_regulation_preparator.prepare_regulation.return_value

    await prepare_regulation.execute(None, REGULATION_ID)

    mock_regulation_preparator.prepare_regulation.assert_awaited_once_with(b"content")
    assert sections_repository.add_sections.await_args.args[-1] == sections
    assert get_preparation_statuses(regulations_repository) == [
        RegulationPreparationStatus.IN_PROGRESS,
        RegulationPreparationStatus.PREPARED,
    ]


@pytest.mark.parametrize(
    ("regulation", "error"),
    [
        (None, RegulationNotFound),
        (create_regulation(RegulationPreparationStatus.PREPARED), RegulationAlreadyInitialized),
    ],
    ids=("not found", "already prepared"),
)
async def test_prepare_regulation_rejected(
    prepare_regulation, regulations_repository, mock_regulation_preparator, regulation, error
):
    store_regulation(regulations_repository, regulation)

    with pytest.raises(error):
        await prepare_regulation.execute(None, REGULATION_ID)

    mock_regulation_preparator.prepare_regulation.assert_not_awaited()


async def test_prepare_regulation_without_content_marks_failed(
    prepare_regulation, regulations_repository, sections_repository, mock_regulations_storage
):
    mock_regulations_storage.get_regulation.side_effect = RegulationContentNotFound

    with pytest.raises(RegulationContentNotFound):
        await prepare_regulation.execute(None, REGULATION_ID)

    sections_repository.add_sections.assert_not_awaited()
    assert get_preparation_statuses(regulations_repository) == [
        RegulationPreparationStatus.IN_PROGRESS,
        RegulationPreparationStatus.FAILED,
    ]


@pytest.mark.parametrize("error", [ServiceUnavailable, RuntimeError])
async def test_prepare_regulation_failure_marks_failed(
    prepare_regulation, regulations_repository, sections_repository, mock_regulation_preparator, error
):
    mock_regulation_preparator.prepare_regulation.side_effect = error

    with pytest.raises(error):
        await prepare_regulation.execute(None, REGULATION_ID)

    sections_repository.add_sections.assert_not_awaited()
    assert get_preparation_statuses(regulations_repository) == [
        RegulationPreparationStatus.IN_PROGRESS,
        RegulationPreparationStatus.FAILED,
    ]


@pytest.mark.parametrize(
    ("description_status", "expected_schedules"),
    [(RegulationDescriptionStatus.IN_PROGRESS, 1), (RegulationDescriptionStatus.NOT_REQUESTED, 0)],
)
async def test_prepare_regulation_schedules_requested_description_generation(
    prepare_regulation,
    regulations_repository,
    mock_regulation_description_generation_scheduler,
    description_status,
    expected_schedules,
):
    store_regulation(regulations_repository, create_regulation(description_status=description_status))

    await prepare_regulation.execute(None, REGULATION_ID)

    scheduler = mock_regulation_description_generation_scheduler
    assert scheduler.schedule_regulation_description_generation.await_count == expected_schedules


@pytest.mark.parametrize(
    ("delivery_attempt", "expected_failed", "expected_statuses"),
    [
        (MAX_REGULATION_PREPARATION_DELIVERIES, False, []),
        (MAX_REGULATION_PREPARATION_DELIVERIES + 1, True, [RegulationPreparationStatus.FAILED]),
    ],
    ids=("within limit", "limit exceeded"),
)
async def test_fail_regulation_preparation(
    fail_regulation_preparation, regulations_repository, delivery_attempt, expected_failed, expected_statuses
):
    failed = await fail_regulation_preparation.execute(None, REGULATION_ID, delivery_attempt)

    assert failed is expected_failed
    assert get_preparation_statuses(regulations_repository) == expected_statuses


async def test_retry_regulation_preparation_schedules_preparation(
    retry_regulation_preparation, regulations_repository, mock_regulation_preparation_scheduler
):
    store_regulation(regulations_repository, create_regulation(RegulationPreparationStatus.FAILED))

    await retry_regulation_preparation.execute(ADMIN, REGULATION_ID)

    assert get_preparation_statuses(regulations_repository) == [RegulationPreparationStatus.IN_PROGRESS]
    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_awaited_once()


@pytest.mark.parametrize(
    ("regulation", "error"),
    [
        (None, RegulationNotFound),
        (create_regulation(RegulationPreparationStatus.NOT_STARTED), RegulationInInvalidState),
        (create_regulation(RegulationPreparationStatus.IN_PROGRESS), RegulationPreparationInProgress),
        (create_regulation(RegulationPreparationStatus.PREPARED), RegulationAlreadyInitialized),
    ],
    ids=("not found", "not uploaded", "in progress", "already prepared"),
)
async def test_retry_regulation_preparation_rejected(
    retry_regulation_preparation, regulations_repository, mock_regulation_preparation_scheduler, regulation, error
):
    store_regulation(regulations_repository, regulation)

    with pytest.raises(error):
        await retry_regulation_preparation.execute(ADMIN, REGULATION_ID)

    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_confirm_regulation_upload_schedules_preparation(
    confirm_regulation_upload, regulations_repository, mock_regulations_storage, mock_regulation_preparation_scheduler
):
    mock_regulations_storage.check_regulation_exists.return_value = True

    await confirm_regulation_upload.execute(ADMIN, REGULATION_ID)

    assert get_preparation_statuses(regulations_repository) == [RegulationPreparationStatus.IN_PROGRESS]
    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_awaited_once()


@pytest.mark.parametrize(
    ("regulation", "error"),
    [
        (None, RegulationNotFound),
        (create_regulation(RegulationPreparationStatus.PREPARED), RegulationAlreadyInitialized),
        (create_regulation(RegulationPreparationStatus.IN_PROGRESS), RegulationPreparationInProgress),
        (create_regulation(RegulationPreparationStatus.FAILED), RegulationInInvalidState),
    ],
    ids=("not found", "already prepared", "in progress", "already failed"),
)
async def test_confirm_regulation_upload_rejected(
    confirm_regulation_upload, regulations_repository, mock_regulation_preparation_scheduler, regulation, error
):
    store_regulation(regulations_repository, regulation)

    with pytest.raises(error):
        await confirm_regulation_upload.execute(ADMIN, REGULATION_ID)

    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_confirm_regulation_upload_without_content(
    confirm_regulation_upload, mock_regulations_storage, mock_regulation_preparation_scheduler
):
    mock_regulations_storage.check_regulation_exists.return_value = False

    with pytest.raises(RegulationContentNotFound):
        await confirm_regulation_upload.execute(ADMIN, REGULATION_ID)

    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_generate_regulation_description_saves_description_with_vector(
    generate_regulation_description, regulations_repository, mock_regulation_description_writer, mock_embedding_port
):
    store_regulation(
        regulations_repository, create_regulation(description_status=RegulationDescriptionStatus.IN_PROGRESS)
    )
    mock_regulation_description_writer.write.return_value = "Załatwianie typowych spraw przez studentów"
    mock_embedding_port.embed_texts.return_value = [[0.1, 0.2]]

    await generate_regulation_description.execute(None, REGULATION_ID)

    assert mock_regulation_description_writer.write.await_args.args[0].presentation_name == "Regulamin studiów"
    mock_embedding_port.embed_texts.assert_awaited_once_with(["Załatwianie typowych spraw przez studentów"])
    assert regulations_repository.set_generated_description.await_args.args[-2:] == (
        "Załatwianie typowych spraw przez studentów",
        [0.1, 0.2],
    )


@pytest.mark.parametrize(
    "regulation",
    [None, create_regulation(description_status=RegulationDescriptionStatus.GENERATED)],
    ids=("not found", "already generated"),
)
async def test_generate_regulation_description_skipped(
    generate_regulation_description, regulations_repository, mock_regulation_description_writer, regulation
):
    store_regulation(regulations_repository, regulation)

    await generate_regulation_description.execute(None, REGULATION_ID)

    mock_regulation_description_writer.write.assert_not_awaited()
    assert get_description_statuses(regulations_repository) == []


@pytest.mark.parametrize("error", [ServiceUnavailable, RuntimeError])
async def test_generate_regulation_description_failure_marks_failed(
    generate_regulation_description, regulations_repository, mock_regulation_description_writer, error
):
    mock_regulation_description_writer.write.side_effect = error

    with pytest.raises(error):
        await generate_regulation_description.execute(None, REGULATION_ID)

    regulations_repository.set_generated_description.assert_not_awaited()
    assert get_description_statuses(regulations_repository) == [
        RegulationDescriptionStatus.IN_PROGRESS,
        RegulationDescriptionStatus.FAILED,
    ]


async def test_generate_regulation_description_of_removed_regulation(
    generate_regulation_description, regulations_repository
):
    regulations_repository.set_generated_description.side_effect = RegulationNotFound

    await generate_regulation_description.execute(None, REGULATION_ID)


@pytest.mark.parametrize(
    ("delivery_attempt", "expected_failed", "expected_statuses"),
    [
        (MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES, False, []),
        (MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES + 1, True, [RegulationDescriptionStatus.FAILED]),
    ],
    ids=("within limit", "limit exceeded"),
)
async def test_fail_regulation_description_generation(
    fail_regulation_description_generation,
    regulations_repository,
    delivery_attempt,
    expected_failed,
    expected_statuses,
):
    failed = await fail_regulation_description_generation.execute(None, REGULATION_ID, delivery_attempt)

    assert failed is expected_failed
    assert get_description_statuses(regulations_repository) == expected_statuses


async def test_regenerate_regulation_description_schedules_generation(
    regenerate_regulation_description, regulations_repository, mock_regulation_description_generation_scheduler
):
    store_regulation(
        regulations_repository,
        create_regulation(RegulationPreparationStatus.PREPARED, RegulationDescriptionStatus.GENERATED),
    )

    await regenerate_regulation_description.execute(ADMIN, REGULATION_ID)

    assert get_description_statuses(regulations_repository) == [RegulationDescriptionStatus.IN_PROGRESS]
    scheduler = mock_regulation_description_generation_scheduler
    scheduler.schedule_regulation_description_generation.assert_awaited_once()


@pytest.mark.parametrize(
    ("regulation", "error"),
    [
        (None, RegulationNotFound),
        (create_regulation(RegulationPreparationStatus.IN_PROGRESS), RegulationInInvalidState),
        (
            create_regulation(RegulationPreparationStatus.PREPARED, RegulationDescriptionStatus.IN_PROGRESS),
            RegulationDescriptionGenerationInProgress,
        ),
    ],
    ids=("not found", "not prepared", "generation in progress"),
)
async def test_regenerate_regulation_description_rejected(
    regenerate_regulation_description,
    regulations_repository,
    mock_regulation_description_generation_scheduler,
    regulation,
    error,
):
    store_regulation(regulations_repository, regulation)

    with pytest.raises(error):
        await regenerate_regulation_description.execute(ADMIN, REGULATION_ID)

    scheduler = mock_regulation_description_generation_scheduler
    scheduler.schedule_regulation_description_generation.assert_not_awaited()


@pytest.mark.parametrize(
    ("generate_description", "description_status"),
    [(False, RegulationDescriptionStatus.NOT_REQUESTED), (True, RegulationDescriptionStatus.IN_PROGRESS)],
)
async def test_add_regulation_registers_regulation(
    add_regulation,
    regulations_repository,
    mock_regulations_storage,
    generate_description,
    description_status,
):
    regulations_repository.register_regulation.return_value = REGULATION_ID
    regulation_data = RegulationData(
        scope=RegulationScope.PUBLIC,
        name="regulation.pdf",
        regulationType=RegulationType.STATUTE,
        organizationId=ORGANIZATION_ID,
        suborganizationId=SUBORGANIZATION_ID,
        generateDescription=generate_description,
    )

    upload_target = await add_regulation.execute(ADMIN, regulation_data)

    assert regulations_repository.register_regulation.await_args.args[-1] == RegulationRegistrationData(
        presentation_name="regulation.pdf",
        regulation_type=RegulationType.STATUTE,
        organization_id=ORGANIZATION_ID,
        suborganization_id=SUBORGANIZATION_ID,
        description_status=description_status,
    )
    mock_regulations_storage.get_upload_target.assert_awaited_once_with(REGULATION_ID)
    assert upload_target == mock_regulations_storage.get_upload_target.return_value


@pytest.mark.parametrize(
    ("preparation_status", "expected_sections_removals"),
    [(RegulationPreparationStatus.PREPARED, 1), (RegulationPreparationStatus.NOT_STARTED, 0)],
)
async def test_delete_regulation(
    delete_regulation,
    regulations_repository,
    sections_repository,
    mock_regulations_storage,
    preparation_status,
    expected_sections_removals,
):
    store_regulation(regulations_repository, create_regulation(preparation_status))

    await delete_regulation.execute(ADMIN, REGULATION_ID)

    assert sections_repository.remove_sections.await_count == expected_sections_removals
    regulations_repository.unregister_regulation.assert_awaited_once()
    mock_regulations_storage.delete_regulation.assert_awaited_once_with(REGULATION_ID)


async def test_delete_regulation_ignores_storage_error(
    delete_regulation, regulations_repository, mock_regulations_storage
):
    mock_regulations_storage.delete_regulation.side_effect = Exception("Storage error")

    await delete_regulation.execute(ADMIN, REGULATION_ID)

    regulations_repository.unregister_regulation.assert_awaited_once()


@pytest.mark.parametrize(
    ("regulation", "error"),
    [
        (None, RegulationNotFound),
        (create_regulation(RegulationPreparationStatus.NOT_STARTED), RegulationsNotPreparedToSearch),
        (create_regulation(RegulationPreparationStatus.PREPARED), RegulationInInvalidState),
    ],
    ids=("not found", "not prepared", "prepared without sections"),
)
async def test_search_regulation_without_sections(
    search_regulation, regulations_repository, sections_repository, regulation, error
):
    sections_repository.search.side_effect = RegulationDocumentsNotFound
    store_regulation(regulations_repository, regulation)

    with pytest.raises(error):
        await search_regulation.execute(ADMIN, REGULATION_ID, SearchParams(threshold=0, query="urlop"))
