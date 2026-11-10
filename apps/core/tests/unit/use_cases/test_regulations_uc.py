from datetime import UTC, datetime
from uuid import UUID

import pytest

from core_service.application.dtos.regulations import RegulationData, RegulationDetailsData, RegulationRepresentation
from core_service.application.dtos.search import SearchParams
from core_service.application.use_cases.regulations import (
    MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES,
    MAX_REGULATION_PREPARATION_DELIVERIES,
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
    UpdateRegulation,
)
from core_service.domain.entities.regulation import Regulation
from core_service.domain.exceptions.descriptions import DescriptionGenerationInProgress
from core_service.domain.exceptions.documents import RegulationDocumentsNotFound
from core_service.domain.exceptions.regulations import (
    RegulationAlreadyInitialized,
    RegulationContentNotFound,
    RegulationInInvalidState,
    RegulationNotFound,
    RegulationPreparationInProgress,
    RegulationsNotPreparedToSearch,
)
from core_service.domain.value_objects.descriptions import DescriptionStatus
from core_service.domain.value_objects.regulations import (
    RegulationOwner,
    RegulationPreparationStatus,
    RegulationRegistrationData,
    RegulationScope,
    RegulationType,
)
from core_service.domain.value_objects.users import Caller
from core_service.shared.exceptions import ServiceUnavailable
from tests.consts import ADMIN_ID, ORGANIZATION_ID, SUBORGANIZATION_ID, TASK_FAILURES, TASK_FAILURES_IDS
from tests.mocks import get_awaited_argument, get_awaited_arguments, record_saved_states

ADMIN = Caller(user_id=ADMIN_ID, is_admin=True)

REGULATION_ID = UUID("5c1d2e3f-4a5b-4c6d-8e7f-9a0b1c2d3e4f")


def create_regulation(
    preparation_status: RegulationPreparationStatus = RegulationPreparationStatus.NOT_STARTED,
    description_status: DescriptionStatus = DescriptionStatus.NOT_REQUESTED,
    description: str | None = None,
) -> Regulation:
    return Regulation(
        id=REGULATION_ID,
        presentation_name="Regulamin studiów",
        preparation_status=preparation_status,
        description=description,
        description_status=description_status,
    )


def create_regulation_representation(
    preparation_status: RegulationPreparationStatus = RegulationPreparationStatus.NOT_STARTED,
    description: str | None = None,
) -> RegulationRepresentation:
    return RegulationRepresentation(
        id=REGULATION_ID,
        create_date=datetime(2026, 1, 1, 10, 0, 0, tzinfo=UTC),
        presentation_name="Regulamin studiów",
        description=description,
        preparation_status=preparation_status,
    )


def store_regulation(regulations_repository, regulation: Regulation | None) -> None:
    regulations_repository.get_for_update.return_value = regulation


def store_regulation_representation(regulations_repository, regulation: RegulationRepresentation | None) -> None:
    regulations_repository.get_regulation_representation.return_value = regulation


def record_preparation_statuses(regulations_repository) -> list[RegulationPreparationStatus]:
    return record_saved_states(regulations_repository.save, "regulation", "preparation_status")


def record_description_statuses(regulations_repository) -> list[DescriptionStatus]:
    return record_saved_states(regulations_repository.save, "regulation", "description_status")


@pytest.fixture
def regulations_repository(mock_regulations_repo):
    mock_regulations_repo.get_regulation_owner.return_value = RegulationOwner(user_id=None)
    store_regulation(mock_regulations_repo, create_regulation())
    store_regulation_representation(mock_regulations_repo, create_regulation_representation())
    return mock_regulations_repo


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
    mock_texts_embedder,
):
    return GenerateRegulationDescription(
        session_maker=mock_session_maker,
        regulations_repository=regulations_repository,
        sections_repository=sections_repository,
        description_writer=mock_regulation_description_writer,
        texts_embedder=mock_texts_embedder,
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
def update_regulation(mock_session_maker, regulations_repository, mock_texts_embedder):
    return UpdateRegulation(
        session_maker=mock_session_maker,
        regulations_repository=regulations_repository,
        texts_embedder=mock_texts_embedder,
    )


@pytest.fixture
def delete_regulation(mock_session_maker, regulations_repository, mock_regulations_storage):
    return DeleteRegulation(
        session_maker=mock_session_maker,
        regulations_repository=regulations_repository,
        regulations_storage=mock_regulations_storage,
    )


@pytest.fixture
def search_regulation(mock_session_maker, mock_texts_embedder, sections_repository, regulations_repository):
    return SearchRegulation(
        session_maker=mock_session_maker,
        embedding_port=mock_texts_embedder,
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
    preparation_statuses = record_preparation_statuses(regulations_repository)
    mock_regulations_storage.get_regulation.return_value = b"content"
    sections = mock_regulation_preparator.prepare_regulation.return_value

    await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt=True)

    mock_regulation_preparator.prepare_regulation.assert_awaited_once_with(b"content")
    assert get_awaited_argument(sections_repository.add_sections, "sections") == sections
    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS, RegulationPreparationStatus.PREPARED]


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
        await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt=True)

    mock_regulation_preparator.prepare_regulation.assert_not_awaited()
    regulations_repository.save.assert_not_awaited()


