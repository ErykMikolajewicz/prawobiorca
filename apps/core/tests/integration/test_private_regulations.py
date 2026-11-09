from uuid import UUID

from fastapi import status
from sqlalchemy import select

from core_service.application.dtos.regulations import RegulationUploadTarget
from core_service.domain.value_objects.regulations import RegulationPreparationStatus, RegulationType
from core_service.infrastructure.relational_db.schemas.regulations import regulations_table
from core_service.infrastructure.tasks.regulations import REGULATION_PREPARATION_TASK_NAME
from tests.consts import ADMIN_ID, UNKNOWN_ID, USER_ID
from tests.integration.fixtures.ai_services import DESCRIPTION_VECTOR, QUERY_VECTOR, UNRELATED_VECTOR
from tests.integration.fixtures.regulations import insert_regulation
from tests.integration.fixtures.tasks import get_scheduled_task_names


async def get_regulation(session_maker, regulation_id):
    async with session_maker() as session:
        result = await session.execute(select(regulations_table).where(regulations_table.c.id == regulation_id))
    return result.one_or_none()


async def test_add_private_regulation(user_client, session_maker, mock_regulations_storage):
    mock_regulations_storage.get_upload_target.side_effect = lambda id_: RegulationUploadTarget(
        id=id_, url="http://storage.local/bucket", fields={"key": str(id_)}
    )

    response = await user_client.post(
        "/api/regulations",
        json={"scope": "PRIVATE", "name": "user-regulation.pdf", "regulationType": RegulationType.ACT},
    )

    assert response.status_code == status.HTTP_201_CREATED
    regulation = await get_regulation(session_maker, UUID(response.json()["id"]))

    assert regulation.user_id == USER_ID
    assert regulation.presentation_name == "user-regulation.pdf"
    assert regulation.regulation_type == RegulationType.ACT


