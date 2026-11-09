from uuid import UUID

from core_service.domain.entities.application import Application
from core_service.domain.value_objects.applications import ApplicationGenerationStatus

APPLICATION_ID = UUID("2c3d4e5f-6a7b-4c8d-9e0f-1a2b3c4d5e6f")
CASE_ID = UUID("4b5c6d7e-8f9a-4b0c-9d1e-2f3a4b5c6d7e")


def test_complete_generation():
    application = Application(id=APPLICATION_ID, case_id=CASE_ID, generation_status=ApplicationGenerationStatus.FAILED)

    application.start_generation()
    application.complete_generation("Wniosek o urlop dziekański")

    assert application.is_generated
    assert application.name == "Wniosek o urlop dziekański"


def test_fail_generation():
    application = Application(id=APPLICATION_ID, case_id=CASE_ID)

    application.fail_generation()

    assert not application.is_generated
    assert application.generation_status == ApplicationGenerationStatus.FAILED