async def test_prepare_regulation_without_content_marks_failed(
    prepare_regulation, regulations_repository, sections_repository, mock_regulations_storage
):
    preparation_statuses = record_preparation_statuses(regulations_repository)
    mock_regulations_storage.get_regulation.side_effect = RegulationContentNotFound

    with pytest.raises(RegulationContentNotFound):
        await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt=True)

    sections_repository.add_sections.assert_not_awaited()
    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS, RegulationPreparationStatus.FAILED]


@pytest.mark.parametrize(("error", "is_last_attempt"), TASK_FAILURES, ids=TASK_FAILURES_IDS)
async def test_prepare_regulation_failure_marks_failed(
    prepare_regulation, regulations_repository, sections_repository, mock_regulation_preparator, error, is_last_attempt
):
    preparation_statuses = record_preparation_statuses(regulations_repository)
    mock_regulation_preparator.prepare_regulation.side_effect = error

    with pytest.raises(error):
        await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt)

    sections_repository.add_sections.assert_not_awaited()
    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS, RegulationPreparationStatus.FAILED]


async def test_prepare_regulation_retried_failure_keeps_in_progress(
    prepare_regulation, regulations_repository, mock_regulation_preparator
):
    preparation_statuses = record_preparation_statuses(regulations_repository)
    mock_regulation_preparator.prepare_regulation.side_effect = ServiceUnavailable

    with pytest.raises(ServiceUnavailable):
        await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt=False)

    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS]


@pytest.mark.parametrize("error", [ServiceUnavailable, RuntimeError])
async def test_prepare_regulation_save_failure_marks_failed(
    prepare_regulation, regulations_repository, sections_repository, error
):
    preparation_statuses = record_preparation_statuses(regulations_repository)
    sections_repository.add_sections.side_effect = error

    with pytest.raises(error):
        await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt=True)

    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS, RegulationPreparationStatus.FAILED]


async def test_prepare_regulation_removed_during_preparation(
    prepare_regulation, regulations_repository, sections_repository
):
    preparation_statuses = record_preparation_statuses(regulations_repository)
    regulations_repository.get_for_update.side_effect = [create_regulation(), None]

    await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt=True)

    sections_repository.add_sections.assert_not_awaited()
    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS]


async def test_prepare_regulation_prepared_by_another_delivery(
    prepare_regulation, regulations_repository, sections_repository
):
    preparation_statuses = record_preparation_statuses(regulations_repository)
    regulations_repository.get_for_update.side_effect = [
        create_regulation(),
        create_regulation(RegulationPreparationStatus.PREPARED),
    ]

    await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt=True)

    sections_repository.add_sections.assert_not_awaited()
    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS]


async def test_prepare_regulation_failure_keeps_regulation_prepared_by_another_delivery(
    prepare_regulation, regulations_repository, mock_regulation_preparator
):
    preparation_statuses = record_preparation_statuses(regulations_repository)
    regulations_repository.get_for_update.side_effect = [
        create_regulation(),
        create_regulation(RegulationPreparationStatus.PREPARED),
    ]
    mock_regulation_preparator.prepare_regulation.side_effect = ServiceUnavailable

    with pytest.raises(ServiceUnavailable):
        await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt=True)

    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS]


@pytest.mark.parametrize(
    ("description_status", "expected_schedules"),
    [(DescriptionStatus.IN_PROGRESS, 1), (DescriptionStatus.NOT_REQUESTED, 0)],
)
async def test_prepare_regulation_schedules_requested_description_generation(
    prepare_regulation,
    regulations_repository,
    mock_regulation_description_generation_scheduler,
    description_status,
    expected_schedules,
):
    store_regulation(regulations_repository, create_regulation(description_status=description_status))

    await prepare_regulation.execute(None, REGULATION_ID, is_last_attempt=True)

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
    preparation_statuses = record_preparation_statuses(regulations_repository)

    failed = await fail_regulation_preparation.execute(None, REGULATION_ID, delivery_attempt)

    assert failed is expected_failed
    assert preparation_statuses == expected_statuses


