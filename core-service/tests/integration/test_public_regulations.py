import math
from uuid import UUID

import pytest
from fastapi import status
from sqlalchemy import delete, insert, select

from src.app.dtos.regulations import RegulationUploadTarget
from src.domain.value_objects.legal_units import UnitType
from src.domain.value_objects.regulations import RegulationPreparationStatus, RegulationType
from src.framework.dependencies.ai_services import get_texts_embedder
from src.infrastructure.relational_db.repositories.sections import PRIMARY_CHUNK_SCORE_WEIGHT
from src.infrastructure.relational_db.schemas.regulations import regulations_table
from src.infrastructure.relational_db.schemas.sections import (
    regulations_chunks_table,
    regulations_sections_table,
)
from src.main import prawobiorca
from src.shared.consts import ACCESS_COOKIE_NAME, VECTOR_LENGTH
from tests.consts import ACCESS_TOKEN, USER_ID


async def test_get_public_regulations(client, override_session_maker, session_maker, set_user, clean_user):
    async with session_maker.begin() as session:
        statement = (
            insert(regulations_table)
            .values(
                [
                    {
                        "user_id": None,
                        "presentation_name": "Public act.pdf",
                        "preparation_status": RegulationPreparationStatus.PREPARED,
                        "regulation_type": RegulationType.ACT,
                    },
                    {
                        "user_id": None,
                        "presentation_name": "Public decree.pdf",
                        "preparation_status": RegulationPreparationStatus.NOT_STARTED,
                        "regulation_type": RegulationType.DECREE,
                    },
                    {
                        "user_id": USER_ID,
                        "presentation_name": "Private act.pdf",
                        "preparation_status": RegulationPreparationStatus.PREPARED,
                        "regulation_type": RegulationType.ACT,
                    },
                ]
            )
            .returning(regulations_table.c.id)
        )

        result = await session.scalars(statement)

    regulations_ids = result.all()
    public_act_id, public_decree_id, private_act_id = regulations_ids

    try:
        response = await client.get("/api/regulations", params={"documentType": RegulationType.ACT})

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                "id": str(public_act_id),
                "presentationName": "Public act.pdf",
                "regulationType": RegulationType.ACT,
                "preparationStatus": RegulationPreparationStatus.PREPARED,
            }
        ]

    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id.in_(regulations_ids)))


class StubTextsEmbedder:
    @staticmethod
    async def embed_queries(queries):
        return [[1.0] * VECTOR_LENGTH]


QUERY_VECTOR = [1.0] * VECTOR_LENGTH
UNRELATED_VECTOR = [1.0, *[0.0] * (VECTOR_LENGTH - 1)]
UNRELATED_SIMILARITY = 1 / math.sqrt(VECTOR_LENGTH)


async def insert_regulation(session, user_id, presentation_name):
    return await session.scalar(
        insert(regulations_table)
        .values(
            {
                "user_id": user_id,
                "presentation_name": presentation_name,
                "preparation_status": RegulationPreparationStatus.PREPARED,
                "regulation_type": RegulationType.ACT,
            }
        )
        .returning(regulations_table.c.id)
    )


async def insert_section(session, regulation_id, user_id, unit_number, text, section_order, chunk_vectors):
    section_id = await session.scalar(
        insert(regulations_sections_table)
        .values(
            {
                "header": f"Rozdział 5 Pracownicy uczelni > Art. {unit_number}",
                "text": text,
                "section_order": section_order,
                "unit_type": UnitType.ARTICLE,
                "unit_number": unit_number,
                "unit_path": ["Rozdział 5 Pracownicy uczelni"],
                "regulation_id": regulation_id,
                "user_id": user_id,
            }
        )
        .returning(regulations_sections_table.c.id)
    )

    await session.execute(
        insert(regulations_chunks_table).values(
            [
                {
                    "section_id": section_id,
                    "chunk_index": chunk_index,
                    "text": f"{text} chunk {chunk_index}",
                    "vector": vector,
                    "span_start_element": chunk_index,
                    "span_start_offset": 0,
                    "span_end_element": chunk_index,
                    "span_end_offset": 10,
                }
                for chunk_index, vector in enumerate(chunk_vectors)
            ]
        )
    )

    return section_id


