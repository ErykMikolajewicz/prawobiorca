from dataclasses import asdict
from uuid import UUID

from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.dtos.cases import CaseData, CaseDocument, NewCaseDocument
from src.domain.exceptions.cases import CaseNotFound
from src.infrastructure.relational_db.schemas.cases import case_documents_table, cases_table


class CasesRepository:
    @staticmethod
    async def list_by_user_id(session: AsyncSession, user_id: UUID) -> list[CaseData]:
        statement = select(CaseData).where(cases_table.c.user_id == user_id).order_by(cases_table.c.create_date.desc())
        result = await session.scalars(statement)
        cases = result.all()
        return cases

    @staticmethod
    async def add(session: AsyncSession, user_id: UUID, case_name: str) -> UUID:
        statement = insert(cases_table).values(user_id=user_id, name=case_name).returning(cases_table.c.id)
        result = await session.execute(statement)
        case_id = result.scalar_one()
        return case_id

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID, case_id: UUID) -> None:
        statement = delete(cases_table).where(cases_table.c.id == case_id, cases_table.c.user_id == user_id)
        await session.execute(statement)


class CaseDocumentsRepository:
    @staticmethod
    async def list_by_case_id(session: AsyncSession, user_id: UUID, case_id: UUID) -> list[CaseDocument]:
        statement = select(CaseDocument).where(
            case_documents_table.c.case_id == case_id, case_documents_table.c.user_id == user_id
        )
        result = await session.scalars(statement)
        case_documents = result.all()

        return case_documents

    @staticmethod
    async def add(session: AsyncSession, user_id: UUID, case_id: UUID, new_document: NewCaseDocument) -> UUID:
        statement = (
            insert(case_documents_table)
            .values(case_id=case_id, user_id=user_id, **asdict(new_document))
            .returning(case_documents_table.c.id)
        )
        try:
            result = await session.execute(statement)
        except IntegrityError:
            raise CaseNotFound
        case_article_id = result.scalar_one()
        return case_article_id

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID, article_id: UUID) -> None:
        statement = (
            delete(case_documents_table)
            .where(case_documents_table.c.id == article_id, case_documents_table.c.user_id == user_id)
            .returning(case_documents_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise CaseNotFound