async def test_fail_regulation_preparation_of_removed_regulation(fail_regulation_preparation, regulations_repository):
    store_regulation(regulations_repository, None)

    failed = await fail_regulation_preparation.execute(None, REGULATION_ID, MAX_REGULATION_PREPARATION_DELIVERIES + 1)

    assert failed is True
    regulations_repository.save.assert_not_awaited()


async def test_fail_regulation_preparation_of_prepared_regulation(fail_regulation_preparation, regulations_repository):
    store_regulation(regulations_repository, create_regulation(RegulationPreparationStatus.PREPARED))

    failed = await fail_regulation_preparation.execute(None, REGULATION_ID, MAX_REGULATION_PREPARATION_DELIVERIES + 1)

    assert failed is True
    regulations_repository.save.assert_not_awaited()


async def test_retry_regulation_preparation_schedules_preparation(
    retry_regulation_preparation, regulations_repository, mock_regulation_preparation_scheduler
):
    preparation_statuses = record_preparation_statuses(regulations_repository)
    store_regulation(regulations_repository, create_regulation(RegulationPreparationStatus.FAILED))

    await retry_regulation_preparation.execute(ADMIN, REGULATION_ID)

    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS]
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

    regulations_repository.save.assert_not_awaited()
    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_confirm_regulation_upload_schedules_preparation(
    confirm_regulation_upload, regulations_repository, mock_regulations_storage, mock_regulation_preparation_scheduler
):
    preparation_statuses = record_preparation_statuses(regulations_repository)
    mock_regulations_storage.check_regulation_exists.return_value = True

    await confirm_regulation_upload.execute(ADMIN, REGULATION_ID)

    assert preparation_statuses == [RegulationPreparationStatus.IN_PROGRESS]
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

    regulations_repository.save.assert_not_awaited()
    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_confirm_regulation_upload_without_content(
    confirm_regulation_upload, regulations_repository, mock_regulations_storage, mock_regulation_preparation_scheduler
):
    mock_regulations_storage.check_regulation_exists.return_value = False

    with pytest.raises(RegulationContentNotFound):
        await confirm_regulation_upload.execute(ADMIN, REGULATION_ID)

    regulations_repository.save.assert_not_awaited()
    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_generate_regulation_description_saves_description_with_vector(
    generate_regulation_description, regulations_repository, mock_regulation_description_writer, mock_texts_embedder
):
    regulation = create_regulation(description_status=DescriptionStatus.IN_PROGRESS)
    store_regulation(regulations_repository, regulation)
    description = "Załatwianie typowych spraw przez studentów"
    mock_regulation_description_writer.write.return_value = description
    mock_texts_embedder.embed_texts.return_value = [[0.1, 0.2]]

    await generate_regulation_description.execute(None, REGULATION_ID, is_last_attempt=True)

    description_source = get_awaited_argument(mock_regulation_description_writer.write, "description_source")
    assert description_source.presentation_name == "Regulamin studiów"
    mock_texts_embedder.embed_texts.assert_awaited_once_with([description])
    assert regulation.description == description
    assert regulation.description_status == DescriptionStatus.GENERATED
    assert get_awaited_argument(regulations_repository.set_description_vector, "vector") == [0.1, 0.2]


@pytest.mark.parametrize(
    "regulation",
    [None, create_regulation(description_status=DescriptionStatus.GENERATED)],
    ids=("not found", "already generated"),
)
async def test_generate_regulation_description_skipped(
    generate_regulation_description, regulations_repository, mock_regulation_description_writer, regulation
):
    store_regulation(regulations_repository, regulation)

    await generate_regulation_description.execute(None, REGULATION_ID, is_last_attempt=True)

    mock_regulation_description_writer.write.assert_not_awaited()
    regulations_repository.save.assert_not_awaited()


@pytest.mark.parametrize(("error", "is_last_attempt"), TASK_FAILURES, ids=TASK_FAILURES_IDS)
async def test_generate_regulation_description_failure_marks_failed(
    generate_regulation_description, regulations_repository, mock_regulation_description_writer, error, is_last_attempt
):
    description_statuses = record_description_statuses(regulations_repository)
    mock_regulation_description_writer.write.side_effect = error

    with pytest.raises(error):
        await generate_regulation_description.execute(None, REGULATION_ID, is_last_attempt)

    regulations_repository.set_description_vector.assert_not_awaited()
    assert description_statuses == [DescriptionStatus.IN_PROGRESS, DescriptionStatus.FAILED]


