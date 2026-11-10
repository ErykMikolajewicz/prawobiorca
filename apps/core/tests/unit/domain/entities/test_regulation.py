from uuid import UUID

import pytest

from core_service.domain.entities.regulation import Regulation
from core_service.domain.exceptions.descriptions import DescriptionGenerationInProgress
from core_service.domain.exceptions.regulations import (
    RegulationAlreadyInitialized,
    RegulationInInvalidState,
    RegulationPreparationInProgress,
)
from core_service.domain.value_objects.descriptions import DescriptionStatus
from core_service.domain.value_objects.regulations import RegulationDetails, RegulationPreparationStatus

REGULATION_ID = UUID("5c1d2e3f-4a5b-4c6d-8e7f-9a0b1c2d3e4f")


def create_regulation(
    preparation_status: RegulationPreparationStatus = RegulationPreparationStatus.NOT_STARTED,
    description_status: DescriptionStatus = DescriptionStatus.NOT_REQUESTED,
) -> Regulation:
    return Regulation(
        id=REGULATION_ID,
        presentation_name="Regulamin studiów",
        preparation_status=preparation_status,
        description_status=description_status,
    )


def test_confirm_upload_starts_preparation():
    regulation = create_regulation()

    regulation.confirm_upload()

    assert regulation.preparation_status == RegulationPreparationStatus.IN_PROGRESS


@pytest.mark.parametrize(
    ("preparation_status", "error"),
    [
        (RegulationPreparationStatus.PREPARED, RegulationAlreadyInitialized),
        (RegulationPreparationStatus.IN_PROGRESS, RegulationPreparationInProgress),
        (RegulationPreparationStatus.FAILED, RegulationInInvalidState),
    ],
)
def test_confirm_upload_rejected(preparation_status, error):
    regulation = create_regulation(preparation_status)

    with pytest.raises(error):
        regulation.confirm_upload()

    assert regulation.preparation_status == preparation_status


def test_retry_preparation_starts_preparation():
    regulation = create_regulation(RegulationPreparationStatus.FAILED)

    regulation.retry_preparation()

    assert regulation.preparation_status == RegulationPreparationStatus.IN_PROGRESS


@pytest.mark.parametrize(
    ("preparation_status", "error"),
    [
        (RegulationPreparationStatus.PREPARED, RegulationAlreadyInitialized),
        (RegulationPreparationStatus.IN_PROGRESS, RegulationPreparationInProgress),
        (RegulationPreparationStatus.NOT_STARTED, RegulationInInvalidState),
    ],
)
def test_retry_preparation_rejected(preparation_status, error):
    regulation = create_regulation(preparation_status)

    with pytest.raises(error):
        regulation.retry_preparation()

    assert regulation.preparation_status == preparation_status


@pytest.mark.parametrize(
    "preparation_status",
    [
        RegulationPreparationStatus.NOT_STARTED,
        RegulationPreparationStatus.IN_PROGRESS,
        RegulationPreparationStatus.FAILED,
    ],
)
def test_start_preparation(preparation_status):
    regulation = create_regulation(preparation_status)

    regulation.start_preparation()

    assert regulation.preparation_status == RegulationPreparationStatus.IN_PROGRESS


def test_start_preparation_of_prepared_regulation():
    regulation = create_regulation(RegulationPreparationStatus.PREPARED)

    with pytest.raises(RegulationAlreadyInitialized):
        regulation.start_preparation()


def test_preparation_result():
    prepared_regulation = create_regulation(RegulationPreparationStatus.IN_PROGRESS)
    failed_regulation = create_regulation(RegulationPreparationStatus.IN_PROGRESS)

    prepared_regulation.complete_preparation()
    failed_regulation.fail_preparation()

    assert prepared_regulation.is_prepared
    assert failed_regulation.preparation_status == RegulationPreparationStatus.FAILED


def test_preparation_result_of_prepared_regulation():
    regulation = create_regulation(RegulationPreparationStatus.PREPARED)

    with pytest.raises(RegulationAlreadyInitialized):
        regulation.complete_preparation()
    with pytest.raises(RegulationAlreadyInitialized):
        regulation.fail_preparation()

    assert regulation.is_prepared


@pytest.mark.parametrize(
    "description_status", [DescriptionStatus.NOT_REQUESTED, DescriptionStatus.GENERATED, DescriptionStatus.FAILED]
)
def test_request_description(description_status):
    regulation = create_regulation(RegulationPreparationStatus.PREPARED, description_status)

    regulation.request_description()

    assert regulation.is_description_in_progress


@pytest.mark.parametrize(
    ("preparation_status", "description_status", "error"),
    [
        (RegulationPreparationStatus.IN_PROGRESS, DescriptionStatus.NOT_REQUESTED, RegulationInInvalidState),
        (RegulationPreparationStatus.PREPARED, DescriptionStatus.IN_PROGRESS, DescriptionGenerationInProgress),
    ],
    ids=("not prepared", "generation in progress"),
)
def test_request_description_rejected(preparation_status, description_status, error):
    regulation = create_regulation(preparation_status, description_status)

    with pytest.raises(error):
        regulation.request_description()


def test_description_generation():
    generated_regulation = create_regulation(description_status=DescriptionStatus.FAILED)
    failed_regulation = create_regulation(description_status=DescriptionStatus.GENERATED)

    generated_regulation.start_description_generation()
    generated_regulation.complete_description_generation("Opis regulaminu.")
    failed_regulation.start_description_generation()
    failed_regulation.fail_description_generation()

    assert generated_regulation.is_description_generated
    assert generated_regulation.description == "Opis regulaminu."
    assert failed_regulation.description_status == DescriptionStatus.FAILED


def test_update_details():
    regulation = create_regulation()

    regulation.update_details(RegulationDetails(presentation_name="Nowy regulamin", description="Opis."))

    assert regulation.presentation_name == "Nowy regulamin"
    assert regulation.description == "Opis."
