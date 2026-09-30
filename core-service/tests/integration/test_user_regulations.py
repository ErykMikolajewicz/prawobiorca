from uuid import UUID

from fastapi import status
from sqlalchemy import insert, select

from src.app.dtos.regulations import RegulationUploadTarget
from src.domain.value_objects.regulations import RegulationPreparationStatus, RegulationType
from src.infrastructure.relational_db.schemas.regulations import regulations_table
from src.shared.consts import ACCESS_COOKIE_NAME
from tests.consts import ACCESS_TOKEN, USER_ID


async def test_add_user_regulation(
    client,
    override_session_maker,
    session_maker,
    override_get_regulations_storage,
    mock_regulations_storage,
    override_authorize_normal_user,
    set_user,
    clean_user,
):
    regulation_data = {"name": "user-regulation.pdf", "regulationType": RegulationType.ACT}

    mock_regulations_storage.get_upload_target.side_effect = lambda id_: RegulationUploadTarget(
        id=id_, url="http://storage.local/bucket", fields={"key": str(id_)}
    )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post("/api/user/regulations", json=regulation_data)

    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert "id" in response_json
    assert "url" in response_json
    assert "fields" in response_json
    regulation_id = UUID(response_json["id"])

    async with session_maker() as session:
        statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
        result = await session.execute(statement)
    regulation = result.one_or_none()

    assert regulation is not None
    assert regulation.user_id == USER_ID
    assert regulation.presentation_name == "user-regulation.pdf"
    assert regulation.preparation_status == RegulationPreparationStatus.NOT_STARTED
    assert regulation.regulation_type == RegulationType.ACT


async def test_delete_user_regulation(
    client,
    override_session_maker,
    session_maker,
    override_get_regulations_storage,
    mock_regulations_storage,
    override_authorize_normal_user,
    set_user,
    clean_user,
):
    async with session_maker.begin() as session:
        regulation_id = await session.scalar(
            insert(regulations_table)
            .values(
                user_id=USER_ID,
                presentation_name="do_usuniecia.pdf",
                regulation_type=RegulationType.ACT,
            )
            .returning(regulations_table.c.id)
        )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.delete(f"/api/user/regulations/{regulation_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    mock_regulations_storage.delete_regulation.assert_awaited_once_with(regulation_id)

    async with session_maker() as session:
        statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
        result = await session.execute(statement)
    deleted_regulation = result.one_or_none()

    assert deleted_regulation is None


async def test_confirm_user_regulation_upload(
    client,
    override_session_maker,
    session_maker,
    override_get_regulations_storage,
    mock_regulations_storage,
    override_get_regulations_preparation_scheduler,
    mock_regulation_preparation_scheduler,
    override_authorize_normal_user,
    set_user,
    clean_user,
):
    async with session_maker.begin() as session:
        regulation_id = await session.scalar(
            insert(regulations_table)
            .values(
                user_id=USER_ID,
                presentation_name="uploaded_but_unconfirmed.pdf",
                regulation_type=RegulationType.ACT,
            )
            .returning(regulations_table.c.id)
        )

    mock_regulations_storage.check_regulation_exists.return_value = True

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(f"/api/user/regulations/{regulation_id}/confirm-upload")

    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_regulations_storage.check_regulation_exists.assert_awaited_once_with(regulation_id)
    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_awaited_once_with(
        USER_ID, regulation_id
    )

    async with session_maker() as session:
        statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
        result = await session.execute(statement)
    regulation = result.one_or_none()

    assert regulation is not None
    assert regulation.preparation_status == RegulationPreparationStatus.IN_PROGRESS


async def test_confirm_user_regulation_upload_already_prepared(
    client,
    override_session_maker,
    session_maker,
    override_get_regulations_storage,
    override_get_regulations_preparation_scheduler,
    override_authorize_normal_user,
    set_user,
    clean_user,
):
    async with session_maker.begin() as session:
        regulation_id = await session.scalar(
            insert(regulations_table)
            .values(
                user_id=USER_ID,
                presentation_name="already_prepared.pdf",
                preparation_status=RegulationPreparationStatus.PREPARED,
                regulation_type=RegulationType.ACT,
            )
            .returning(regulations_table.c.id)
        )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(f"/api/user/regulations/{regulation_id}/confirm-upload")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Regulation is already prepared!"

    async with session_maker() as session:
        statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
        result = await session.execute(statement)
    regulation = result.one_or_none()

    assert regulation is not None
    assert regulation.preparation_status == RegulationPreparationStatus.PREPARED


async def test_confirm_user_regulation_upload_storage_missing(
    client,
    override_session_maker,
    session_maker,
    override_get_regulations_storage,
    mock_regulations_storage,
    override_get_regulations_preparation_scheduler,
    override_authorize_normal_user,
    set_user,
    clean_user,
):
    async with session_maker.begin() as session:
        regulation_id = await session.scalar(
            insert(regulations_table)
            .values(
                user_id=USER_ID,
                presentation_name="missing_in_storage.pdf",
                regulation_type=RegulationType.ACT,
            )
            .returning(regulations_table.c.id)
        )

    mock_regulations_storage.check_regulation_exists.return_value = False

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(f"/api/user/regulations/{regulation_id}/confirm-upload")

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "Regulation content not found in storage!"
    mock_regulations_storage.check_regulation_exists.assert_awaited_once_with(regulation_id)

    async with session_maker() as session:
        statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
        result = await session.execute(statement)
    regulation = result.one_or_none()

    assert regulation is not None
    assert regulation.preparation_status == RegulationPreparationStatus.NOT_STARTED


async def test_retry_user_regulation_preparation(
    client,
    override_session_maker,
    session_maker,
    override_get_regulations_preparation_scheduler,
    mock_regulation_preparation_scheduler,
    override_authorize_normal_user,
    set_user,
    clean_user,
):
    async with session_maker.begin() as session:
        regulation_id = await session.scalar(
            insert(regulations_table)
            .values(
                user_id=USER_ID,
                presentation_name="to_prepare.pdf",
                preparation_status=RegulationPreparationStatus.FAILED,
                regulation_type=RegulationType.ACT,
            )
            .returning(regulations_table.c.id)
        )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(f"/api/user/regulations/{regulation_id}/preparation-retry")

    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_awaited_once_with(
        USER_ID, regulation_id
    )

    async with session_maker() as session:
        statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
        result = await session.execute(statement)
    regulation = result.one_or_none()

    assert regulation is not None
    assert regulation.preparation_status == RegulationPreparationStatus.IN_PROGRESS


async def test_retry_user_regulation_preparation_already_prepared(
    client,
    override_session_maker,
    session_maker,
    override_get_regulations_preparation_scheduler,
    mock_regulation_preparation_scheduler,
    override_authorize_normal_user,
    set_user,
    clean_user,
):
    async with session_maker.begin() as session:
        regulation_id = await session.scalar(
            insert(regulations_table)
            .values(
                user_id=USER_ID,
                presentation_name="already_prepared_for_prep.pdf",
                preparation_status=RegulationPreparationStatus.PREPARED,
                regulation_type=RegulationType.ACT,
            )
            .returning(regulations_table.c.id)
        )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(f"/api/user/regulations/{regulation_id}/preparation-retry")

    assert response.status_code == status.HTTP_409_CONFLICT
    mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_not_awaited()
