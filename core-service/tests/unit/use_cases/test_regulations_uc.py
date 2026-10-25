from unittest.mock import AsyncMock, MagicMock

import pytest

from src.app.dtos.regulations import (
    RegulationData,
    RegulationDetailsData,
    RegulationRepresentation,
    RegulationUploadTarget,
)
from src.app.dtos.search import SearchParams
from src.app.use_cases.regulations import (
    AddRegulation,
    ConfirmRegulationUpload,
    DeleteRegulation,
    FailRegulationDescriptionGeneration,
    FailRegulationPreparation,
    GenerateRegulationDescription,
    GetRegulation,
    GetRegulationDownloadUrl,
    ListRegulations,
    PrepareRegulation,
    RegenerateRegulationDescription,
    RetryRegulationPreparation,
    SearchRegulation,
    UpdateRegulation,
)
from src.domain.exceptions.access import AccessForbidden, LoginRequired
from src.domain.exceptions.documents import RegulationDocumentsNotFound
from src.domain.exceptions.organizations import OrganizationNotFound
from src.domain.exceptions.regulations import (
    RegulationAlreadyInitialized,
    RegulationContentNotFound,
    RegulationDescriptionGenerationInProgress,
    RegulationInInvalidState,
    RegulationNotFound,
    RegulationPreparationInProgress,
    RegulationsNotPreparedToSearch,
)
from src.domain.value_objects.organizations import OrganizationFilter
from src.domain.value_objects.regulations import (
    RegulationDescriptionStatus,
    RegulationDetails,
    RegulationOwner,
    RegulationPreparationStatus,
    RegulationRegistrationData,
    RegulationScope,
    RegulationType,
    SectionContent,
)
from src.domain.value_objects.users import Caller
from src.shared.consts import (
    MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES,
    MAX_REGULATION_PREPARATION_DELIVERIES,
)
from src.shared.exceptions import ServiceUnavailable


def get_set_statuses(mock_regulations_repository):
    return [call.args[3] for call in mock_regulations_repository.set_preparation_status.await_args_list]


def get_set_description_statuses(mock_regulations_repository):
    return [call.args[3] for call in mock_regulations_repository.set_description_status.await_args_list]