async def test_generate_regulation_description_retried_failure_keeps_in_progress(
    generate_regulation_description, regulations_repository, mock_regulation_description_writer
):
    description_statuses = record_description_statuses(regulations_repository)
    mock_regulation_description_writer.write.side_effect = ServiceUnavailable

    with pytest.raises(ServiceUnavailable):
        await generate_regulation_description.execute(None, REGULATION_ID, is_last_attempt=False)

    assert description_statuses == [DescriptionStatus.IN_PROGRESS]


async def test_generate_regulation_description_failure_keeps_description_generated_by_another_delivery(
    generate_regulation_description, regulations_repository, mock_regulation_description_writer
):
    description_statuses = record_description_statuses(regulations_repository)
    regulations_repository.get_for_update.side_effect = [
        create_regulation(),
        create_regulation(description_status=DescriptionStatus.GENERATED),
    ]
    mock_regulation_description_writer.write.side_effect = RuntimeError

    with pytest.raises(RuntimeError):
        await generate_regulation_description.execute(None, REGULATION_ID, is_last_attempt=True)

    assert description_statuses == [DescriptionStatus.IN_PROGRESS]


@pytest.mark.parametrize("error", [ServiceUnavailable, RuntimeError])
async def test_generate_regulation_description_save_failure_marks_failed(
    generate_regulation_description, regulations_repository, error
):
    description_statuses = record_description_statuses(regulations_repository)
    regulations_repository.get_for_update.side_effect = lambda *_: create_regulation()
    regulations_repository.set_description_vector.side_effect = error

    with pytest.raises(error):
        await generate_regulation_description.execute(None, REGULATION_ID, is_last_attempt=True)

    assert description_statuses[-1] == DescriptionStatus.FAILED


async def test_generate_regulation_description_of_removed_regulation(
    generate_regulation_description, regulations_repository
):
    description_statuses = record_description_statuses(regulations_repository)
    regulations_repository.get_for_update.side_effect = [create_regulation(), None]

    await generate_regulation_description.execute(None, REGULATION_ID, is_last_attempt=True)

    regulations_repository.set_description_vector.assert_not_awaited()
    assert description_statuses == [DescriptionStatus.IN_PROGRESS]


async def test_generate_regulation_description_failure_of_removed_regulation(
    generate_regulation_description, regulations_repository, mock_regulation_description_writer
):
    description_statuses = record_description_statuses(regulations_repository)
    regulations_repository.get_for_update.side_effect = [create_regulation(), None]
    mock_regulation_description_writer.write.side_effect = ServiceUnavailable

    with pytest.raises(ServiceUnavailable):
        await generate_regulation_description.execute(None, REGULATION_ID, is_last_attempt=True)

    assert description_statuses == [DescriptionStatus.IN_PROGRESS]