async def test_add_private_regulation_with_organization(user_client):
    response = await user_client.post(
        "/api/regulations",
        json={"scope": "PRIVATE", "name": "user-regulation.pdf", "organizationId": str(UNKNOWN_ID)},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


async def test_add_public_regulation_as_normal_user(user_client):
    response = await user_client.post("/api/regulations", json={"scope": "PUBLIC", "name": "public.pdf"})

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_get_private_regulations(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID)
        await insert_regulation(session, None)

    response = await user_client.get("/api/regulations", params={"scope": "PRIVATE"})

    assert response.status_code == status.HTTP_200_OK
    assert [regulation["id"] for regulation in response.json()] == [str(regulation_id)]


async def test_get_private_regulations_unlogged(client):
    response = await client.get("/api/regulations", params={"scope": "PRIVATE"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_search_private_regulations(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID, description_vector=QUERY_VECTOR)
        await insert_regulation(session, None, description_vector=QUERY_VECTOR)

    response = await user_client.get(
        "/api/regulations/search", params={"scope": "PRIVATE", "query": "zapytanie", "threshold": 0.5}
    )

    assert response.status_code == status.HTTP_200_OK
    assert [result["regulation"]["id"] for result in response.json()] == [str(regulation_id)]


async def test_search_private_regulations_unlogged(client):
    response = await client.get(
        "/api/regulations/search", params={"scope": "PRIVATE", "query": "zapytanie", "threshold": 0.5}
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_get_other_user_private_regulation(user_client, session_maker, admin):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, ADMIN_ID)

    response = await user_client.get(f"/api/regulations/{regulation_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_get_private_regulation_download_url(user_client, session_maker, mock_regulations_storage):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID)
    mock_regulations_storage.get_download_url.return_value = "http://storage.local/bucket/regulation"

    response = await user_client.get(f"/api/regulations/{regulation_id}/download-url")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "http://storage.local/bucket/regulation"
    mock_regulations_storage.get_download_url.assert_awaited_once_with(regulation_id)


async def test_update_private_regulation(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID)

    response = await user_client.patch(
        f"/api/regulations/{regulation_id}", json={"name": "renamed-regulation.pdf", "description": "Opis regulacji"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["presentationName"] == "renamed-regulation.pdf"
    assert response.json()["description"] == "Opis regulacji"

    regulation = await get_regulation(session_maker, regulation_id)

    assert regulation.presentation_name == "renamed-regulation.pdf"
    assert regulation.description == "Opis regulacji"


async def test_update_private_regulation_description_recalculates_description_vector(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(
            session, USER_ID, description="Opis", description_vector=UNRELATED_VECTOR
        )

    response = await user_client.patch(
        f"/api/regulations/{regulation_id}", json={"name": "regulation.pdf", "description": "Opis"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert list((await get_regulation(session_maker, regulation_id)).description_vector) == UNRELATED_VECTOR

    response = await user_client.patch(
        f"/api/regulations/{regulation_id}", json={"name": "regulation.pdf", "description": "Nowy opis"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert list((await get_regulation(session_maker, regulation_id)).description_vector) == DESCRIPTION_VECTOR

    response = await user_client.patch(f"/api/regulations/{regulation_id}", json={"name": "regulation.pdf"})

    assert response.status_code == status.HTTP_200_OK
    assert (await get_regulation(session_maker, regulation_id)).description_vector is None


async def test_update_private_regulation_not_found(user_client):
    response = await user_client.patch(f"/api/regulations/{UNKNOWN_ID}", json={"name": "renamed-regulation.pdf"})

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_delete_private_regulation(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID)

    response = await user_client.delete(f"/api/regulations/{regulation_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert await get_regulation(session_maker, regulation_id) is None


async def test_delete_other_user_private_regulation_as_admin(admin_client, session_maker, user):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID)

    response = await admin_client.delete(f"/api/regulations/{regulation_id}")

    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_confirm_private_regulation_upload(user_client, session_maker, mock_regulations_storage):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID)
    mock_regulations_storage.check_regulation_exists.return_value = True

    response = await user_client.post(f"/api/regulations/{regulation_id}/confirm-upload")

    assert response.status_code == status.HTTP_202_ACCEPTED
    regulation = await get_regulation(session_maker, regulation_id)
    assert regulation.preparation_status == RegulationPreparationStatus.IN_PROGRESS
    assert await get_scheduled_task_names(session_maker) == [REGULATION_PREPARATION_TASK_NAME]


async def test_confirm_private_regulation_upload_already_prepared(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(
            session, USER_ID, preparation_status=RegulationPreparationStatus.PREPARED
        )

    response = await user_client.post(f"/api/regulations/{regulation_id}/confirm-upload")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Regulation is already prepared!"


async def test_confirm_private_regulation_upload_content_not_found(
    user_client, session_maker, mock_regulations_storage
):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID)
    mock_regulations_storage.check_regulation_exists.return_value = False

    response = await user_client.post(f"/api/regulations/{regulation_id}/confirm-upload")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Regulation content not found in storage!"


async def test_retry_private_regulation_preparation(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, USER_ID, preparation_status=RegulationPreparationStatus.FAILED)

    response = await user_client.post(f"/api/regulations/{regulation_id}/preparation-retry")

    assert response.status_code == status.HTTP_202_ACCEPTED
    regulation = await get_regulation(session_maker, regulation_id)
    assert regulation.preparation_status == RegulationPreparationStatus.IN_PROGRESS
    assert await get_scheduled_task_names(session_maker) == [REGULATION_PREPARATION_TASK_NAME]


async def test_retry_private_regulation_preparation_already_prepared(user_client, session_maker):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(
            session, USER_ID, preparation_status=RegulationPreparationStatus.PREPARED
        )

    response = await user_client.post(f"/api/regulations/{regulation_id}/preparation-retry")

    assert response.status_code == status.HTTP_409_CONFLICT