async def test_prepare_regulation_success(
    mock_session_maker,
    mock_regulations_repository,
    mock_regulations_storage,
    mock_sections_repo,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_regulations_storage.get_regulation.return_value = b"content"

    mock_regulation_preparator = AsyncMock()
    mock_regulation_preparator.prepare_regulation.return_value = ["doc1", "doc2"]

    use_case = PrepareRegulation(
        session_maker=mock_session_maker,
        regulations_storage=mock_regulations_storage,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
        regulation_preparator=mock_regulation_preparator,
        description_generation_scheduler=AsyncMock(),
    )

    await use_case.execute(user_id, regulation_id)

    mock_regulations_repository.get_regulation_representation.assert_awaited_once()
    mock_regulations_storage.get_regulation.assert_awaited_once_with(regulation_id)
    mock_regulation_preparator.prepare_regulation.assert_awaited_once_with(b"content")
    mock_sections_repo.add_sections.assert_awaited_once()
    assert get_set_statuses(mock_regulations_repository) == [
        RegulationPreparationStatus.IN_PROGRESS,
        RegulationPreparationStatus.PREPARED,
    ]


async def test_prepare_regulation_not_found(
    mock_session_maker,
    mock_regulations_repository,
    mock_regulations_storage,
    mock_sections_repo,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    mock_regulations_repository.get_regulation_representation.return_value = None

    mock_regulation_preparator = AsyncMock()

    use_case = PrepareRegulation(
        session_maker=mock_session_maker,
        regulations_storage=mock_regulations_storage,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
        regulation_preparator=mock_regulation_preparator,
        description_generation_scheduler=AsyncMock(),
    )

    with pytest.raises(RegulationNotFound):
        await use_case.execute(user_id, regulation_id)


async def test_prepare_regulation_already_initialized(
    mock_session_maker,
    mock_regulations_repository,
    mock_regulations_storage,
    mock_sections_repo,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.PREPARED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_regulation_preparator = AsyncMock()

    use_case = PrepareRegulation(
        session_maker=mock_session_maker,
        regulations_storage=mock_regulations_storage,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
        regulation_preparator=mock_regulation_preparator,
        description_generation_scheduler=AsyncMock(),
    )

    with pytest.raises(RegulationAlreadyInitialized):
        await use_case.execute(user_id, regulation_id)


async def test_prepare_regulation_content_not_found(
    mock_session_maker,
    mock_regulations_repository,
    mock_regulations_storage,
    mock_sections_repo,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_regulations_storage.get_regulation.side_effect = RegulationContentNotFound

    mock_regulation_preparator = AsyncMock()

    use_case = PrepareRegulation(
        session_maker=mock_session_maker,
        regulations_storage=mock_regulations_storage,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
        regulation_preparator=mock_regulation_preparator,
        description_generation_scheduler=AsyncMock(),
    )

    with pytest.raises(RegulationContentNotFound):
        await use_case.execute(user_id, regulation_id)

    assert get_set_statuses(mock_regulations_repository) == [
        RegulationPreparationStatus.IN_PROGRESS,
        RegulationPreparationStatus.FAILED,
    ]


async def test_prepare_regulation_service_unavailable(
    mock_session_maker,
    mock_regulations_repository,
    mock_regulations_storage,
    mock_sections_repo,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_regulations_storage.get_regulation.return_value = b"content"

    mock_regulation_preparator = AsyncMock()
    mock_regulation_preparator.prepare_regulation.side_effect = ServiceUnavailable()

    use_case = PrepareRegulation(
        session_maker=mock_session_maker,
        regulations_storage=mock_regulations_storage,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
        regulation_preparator=mock_regulation_preparator,
        description_generation_scheduler=AsyncMock(),
    )

    with pytest.raises(ServiceUnavailable):
        await use_case.execute(user_id, regulation_id)

    assert get_set_statuses(mock_regulations_repository) == [
        RegulationPreparationStatus.IN_PROGRESS,
        RegulationPreparationStatus.FAILED,
    ]


async def test_prepare_regulation_unexpected_exception(
    mock_session_maker,
    mock_regulations_repository,
    mock_regulations_storage,
    mock_sections_repo,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_regulations_storage.get_regulation.return_value = b"content"

    mock_regulation_preparator = AsyncMock()
    mock_regulation_preparator.prepare_regulation.side_effect = RuntimeError("Unexpected Error")

    use_case = PrepareRegulation(
        session_maker=mock_session_maker,
        regulations_storage=mock_regulations_storage,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
        regulation_preparator=mock_regulation_preparator,
        description_generation_scheduler=AsyncMock(),
    )

    with pytest.raises(RuntimeError):
        await use_case.execute(user_id, regulation_id)

    assert get_set_statuses(mock_regulations_repository) == [
        RegulationPreparationStatus.IN_PROGRESS,
        RegulationPreparationStatus.FAILED,
    ]


async def test_fail_regulation_preparation_deliveries_limit_exceeded(
    mock_session_maker, mock_regulations_repository, uuid_generator
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    use_case = FailRegulationPreparation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    failed = await use_case.execute(user_id, regulation_id, MAX_REGULATION_PREPARATION_DELIVERIES + 1)

    assert failed is True
    mock_regulations_repository.set_preparation_status.assert_awaited_once_with(
        mock_session_maker.begin.return_value.__aenter__.return_value,
        user_id,
        regulation_id,
        RegulationPreparationStatus.FAILED,
    )


async def test_fail_regulation_preparation_deliveries_limit_not_exceeded(
    mock_session_maker, mock_regulations_repository, uuid_generator
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    use_case = FailRegulationPreparation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    failed = await use_case.execute(user_id, regulation_id, MAX_REGULATION_PREPARATION_DELIVERIES)

    assert failed is False
    mock_regulations_repository.set_preparation_status.assert_not_awaited()


async def test_retry_regulation_preparation_success(
    mock_session_maker,
    mock_regulations_repository,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.FAILED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_scheduler = AsyncMock()

    use_case = RetryRegulationPreparation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulation_preparation_scheduler=mock_scheduler,
    )

    await use_case.execute(Caller(user_id), regulation_id)

    assert get_set_statuses(mock_regulations_repository) == [RegulationPreparationStatus.IN_PROGRESS]
    mock_scheduler.schedule_regulation_preparation.assert_awaited_once_with(
        mock_session_maker.begin.return_value.__aenter__.return_value, user_id, regulation_id
    )


async def test_retry_regulation_preparation_not_found(
    mock_session_maker,
    mock_regulations_repository,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_regulations_repository.get_regulation_representation.return_value = None

    mock_scheduler = AsyncMock()

    use_case = RetryRegulationPreparation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(RegulationNotFound):
        await use_case.execute(Caller(user_id), regulation_id)

    mock_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_retry_regulation_preparation_content_not_uploaded(
    mock_session_maker,
    mock_regulations_repository,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_scheduler = AsyncMock()

    use_case = RetryRegulationPreparation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(RegulationInInvalidState):
        await use_case.execute(Caller(user_id), regulation_id)

    mock_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_retry_regulation_preparation_already_prepared(
    mock_session_maker,
    mock_regulations_repository,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.PREPARED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_scheduler = AsyncMock()

    use_case = RetryRegulationPreparation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(RegulationAlreadyInitialized):
        await use_case.execute(Caller(user_id), regulation_id)

    mock_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_retry_regulation_preparation_already_in_progress(
    mock_session_maker,
    mock_regulations_repository,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.IN_PROGRESS
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_scheduler = AsyncMock()

    use_case = RetryRegulationPreparation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(RegulationPreparationInProgress):
        await use_case.execute(Caller(user_id), regulation_id)

    mock_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_retry_regulation_preparation_scheduler_unavailable(
    mock_session_maker,
    mock_regulations_repository,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.FAILED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_scheduler = AsyncMock()
    mock_scheduler.schedule_regulation_preparation.side_effect = ServiceUnavailable()

    use_case = RetryRegulationPreparation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(ServiceUnavailable):
        await use_case.execute(Caller(user_id), regulation_id)

    assert get_set_statuses(mock_regulations_repository) == [RegulationPreparationStatus.IN_PROGRESS]


async def test_add_public_regulation_success(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    regulation_id = next(uuid_generator)
    mock_regulations_repository.register_regulation.return_value = regulation_id
    upload_target = RegulationUploadTarget(
        id=regulation_id, url="http://object-storage", fields={"key": str(regulation_id)}
    )
    mock_regulations_storage.get_upload_target.return_value = upload_target

    regulation_data = RegulationData(
        scope=RegulationScope.PUBLIC, name="regulation.pdf", regulationType=RegulationType.ACT
    )

    add_regulation = AddRegulation(
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        session_maker=mock_session_maker,
    )

    result = await add_regulation.execute(Caller(next(uuid_generator), is_admin=True), regulation_data)

    assert result == upload_target
    mock_regulations_repository.register_regulation.assert_awaited_once()
    mock_regulations_storage.get_upload_target.assert_awaited_once_with(regulation_id)


async def test_add_user_regulation_success(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.register_regulation.return_value = regulation_id
    upload_target = RegulationUploadTarget(
        id=regulation_id, url="http://object-storage", fields={"key": str(regulation_id)}
    )
    mock_regulations_storage.get_upload_target.return_value = upload_target

    regulation_data = RegulationData(
        scope=RegulationScope.PRIVATE, name="user-regulation.pdf", regulationType=RegulationType.ACT
    )

    add_regulation = AddRegulation(
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        session_maker=mock_session_maker,
    )

    result = await add_regulation.execute(Caller(user_id), regulation_data)

    assert result == upload_target
    assert mock_regulations_repository.register_regulation.await_args.args[1] == user_id
    mock_regulations_storage.get_upload_target.assert_awaited_once_with(regulation_id)


async def test_add_public_regulation_with_organization(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker, mock_opened_session
):
    regulation_id = next(uuid_generator)
    organization_id = next(uuid_generator)
    suborganization_id = next(uuid_generator)
    mock_regulations_repository.register_regulation.return_value = regulation_id

    regulation_data = RegulationData(
        scope=RegulationScope.PUBLIC,
        name="regulation.pdf",
        regulationType=RegulationType.STATUTE,
        organizationId=organization_id,
        suborganizationId=suborganization_id,
    )

    add_regulation = AddRegulation(
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        session_maker=mock_session_maker,
    )

    await add_regulation.execute(Caller(next(uuid_generator), is_admin=True), regulation_data)

    mock_regulations_repository.register_regulation.assert_awaited_once_with(
        mock_opened_session,
        None,
        RegulationRegistrationData(
            presentation_name="regulation.pdf",
            regulation_type=RegulationType.STATUTE,
            organization_id=organization_id,
            suborganization_id=suborganization_id,
        ),
    )


async def test_add_public_regulation_organization_not_found(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    mock_regulations_repository.register_regulation.side_effect = OrganizationNotFound

    regulation_data = RegulationData(
        scope=RegulationScope.PUBLIC, name="regulation.pdf", organizationId=next(uuid_generator)
    )

    add_regulation = AddRegulation(
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        session_maker=mock_session_maker,
    )

    with pytest.raises(OrganizationNotFound):
        await add_regulation.execute(Caller(next(uuid_generator), is_admin=True), regulation_data)

    mock_regulations_storage.get_upload_target.assert_not_awaited()


async def test_confirm_regulation_upload_success(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep
    mock_regulations_storage.check_regulation_exists.return_value = True

    mock_scheduler = AsyncMock()

    use_case = ConfirmRegulationUpload(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        regulation_preparation_scheduler=mock_scheduler,
    )

    await use_case.execute(Caller(user_id), regulation_id)

    mock_regulations_storage.check_regulation_exists.assert_called_once_with(regulation_id)
    mock_regulations_repository.set_preparation_status.assert_called_once_with(
        mock_session_maker.begin.return_value.__aenter__.return_value,
        user_id,
        regulation_id,
        RegulationPreparationStatus.IN_PROGRESS,
    )
    mock_scheduler.schedule_regulation_preparation.assert_awaited_once_with(
        mock_session_maker.begin.return_value.__aenter__.return_value, user_id, regulation_id
    )


async def test_confirm_regulation_upload_not_found(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_regulations_repository.get_regulation_representation.return_value = None

    mock_scheduler = AsyncMock()

    use_case = ConfirmRegulationUpload(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(RegulationNotFound):
        await use_case.execute(Caller(user_id), regulation_id)


@pytest.mark.asyncio
async def test_confirm_regulation_upload_already_prepared(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.PREPARED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_scheduler = AsyncMock()

    use_case = ConfirmRegulationUpload(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(RegulationAlreadyInitialized):
        await use_case.execute(Caller(user_id), regulation_id)


async def test_confirm_regulation_upload_content_not_found(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep
    mock_regulations_storage.check_regulation_exists.return_value = False

    mock_scheduler = AsyncMock()

    use_case = ConfirmRegulationUpload(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(RegulationContentNotFound):
        await use_case.execute(Caller(user_id), regulation_id)


async def test_confirm_regulation_upload_already_in_progress(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.IN_PROGRESS
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_scheduler = AsyncMock()

    use_case = ConfirmRegulationUpload(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(RegulationPreparationInProgress):
        await use_case.execute(Caller(user_id), regulation_id)

    mock_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_confirm_regulation_upload_already_failed(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.FAILED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_scheduler = AsyncMock()

    use_case = ConfirmRegulationUpload(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(RegulationInInvalidState):
        await use_case.execute(Caller(user_id), regulation_id)

    mock_scheduler.schedule_regulation_preparation.assert_not_awaited()


async def test_confirm_regulation_upload_scheduler_unavailable(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep
    mock_regulations_storage.check_regulation_exists.return_value = True

    mock_scheduler = AsyncMock()
    mock_scheduler.schedule_regulation_preparation.side_effect = ServiceUnavailable()

    use_case = ConfirmRegulationUpload(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        regulation_preparation_scheduler=mock_scheduler,
    )

    with pytest.raises(ServiceUnavailable):
        await use_case.execute(Caller(user_id), regulation_id)

    assert get_set_statuses(mock_regulations_repository) == [RegulationPreparationStatus.IN_PROGRESS]


async def test_get_regulation_download_url_success(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_regulations_repository.get_regulation_representation.return_value = MagicMock()
    mock_regulations_storage.get_download_url.return_value = "http://object-storage/regulation"

    use_case = GetRegulationDownloadUrl(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
    )

    result = await use_case.execute(Caller(user_id), regulation_id)

    assert result == "http://object-storage/regulation"
    mock_regulations_storage.get_download_url.assert_awaited_once_with(regulation_id)


async def test_get_regulation_download_url_not_found(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_regulations_repository.get_regulation_representation.return_value = None

    use_case = GetRegulationDownloadUrl(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
    )

    with pytest.raises(RegulationNotFound):
        await use_case.execute(Caller(user_id), regulation_id)


async def test_get_regulation_success(uuid_generator, mock_regulations_repository, mock_session_maker):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_result = MagicMock(spec=RegulationRepresentation)
    mock_regulations_repository.get_regulation_representation.return_value = mock_result

    use_case = GetRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    result = await use_case.execute(Caller(user_id), regulation_id)

    assert result == mock_result
    mock_regulations_repository.get_regulation_representation.assert_awaited_once()


async def test_get_regulation_not_found(uuid_generator, mock_regulations_repository, mock_session_maker):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_regulations_repository.get_regulation_representation.return_value = None

    use_case = GetRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    with pytest.raises(RegulationNotFound):
        await use_case.execute(Caller(user_id), regulation_id)


async def test_list_regulations_success(uuid_generator, mock_regulations_repository, mock_session_maker):
    user_id = next(uuid_generator)

    mock_result = MagicMock(spec=RegulationRepresentation)
    mock_result.regulation_type = RegulationType.ACT
    mock_results = [mock_result, MagicMock(spec=RegulationRepresentation)]
    mock_regulations_repository.list_regulations.return_value = mock_results

    use_case = ListRegulations(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    result = await use_case.execute(Caller(user_id), RegulationScope.PRIVATE, RegulationType.ACT, None)

    assert result == mock_results
    assert result[0].regulation_type == RegulationType.ACT
    mock_regulations_repository.list_regulations.assert_awaited_once()


async def test_list_regulations_with_organization_filter(
    uuid_generator, mock_regulations_repository, mock_session_maker, mock_opened_session
):
    organization_id = next(uuid_generator)
    suborganization_id = next(uuid_generator)
    organization_filter = OrganizationFilter(organization_id, suborganization_id)
    mock_regulations_repository.list_regulations.return_value = []

    use_case = ListRegulations(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    await use_case.execute(Caller(None), RegulationScope.PUBLIC, None, organization_filter)

    mock_regulations_repository.list_regulations.assert_awaited_once_with(
        mock_opened_session, None, None, organization_filter
    )


async def test_update_regulation_success(uuid_generator, mock_regulations_repository, mock_session_maker):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_result = MagicMock(spec=RegulationRepresentation)
    mock_regulations_repository.update_regulation_details.return_value = mock_result

    use_case = UpdateRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    result = await use_case.execute(
        Caller(user_id), regulation_id, RegulationDetailsData(name="New name", description="New description")
    )

    assert result == mock_result
    mock_regulations_repository.update_regulation_details.assert_awaited_once()
    assert mock_regulations_repository.update_regulation_details.await_args.args[1:] == (
        user_id,
        regulation_id,
        RegulationDetails(presentation_name="New name", description="New description"),
    )


async def test_update_regulation_not_found(uuid_generator, mock_regulations_repository, mock_session_maker):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_regulations_repository.update_regulation_details.side_effect = RegulationNotFound

    use_case = UpdateRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    with pytest.raises(RegulationNotFound):
        await use_case.execute(Caller(user_id), regulation_id, RegulationDetailsData(name="New name"))


async def test_delete_regulation_prepared_success(
    mock_session_maker,
    mock_regulations_repository,
    mock_sections_repo,
    mock_regulations_storage,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.PREPARED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    use_case = DeleteRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        sections_repository=mock_sections_repo,
        regulations_storage=mock_regulations_storage,
    )

    await use_case.execute(Caller(user_id), regulation_id)

    mock_sections_repo.remove_sections.assert_awaited_once()
    mock_regulations_repository.unregister_regulation.assert_awaited_once()
    mock_regulations_storage.delete_regulation.assert_awaited_once_with(regulation_id)


async def test_delete_regulation_not_prepared_success(
    mock_session_maker,
    mock_regulations_repository,
    mock_sections_repo,
    mock_regulations_storage,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    use_case = DeleteRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        sections_repository=mock_sections_repo,
        regulations_storage=mock_regulations_storage,
    )

    await use_case.execute(Caller(user_id), regulation_id)

    mock_sections_repo.remove_sections.assert_not_awaited()
    mock_regulations_repository.unregister_regulation.assert_awaited_once()
    mock_regulations_storage.delete_regulation.assert_awaited_once_with(regulation_id)


async def test_delete_regulation_not_found(
    mock_session_maker,
    mock_regulations_repository,
    mock_sections_repo,
    mock_regulations_storage,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_regulations_repository.get_regulation_representation.return_value = None

    use_case = DeleteRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        sections_repository=mock_sections_repo,
        regulations_storage=mock_regulations_storage,
    )

    with pytest.raises(RegulationNotFound):
        await use_case.execute(Caller(user_id), regulation_id)


async def test_delete_regulation_storage_error(
    mock_session_maker,
    mock_regulations_repository,
    mock_sections_repo,
    mock_regulations_storage,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.PREPARED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_regulations_storage.delete_regulation.side_effect = Exception("Storage error")

    use_case = DeleteRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        sections_repository=mock_sections_repo,
        regulations_storage=mock_regulations_storage,
    )

    # Should not raise exception
    await use_case.execute(Caller(user_id), regulation_id)

    mock_sections_repo.remove_sections.assert_awaited_once()
    mock_regulations_repository.unregister_regulation.assert_awaited_once()


async def test_search_file_success(
    mock_embedding_port,
    mock_sections_repo,
    mock_session_maker,
    uuid_generator,
    mock_opened_session,
    mock_regulations_repository,
):
    query = "test query"
    embedding_vector = [0.1, 0.2, 0.3]
    search_results = [
        {"id": "doc1", "text": "relevant document"},
        {"id": "doc2", "text": "another document"},
    ]

    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_embedding_port.embed_queries.return_value = [embedding_vector]
    mock_sections_repo.search.return_value = search_results

    search_params = SearchParams(threshold=0, limit=None, query=query)

    use_case = SearchRegulation(
        session_maker=mock_session_maker,
        embedding_port=mock_embedding_port,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
    )

    result = await use_case.execute(Caller(user_id), regulation_id, search_params)

    assert result == search_results
    mock_embedding_port.embed_queries.assert_awaited_once_with([query])
    mock_sections_repo.search.assert_awaited_once_with(
        mock_opened_session, user_id, regulation_id, embedding_vector, search_params
    )


async def test_search_file_no_results(
    mock_embedding_port,
    mock_sections_repo,
    mock_session_maker,
    uuid_generator,
    mock_opened_session,
    mock_regulations_repository,
):
    query = "unknown query"
    embedding_vector = [0.0, 0.0, 0.0]
    search_results = []

    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_embedding_port.embed_queries.return_value = [embedding_vector]
    mock_sections_repo.search.return_value = search_results

    search_params = SearchParams(threshold=0, limit=None, query=query)

    use_case = SearchRegulation(
        session_maker=mock_session_maker,
        embedding_port=mock_embedding_port,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
    )

    result = await use_case.execute(Caller(user_id), regulation_id, search_params)

    assert result == []
    mock_embedding_port.embed_queries.assert_awaited_once_with([query])
    mock_sections_repo.search.assert_awaited_once_with(
        mock_opened_session, user_id, regulation_id, embedding_vector, search_params
    )


async def test_search_file_embedding_error(
    mock_embedding_port, mock_session_maker, mock_sections_repo, uuid_generator, mock_regulations_repository
):
    query = "error query"
    mock_embedding_port.embed_queries.side_effect = Exception("Embedding service down")

    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    search_params = SearchParams(threshold=0, limit=None, query=query)

    use_case = SearchRegulation(
        session_maker=mock_session_maker,
        embedding_port=mock_embedding_port,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
    )

    with pytest.raises(Exception, match="Embedding service down"):
        await use_case.execute(Caller(user_id), regulation_id, search_params)

    mock_embedding_port.embed_queries.assert_awaited_once_with([query])
    mock_sections_repo.search.assert_not_awaited()


async def test_search_file_repository_error(
    mock_embedding_port,
    mock_sections_repo,
    mock_session_maker,
    uuid_generator,
    mock_opened_session,
    mock_regulations_repository,
):
    query = "repo error query"
    embedding_vector = [0.1, 0.1, 0.1]

    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    search_params = SearchParams(threshold=0, limit=None, query=query)

    mock_embedding_port.embed_queries.return_value = [embedding_vector]
    mock_sections_repo.search.side_effect = Exception("Database error")

    use_case = SearchRegulation(
        session_maker=mock_session_maker,
        embedding_port=mock_embedding_port,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
    )

    with pytest.raises(Exception, match="Database error"):
        await use_case.execute(Caller(user_id), regulation_id, search_params=search_params)


async def test_search_file_documents_not_found_but_regulation_not_found(
    mock_embedding_port,
    mock_sections_repo,
    mock_session_maker,
    uuid_generator,
    mock_regulations_repository,
):
    query = "query"
    embedding_vector = [0.1, 0.2, 0.3]
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_embedding_port.embed_queries.return_value = [embedding_vector]
    mock_sections_repo.search.side_effect = RegulationDocumentsNotFound
    mock_regulations_repository.get_regulation_representation.return_value = None

    search_params = SearchParams(threshold=0, limit=None, query=query)

    use_case = SearchRegulation(
        session_maker=mock_session_maker,
        embedding_port=mock_embedding_port,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
    )

    with pytest.raises(RegulationNotFound):
        await use_case.execute(Caller(user_id), regulation_id, search_params)


async def test_search_file_documents_not_found_not_prepared(
    mock_embedding_port,
    mock_sections_repo,
    mock_session_maker,
    uuid_generator,
    mock_regulations_repository,
):
    query = "query"
    embedding_vector = [0.1, 0.2, 0.3]
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_embedding_port.embed_queries.return_value = [embedding_vector]
    mock_sections_repo.search.side_effect = RegulationDocumentsNotFound

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    regulation_rep.presentation_name = "Doc"
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    search_params = SearchParams(threshold=0, limit=None, query=query)

    use_case = SearchRegulation(
        session_maker=mock_session_maker,
        embedding_port=mock_embedding_port,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
    )

    with pytest.raises(RegulationsNotPreparedToSearch):
        await use_case.execute(Caller(user_id), regulation_id, search_params)


async def test_search_file_documents_not_found_invalid_state(
    mock_embedding_port,
    mock_sections_repo,
    mock_session_maker,
    uuid_generator,
    mock_regulations_repository,
):
    query = "query"
    embedding_vector = [0.1, 0.2, 0.3]
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)

    mock_embedding_port.embed_queries.return_value = [embedding_vector]
    mock_sections_repo.search.side_effect = RegulationDocumentsNotFound

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.PREPARED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    search_params = SearchParams(threshold=0, limit=None, query=query)

    use_case = SearchRegulation(
        session_maker=mock_session_maker,
        embedding_port=mock_embedding_port,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
    )

    with pytest.raises(RegulationInInvalidState):
        await use_case.execute(Caller(user_id), regulation_id, search_params)


async def test_add_public_regulation_as_normal_user(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    regulation_data = RegulationData(scope=RegulationScope.PUBLIC, name="regulation.pdf")

    add_regulation = AddRegulation(
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        session_maker=mock_session_maker,
    )

    with pytest.raises(AccessForbidden):
        await add_regulation.execute(Caller(next(uuid_generator)), regulation_data)

    mock_regulations_repository.register_regulation.assert_not_awaited()


async def test_list_private_regulations_unlogged(mock_regulations_repository, mock_session_maker):
    use_case = ListRegulations(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    with pytest.raises(LoginRequired):
        await use_case.execute(Caller(None), RegulationScope.PRIVATE, None, None)

    mock_regulations_repository.list_regulations.assert_not_awaited()


async def test_get_other_user_private_regulation(uuid_generator, mock_regulations_repository, mock_session_maker):
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(next(uuid_generator))

    use_case = GetRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
    )

    with pytest.raises(RegulationNotFound):
        await use_case.execute(Caller(next(uuid_generator), is_admin=True), regulation_id)

    mock_regulations_repository.get_regulation_representation.assert_not_awaited()


async def test_delete_public_regulation_as_normal_user(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    regulation_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(None)

    use_case = DeleteRegulation(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        sections_repository=AsyncMock(),
        regulations_storage=mock_regulations_storage,
    )

    with pytest.raises(AccessForbidden):
        await use_case.execute(Caller(next(uuid_generator)), regulation_id)

    mock_regulations_repository.unregister_regulation.assert_not_awaited()
    mock_regulations_storage.delete_regulation.assert_not_awaited()


async def test_prepare_regulation_schedules_description_generation(
    mock_session_maker,
    mock_regulations_repository,
    mock_regulations_storage,
    mock_sections_repo,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    regulation_rep.description_status = RegulationDescriptionStatus.IN_PROGRESS
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_regulations_storage.get_regulation.return_value = b"content"
    mock_scheduler = AsyncMock()

    use_case = PrepareRegulation(
        session_maker=mock_session_maker,
        regulations_storage=mock_regulations_storage,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
        regulation_preparator=AsyncMock(),
        description_generation_scheduler=mock_scheduler,
    )

    await use_case.execute(user_id, regulation_id)

    mock_scheduler.schedule_regulation_description_generation.assert_awaited_once_with(
        mock_session_maker.begin.return_value.__aenter__.return_value, user_id, regulation_id
    )


async def test_prepare_regulation_without_description_generation(
    mock_session_maker,
    mock_regulations_repository,
    mock_regulations_storage,
    mock_sections_repo,
    uuid_generator,
):
    user_id = next(uuid_generator)
    regulation_id = next(uuid_generator)

    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.NOT_STARTED
    regulation_rep.description_status = RegulationDescriptionStatus.NOT_REQUESTED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    mock_regulations_storage.get_regulation.return_value = b"content"
    mock_scheduler = AsyncMock()

    use_case = PrepareRegulation(
        session_maker=mock_session_maker,
        regulations_storage=mock_regulations_storage,
        sections_repository=mock_sections_repo,
        regulations_repository=mock_regulations_repository,
        regulation_preparator=AsyncMock(),
        description_generation_scheduler=mock_scheduler,
    )

    await use_case.execute(user_id, regulation_id)

    mock_scheduler.schedule_regulation_description_generation.assert_not_awaited()


async def test_add_regulation_with_description_generation(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    mock_regulations_repository.register_regulation.return_value = next(uuid_generator)

    regulation_data = RegulationData(scope=RegulationScope.PUBLIC, name="regulation.pdf", generateDescription=True)

    add_regulation = AddRegulation(
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        session_maker=mock_session_maker,
    )

    await add_regulation.execute(Caller(next(uuid_generator), is_admin=True), regulation_data)

    registration_data = mock_regulations_repository.register_regulation.await_args.args[2]
    assert registration_data.description_status == RegulationDescriptionStatus.IN_PROGRESS


async def test_add_regulation_with_description_generation_as_normal_user(
    uuid_generator, mock_regulations_repository, mock_regulations_storage, mock_session_maker
):
    regulation_data = RegulationData(scope=RegulationScope.PRIVATE, name="regulation.pdf", generateDescription=True)

    add_regulation = AddRegulation(
        regulations_repository=mock_regulations_repository,
        regulations_storage=mock_regulations_storage,
        session_maker=mock_session_maker,
    )

    with pytest.raises(AccessForbidden):
        await add_regulation.execute(Caller(next(uuid_generator)), regulation_data)

    mock_regulations_repository.register_regulation.assert_not_awaited()


def create_generate_regulation_description(
    mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port
):
    mock_description_writer = AsyncMock()
    mock_description_writer.write.return_value = "Załatwianie typowych spraw przez studentów"

    use_case = GenerateRegulationDescription(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        sections_repository=mock_sections_repo,
        description_writer=mock_description_writer,
        texts_embedder=mock_embedding_port,
    )
    return use_case, mock_description_writer


async def test_generate_regulation_description_success(
    mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port, uuid_generator
):
    regulation_id = next(uuid_generator)

    regulation_rep = MagicMock()
    regulation_rep.presentation_name = "Regulamin studiów"
    regulation_rep.description_status = RegulationDescriptionStatus.IN_PROGRESS
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep
    mock_sections_repo.list_sections_contents.return_value = [
        SectionContent(header="Rozdział 1 Postanowienia ogólne > § 1", text="§ 1. Regulamin określa...")
    ]
    mock_embedding_port.embed_texts.return_value = [[0.1, 0.2]]

    use_case, mock_description_writer = create_generate_regulation_description(
        mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port
    )

    await use_case.execute(None, regulation_id)

    description_source = mock_description_writer.write.await_args.args[0]
    assert description_source.presentation_name == "Regulamin studiów"
    assert description_source.headings == ["Rozdział 1 Postanowienia ogólne"]
    mock_embedding_port.embed_texts.assert_awaited_once_with(["Załatwianie typowych spraw przez studentów"])
    mock_regulations_repository.set_generated_description.assert_awaited_once_with(
        mock_session_maker.begin.return_value.__aenter__.return_value,
        None,
        regulation_id,
        "Załatwianie typowych spraw przez studentów",
        [0.1, 0.2],
    )


async def test_generate_regulation_description_regulation_not_found(
    mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port, uuid_generator
):
    mock_regulations_repository.get_regulation_representation.return_value = None

    use_case, mock_description_writer = create_generate_regulation_description(
        mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port
    )

    await use_case.execute(None, next(uuid_generator))

    mock_description_writer.write.assert_not_awaited()


async def test_generate_regulation_description_already_generated(
    mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port, uuid_generator
):
    regulation_rep = MagicMock()
    regulation_rep.description_status = RegulationDescriptionStatus.GENERATED
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep

    use_case, mock_description_writer = create_generate_regulation_description(
        mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port
    )

    await use_case.execute(None, next(uuid_generator))

    mock_description_writer.write.assert_not_awaited()
    mock_regulations_repository.set_description_status.assert_not_awaited()


async def test_generate_regulation_description_service_unavailable(
    mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port, uuid_generator
):
    regulation_rep = MagicMock()
    regulation_rep.presentation_name = "Regulamin studiów"
    regulation_rep.description_status = RegulationDescriptionStatus.IN_PROGRESS
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep
    mock_sections_repo.list_sections_contents.return_value = []

    use_case, mock_description_writer = create_generate_regulation_description(
        mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port
    )
    mock_description_writer.write.side_effect = ServiceUnavailable()

    with pytest.raises(ServiceUnavailable):
        await use_case.execute(None, next(uuid_generator))

    assert get_set_description_statuses(mock_regulations_repository) == [
        RegulationDescriptionStatus.IN_PROGRESS,
        RegulationDescriptionStatus.FAILED,
    ]
    mock_regulations_repository.set_generated_description.assert_not_awaited()


async def test_generate_regulation_description_regulation_removed(
    mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port, uuid_generator
):
    regulation_rep = MagicMock()
    regulation_rep.presentation_name = "Regulamin studiów"
    regulation_rep.description_status = RegulationDescriptionStatus.IN_PROGRESS
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep
    mock_sections_repo.list_sections_contents.return_value = []
    mock_embedding_port.embed_texts.return_value = [[0.1, 0.2]]
    mock_regulations_repository.set_generated_description.side_effect = RegulationNotFound()

    use_case, _ = create_generate_regulation_description(
        mock_session_maker, mock_regulations_repository, mock_sections_repo, mock_embedding_port
    )

    await use_case.execute(None, next(uuid_generator))


async def test_fail_regulation_description_generation_deliveries_limit_exceeded(
    mock_session_maker, mock_regulations_repository, uuid_generator
):
    use_case = FailRegulationDescriptionGeneration(
        session_maker=mock_session_maker, regulations_repository=mock_regulations_repository
    )

    is_failed = await use_case.execute(None, next(uuid_generator), MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES + 1)

    assert is_failed
    assert get_set_description_statuses(mock_regulations_repository) == [RegulationDescriptionStatus.FAILED]


async def test_fail_regulation_description_generation_deliveries_limit_not_exceeded(
    mock_session_maker, mock_regulations_repository, uuid_generator
):
    use_case = FailRegulationDescriptionGeneration(
        session_maker=mock_session_maker, regulations_repository=mock_regulations_repository
    )

    is_failed = await use_case.execute(None, next(uuid_generator), MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES)

    assert not is_failed
    mock_regulations_repository.set_description_status.assert_not_awaited()


def create_regenerate_regulation_description(mock_session_maker, mock_regulations_repository, regulation_rep):
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(None)
    mock_regulations_repository.get_regulation_representation.return_value = regulation_rep
    mock_scheduler = AsyncMock()

    use_case = RegenerateRegulationDescription(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        description_generation_scheduler=mock_scheduler,
    )
    return use_case, mock_scheduler


async def test_regenerate_regulation_description_success(
    mock_session_maker, mock_regulations_repository, uuid_generator
):
    regulation_id = next(uuid_generator)
    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.PREPARED
    regulation_rep.description_status = RegulationDescriptionStatus.GENERATED

    use_case, mock_scheduler = create_regenerate_regulation_description(
        mock_session_maker, mock_regulations_repository, regulation_rep
    )

    await use_case.execute(Caller(next(uuid_generator), is_admin=True), regulation_id)

    assert get_set_description_statuses(mock_regulations_repository) == [RegulationDescriptionStatus.IN_PROGRESS]
    mock_scheduler.schedule_regulation_description_generation.assert_awaited_once_with(
        mock_session_maker.begin.return_value.__aenter__.return_value, None, regulation_id
    )


async def test_regenerate_regulation_description_as_normal_user(
    mock_session_maker, mock_regulations_repository, uuid_generator
):
    user_id = next(uuid_generator)
    mock_regulations_repository.get_regulation_owner.return_value = RegulationOwner(user_id)
    mock_scheduler = AsyncMock()

    use_case = RegenerateRegulationDescription(
        session_maker=mock_session_maker,
        regulations_repository=mock_regulations_repository,
        description_generation_scheduler=mock_scheduler,
    )

    with pytest.raises(AccessForbidden):
        await use_case.execute(Caller(user_id), next(uuid_generator))

    mock_scheduler.schedule_regulation_description_generation.assert_not_awaited()


async def test_regenerate_regulation_description_not_prepared(
    mock_session_maker, mock_regulations_repository, uuid_generator
):
    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.IN_PROGRESS

    use_case, mock_scheduler = create_regenerate_regulation_description(
        mock_session_maker, mock_regulations_repository, regulation_rep
    )

    with pytest.raises(RegulationInInvalidState):
        await use_case.execute(Caller(next(uuid_generator), is_admin=True), next(uuid_generator))

    mock_scheduler.schedule_regulation_description_generation.assert_not_awaited()


async def test_regenerate_regulation_description_already_in_progress(
    mock_session_maker, mock_regulations_repository, uuid_generator
):
    regulation_rep = MagicMock()
    regulation_rep.preparation_status = RegulationPreparationStatus.PREPARED
    regulation_rep.description_status = RegulationDescriptionStatus.IN_PROGRESS

    use_case, mock_scheduler = create_regenerate_regulation_description(
        mock_session_maker, mock_regulations_repository, regulation_rep
    )

    with pytest.raises(RegulationDescriptionGenerationInProgress):
        await use_case.execute(Caller(next(uuid_generator), is_admin=True), next(uuid_generator))

    mock_scheduler.schedule_regulation_description_generation.assert_not_awaited()


async def test_regenerate_regulation_description_not_found(
    mock_session_maker, mock_regulations_repository, uuid_generator
):
    use_case, _ = create_regenerate_regulation_description(mock_session_maker, mock_regulations_repository, None)

    with pytest.raises(RegulationNotFound):
        await use_case.execute(Caller(next(uuid_generator), is_admin=True), next(uuid_generator))