@pytest.mark.parametrize(
    ("delivery_attempt", "expected_failed", "expected_statuses"),
    [
        (MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES, False, []),
        (MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES + 1, True, [DescriptionStatus.FAILED]),
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
    description_statuses = record_description_statuses(regulations_repository)

    failed = await fail_regulation_description_generation.execute(None, REGULATION_ID, delivery_attempt)

    assert failed is expected_failed
    assert description_statuses == expected_statuses


async def test_fail_regulation_description_generation_of_removed_regulation(
    fail_regulation_description_generation, regulations_repository
):
    store_regulation(regulations_repository, None)

    failed = await fail_regulation_description_generation.execute(
        None, REGULATION_ID, MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES + 1
    )

    assert failed is True
    regulations_repository.save.assert_not_awaited()


async def test_regenerate_regulation_description_schedules_generation(
    regenerate_regulation_description, regulations_repository, mock_regulation_description_generation_scheduler
):
    description_statuses = record_description_statuses(regulations_repository)
    store_regulation(
        regulations_repository, create_regulation(RegulationPreparationStatus.PREPARED, DescriptionStatus.GENERATED)
    )

    await regenerate_regulation_description.execute(ADMIN, REGULATION_ID)

    assert description_statuses == [DescriptionStatus.IN_PROGRESS]
    scheduler = mock_regulation_description_generation_scheduler
    scheduler.schedule_regulation_description_generation.assert_awaited_once()


@pytest.mark.parametrize(
    ("regulation", "error"),
    [
        (None, RegulationNotFound),
        (create_regulation(RegulationPreparationStatus.IN_PROGRESS), RegulationInInvalidState),
        (
            create_regulation(RegulationPreparationStatus.PREPARED, DescriptionStatus.IN_PROGRESS),
            DescriptionGenerationInProgress,
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

    regulations_repository.save.assert_not_awaited()
    scheduler = mock_regulation_description_generation_scheduler
    scheduler.schedule_regulation_description_generation.assert_not_awaited()


@pytest.mark.parametrize(
    ("generate_description", "description_status"),
    [(False, DescriptionStatus.NOT_REQUESTED), (True, DescriptionStatus.IN_PROGRESS)],
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
        regulation_type=RegulationType.STATUTE,
        organization_id=ORGANIZATION_ID,
        suborganization_id=SUBORGANIZATION_ID,
        generate_description=generate_description,
    )

    upload_target = await add_regulation.execute(ADMIN, regulation_data)

    registration_data = get_awaited_argument(regulations_repository.register_regulation, "regulation_registration_data")
    assert registration_data == RegulationRegistrationData(
        presentation_name="regulation.pdf",
        regulation_type=RegulationType.STATUTE,
        organization_id=ORGANIZATION_ID,
        suborganization_id=SUBORGANIZATION_ID,
        description_status=description_status,
    )
    mock_regulations_storage.get_upload_target.assert_awaited_once_with(REGULATION_ID)
    assert upload_target == mock_regulations_storage.get_upload_target.return_value


async def test_update_regulation_saves_details(update_regulation, regulations_repository):
    regulation = create_regulation()
    store_regulation(regulations_repository, regulation)

    result = await update_regulation.execute(
        ADMIN, REGULATION_ID, RegulationDetailsData(name="Nowy regulamin", description="Opis.")
    )

    assert regulation.presentation_name == "Nowy regulamin"
    assert regulation.description == "Opis."
    assert get_awaited_argument(regulations_repository.save, "regulation") is regulation
    assert result == regulations_repository.save.return_value


@pytest.mark.parametrize(
    ("description", "expected_vectors"),
    [("Nowy opis.", [[0.1, 0.2]]), ("Opis.", []), (None, [None]), ("", [None]), ("   ", [None])],
    ids=("changed", "unchanged", "removed", "empty", "blank"),
)
async def test_update_regulation_description_vector(
    update_regulation, regulations_repository, mock_texts_embedder, description, expected_vectors
):
    store_regulation_representation(regulations_repository, create_regulation_representation(description="Opis."))
    mock_texts_embedder.embed_texts.return_value = [[0.1, 0.2]]

    await update_regulation.execute(
        ADMIN, REGULATION_ID, RegulationDetailsData(name="Regulamin studiów", description=description)
    )

    vectors = get_awaited_arguments(regulations_repository.set_description_vector, "vector")
    assert vectors == expected_vectors


async def test_update_regulation_not_saved_when_embedding_unavailable(
    update_regulation, regulations_repository, mock_texts_embedder
):
    mock_texts_embedder.embed_texts.side_effect = ServiceUnavailable

    with pytest.raises(ServiceUnavailable):
        await update_regulation.execute(
            ADMIN, REGULATION_ID, RegulationDetailsData(name="Regulamin studiów", description="Opis.")
        )

    regulations_repository.save.assert_not_awaited()


@pytest.mark.parametrize(
    ("regulation_representation", "regulation"),
    [(None, create_regulation()), (create_regulation_representation(), None)],
    ids=("not found", "removed during embedding"),
)
async def test_update_regulation_not_found(
    update_regulation, regulations_repository, regulation_representation, regulation
):
    store_regulation_representation(regulations_repository, regulation_representation)
    store_regulation(regulations_repository, regulation)

    with pytest.raises(RegulationNotFound):
        await update_regulation.execute(ADMIN, REGULATION_ID, RegulationDetailsData(name="Regulamin studiów"))

    regulations_repository.save.assert_not_awaited()


async def test_delete_regulation(delete_regulation, regulations_repository, mock_regulations_storage):
    await delete_regulation.execute(ADMIN, REGULATION_ID)

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
        (create_regulation_representation(RegulationPreparationStatus.NOT_STARTED), RegulationsNotPreparedToSearch),
        (create_regulation_representation(RegulationPreparationStatus.PREPARED), RegulationInInvalidState),
    ],
    ids=("not found", "not prepared", "prepared without sections"),
)
async def test_search_regulation_without_sections(
    search_regulation, regulations_repository, sections_repository, regulation, error
):
    sections_repository.search.side_effect = RegulationDocumentsNotFound
    store_regulation_representation(regulations_repository, regulation)

    with pytest.raises(error):
        await search_regulation.execute(ADMIN, REGULATION_ID, SearchParams(threshold=0, query="urlop"))