async def test_search_regulations_documents(client, override_session_maker, session_maker, set_user, clean_user):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()

    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public searchable regulation.pdf")
        other_regulation_id = await insert_regulation(session, USER_ID, "User searchable regulation.pdf")

        matching_section_id = await insert_section(
            session, regulation_id, None, "112", "Matching public regulation section", 0, [QUERY_VECTOR]
        )
        await insert_section(
            session, regulation_id, None, "114", "Unrelated public regulation section", 1, [UNRELATED_VECTOR]
        )
        await insert_section(
            session, other_regulation_id, USER_ID, "113", "Matching user regulation section", 0, [QUERY_VECTOR]
        )

    try:
        response = await client.get(
            f"/api/regulations/{regulation_id}/documents",
            params={"threshold": 0.9, "limit": 10, "query": "public document query"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == [
            {
                "id": str(matching_section_id),
                "score": pytest.approx(1.0),
                "header": "Rozdział 5 Pracownicy uczelni > Art. 112",
                "text": "Matching public regulation section",
                "unit_type": UnitType.ARTICLE,
                "unit_number": "112",
                "unit_path": ["Rozdział 5 Pracownicy uczelni"],
                "elements": None,
                "highlight": {"start_element": 0, "start_offset": 0, "end_element": 0, "end_offset": 10},
            }
        ]
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)
        async with session_maker.begin() as session:
            await session.execute(
                delete(regulations_table).where(regulations_table.c.id.in_([regulation_id, other_regulation_id]))
            )


async def test_search_scores_section_by_its_two_best_chunks(
    client, override_session_maker, session_maker, set_user, clean_user
):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()

    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public multi chunk regulation.pdf")

        single_chunk_section_id = await insert_section(
            session, regulation_id, None, "112", "Single chunk section", 0, [QUERY_VECTOR]
        )
        multi_chunk_section_id = await insert_section(
            session,
            regulation_id,
            None,
            "113",
            "Multi chunk section",
            1,
            [QUERY_VECTOR, UNRELATED_VECTOR, UNRELATED_VECTOR],
        )

    expected_score = PRIMARY_CHUNK_SCORE_WEIGHT * 1.0 + (1 - PRIMARY_CHUNK_SCORE_WEIGHT) * UNRELATED_SIMILARITY

    try:
        response = await client.get(
            f"/api/regulations/{regulation_id}/documents",
            params={"threshold": 0.5, "limit": 10, "query": "public document query"},
        )

        assert response.status_code == status.HTTP_200_OK
        results_by_id = {result["id"]: result["score"] for result in response.json()}

        assert results_by_id[str(single_chunk_section_id)] == pytest.approx(1.0)
        assert results_by_id[str(multi_chunk_section_id)] == pytest.approx(expected_score)
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_search_highlights_best_chunk_of_section(
    client, override_session_maker, session_maker, set_user, clean_user
):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()

    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public highlighted regulation.pdf")

        await insert_section(
            session,
            regulation_id,
            None,
            "112",
            "Highlighted section",
            0,
            [UNRELATED_VECTOR, QUERY_VECTOR, UNRELATED_VECTOR],
        )

    try:
        response = await client.get(
            f"/api/regulations/{regulation_id}/documents",
            params={"threshold": 0.5, "limit": 10, "query": "public document query"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()[0]["highlight"] == {
            "start_element": 1,
            "start_offset": 0,
            "end_element": 1,
            "end_offset": 10,
        }
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


@pytest.mark.parametrize(
    ("order_by", "expected_numbers"),
    [
        ("document", ["112", "113"]),
        ("score", ["113", "112"]),
    ],
)
async def test_search_orders_results(
    client, override_session_maker, session_maker, set_user, clean_user, order_by, expected_numbers
):
    prawobiorca.dependency_overrides[get_texts_embedder] = lambda: StubTextsEmbedder()

    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Public ordered regulation.pdf")

        await insert_section(
            session, regulation_id, None, "112", "Lower score section", 0, [QUERY_VECTOR, UNRELATED_VECTOR]
        )
        await insert_section(session, regulation_id, None, "113", "Higher score section", 1, [QUERY_VECTOR])

    try:
        response = await client.get(
            f"/api/regulations/{regulation_id}/documents",
            params={"threshold": 0.5, "limit": 10, "query": "public document query", "order_by": order_by},
        )

        assert response.status_code == status.HTTP_200_OK
        assert [result["unit_number"] for result in response.json()] == expected_numbers
    finally:
        prawobiorca.dependency_overrides.pop(get_texts_embedder, None)
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_add_public_regulation_as_admin(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_regulations_storage,
    mock_regulations_storage,
):
    regulation_data = {"name": "public-regulation.pdf", "regulationType": RegulationType.DECREE}

    mock_regulations_storage.get_upload_target.side_effect = lambda id_: RegulationUploadTarget(
        id=id_, url="http://storage.local/bucket", fields={"key": str(id_)}
    )

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post("/api/regulations", json=regulation_data)

    assert response.status_code == status.HTTP_201_CREATED

    response_json = response.json()
    assert "id" in response_json
    assert "url" in response_json
    assert "fields" in response_json
    regulation_id = UUID(response_json["id"])

    try:
        async with session_maker() as session:
            statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
            result = await session.execute(statement)
        regulation = result.one_or_none()

        assert regulation is not None
        assert regulation.user_id is None
        assert regulation.presentation_name == "public-regulation.pdf"
        assert regulation.preparation_status == RegulationPreparationStatus.NOT_STARTED
        assert regulation.regulation_type == RegulationType.DECREE
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))


async def test_confirm_public_regulation_upload_as_admin(
    client,
    override_session_maker,
    session_maker,
    override_authorize_admin_user,
    override_get_regulations_storage,
    mock_regulations_storage,
    override_get_regulations_preparation_scheduler,
    mock_regulation_preparation_scheduler,
):
    async with session_maker.begin() as session:
        regulation_id = await session.scalar(
            insert(regulations_table)
            .values(
                user_id=None,
                presentation_name="public_confirm.pdf",
                regulation_type=RegulationType.ACT,
            )
            .returning(regulations_table.c.id)
        )

    mock_regulations_storage.check_regulation_exists.return_value = True

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    try:
        response = await client.post(f"/api/regulations/{regulation_id}/confirm-upload")

        assert response.status_code == status.HTTP_202_ACCEPTED
        mock_regulations_storage.check_regulation_exists.assert_awaited_once_with(regulation_id)
        mock_regulation_preparation_scheduler.schedule_regulation_preparation.assert_awaited_once_with(
            None, regulation_id
        )

        async with session_maker() as session:
            statement = select(regulations_table).where(regulations_table.c.id == regulation_id)
            result = await session.execute(statement)
        regulation = result.one_or_none()

        assert regulation is not None
        assert regulation.preparation_status == RegulationPreparationStatus.IN_PROGRESS
    finally:
        async with session_maker.begin() as session:
            await session.execute(delete(regulations_table).where(regulations_table.c.id == regulation_id))
