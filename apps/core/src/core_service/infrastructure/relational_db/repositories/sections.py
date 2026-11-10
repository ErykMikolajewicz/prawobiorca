from dataclasses import asdict
from itertools import batched
from typing import Any
from uuid import UUID

from sqlalchemy import Table, case, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession as SqlaAsyncSession

from core_service.application.dtos.search import (
    SearchOrder,
    SearchParams,
    SearchResult,
    SearchResultElement,
    SearchResultHighlight,
)
from core_service.application.ports.relational import AsyncSession
from core_service.domain.exceptions.documents import RegulationDocumentsNotFound
from core_service.domain.value_objects.regulations import SectionContent
from core_service.domain.value_objects.sections import SectionsCollection
from core_service.infrastructure.relational_db.schemas.sections import (
    regulations_chunks_table,
    regulations_sections_table,
)
from core_service.infrastructure.relational_db.session import sqla_session

PRIMARY_CHUNK_SCORE_WEIGHT = 0.8

SPAN_COLUMNS = ("span_start_element", "span_end_element")

INSERT_BATCH_SIZE = 1000


async def _insert_in_batches(session: SqlaAsyncSession, table: Table, rows: list[dict[str, Any]]) -> None:
    for batch in batched(rows, INSERT_BATCH_SIZE, strict=False):
        await session.execute(insert(table).values(list(batch)))


class SqlaSectionsRepository:
    @staticmethod
    async def add_sections(
        session: AsyncSession,
        user_id: UUID | None,
        regulation_id: UUID,
        sections: SectionsCollection,
    ) -> None:
        session = sqla_session(session)
        sections_data = []
        chunks_data = []
        for section in sections:
            sections_data.append(
                {
                    "id": section.id,
                    "header": section.header,
                    "text": section.text,
                    "section_order": section.section_order,
                    "elements": [asdict(element) for element in section.elements],
                    "regulation_id": regulation_id,
                    "user_id": user_id,
                }
            )
            chunks_data.extend(
                {
                    "id": chunk.id,
                    "section_id": section.id,
                    "chunk_index": chunk.chunk_index,
                    "text": chunk.text,
                    "vector": chunk.vector,
                    "span_start_element": chunk.span.start_element if chunk.span else None,
                    "span_end_element": chunk.span.end_element if chunk.span else None,
                }
                for chunk in section.chunks
            )

        await _insert_in_batches(session, regulations_sections_table, sections_data)
        await _insert_in_batches(session, regulations_chunks_table, chunks_data)

    @staticmethod
    async def list_sections_contents(
        session: AsyncSession, user_id: UUID | None, regulation_id: UUID
    ) -> list[SectionContent]:
        session = sqla_session(session)
        statement = (
            select(regulations_sections_table.c.header, regulations_sections_table.c.text)
            .where(
                regulations_sections_table.c.regulation_id == regulation_id,
                regulations_sections_table.c.user_id == user_id,
            )
            .order_by(regulations_sections_table.c.section_order)
        )
        result = await session.execute(statement)

        return [SectionContent(header=row.header, text=row.text) for row in result]

    @staticmethod
    async def search(
        session: AsyncSession,
        user_id: UUID | None,
        regulation_id: UUID,
        vector: list[float],
        search_params: SearchParams,
    ) -> list[SearchResult]:
        session = sqla_session(session)
        exists_query = (
            select(1)
            .where(
                regulations_sections_table.c.regulation_id == regulation_id,
                regulations_sections_table.c.user_id == user_id,
            )
            .limit(1)
        )
        exists_result = await session.execute(exists_query)
        if not exists_result.scalar():
            raise RegulationDocumentsNotFound()

        distance = regulations_chunks_table.c.vector.cosine_distance(vector)

        ranked_chunks = (
            select(
                regulations_chunks_table.c.section_id,
                (1 - distance).label("similarity"),
                *(regulations_chunks_table.c[column] for column in SPAN_COLUMNS),
                func.row_number()
                .over(partition_by=regulations_chunks_table.c.section_id, order_by=distance.asc())
                .label("chunk_rank"),
            )
            .select_from(
                regulations_chunks_table.join(
                    regulations_sections_table,
                    regulations_chunks_table.c.section_id == regulations_sections_table.c.id,
                )
            )
            .where(
                regulations_sections_table.c.regulation_id == regulation_id,
                regulations_sections_table.c.user_id == user_id,
            )
            .subquery()
        )

        primary_weight = PRIMARY_CHUNK_SCORE_WEIGHT
        secondary_weight = 1 - primary_weight

        best_similarity = func.max(case((ranked_chunks.c.chunk_rank == 1, ranked_chunks.c.similarity)))
        second_similarity = func.max(case((ranked_chunks.c.chunk_rank == 2, ranked_chunks.c.similarity)))
        score = case(
            (second_similarity.is_(None), best_similarity),
            else_=primary_weight * best_similarity + secondary_weight * second_similarity,
        )

        best_chunk_span = [
            func.max(case((ranked_chunks.c.chunk_rank == 1, ranked_chunks.c[column]))).label(column)
            for column in SPAN_COLUMNS
        ]

        scored_sections = (
            select(ranked_chunks.c.section_id, score.label("score"), *best_chunk_span)
            .where(ranked_chunks.c.chunk_rank <= 2)
            .group_by(ranked_chunks.c.section_id)
            .having(score >= search_params.threshold)
            .order_by(score.desc())
            .limit(search_params.limit)
            .subquery()
        )

        if search_params.order_by == SearchOrder.SCORE:
            result_order = scored_sections.c.score.desc()
        else:
            result_order = regulations_sections_table.c.section_order.asc()

        query = (
            select(
                regulations_sections_table.c.id,
                regulations_sections_table.c.header,
                regulations_sections_table.c.text,
                regulations_sections_table.c.elements,
                scored_sections.c.score,
                *(scored_sections.c[column] for column in SPAN_COLUMNS),
            )
            .select_from(
                regulations_sections_table.join(
                    scored_sections, scored_sections.c.section_id == regulations_sections_table.c.id
                )
            )
            .order_by(result_order)
        )

        result = await session.execute(query)
        rows = result.all()

        return [
            SearchResult(
                id=row.id,
                header=row.header,
                text=row.text,
                elements=[SearchResultElement(**element) for element in row.elements],
                score=row.score,
                highlight=SearchResultHighlight(
                    start_element=row.span_start_element,
                    end_element=row.span_end_element,
                )
                if row.span_start_element is not None
                else None,
            )
            for row in rows
        ]
