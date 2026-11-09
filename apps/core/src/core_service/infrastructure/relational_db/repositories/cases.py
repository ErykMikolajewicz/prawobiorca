from uuid import UUID

from pydantic import TypeAdapter
from sqlalchemy import delete, insert, select
from sqlalchemy.exc import IntegrityError

from core_service.application.dtos.cases import CaseData, CaseDocument, NewCaseDocument
from core_service.application.ports.relational import AsyncSession
from core_service.domain.exceptions.cases import CaseNotFound
from core_service.infrastructure.relational_db.schemas.cases import case_documents_table, cases_table
from core_service.infrastructure.relational_db.session import sqla_session


async def check_case_exists(session: AsyncSession, user_id: UUID, case_id: UUID) -> None:
    session = sqla_session(session)
    statement = select(cases_table.c.id).where(cases_table.c.id == case_id, cases_table.c.user_id == user_id)
    if await session.scalar(statement) is None:
        raise CaseNotFound


class SqlaCasesRepository:
    @staticmethod
    async def list_by_user_id(session: AsyncSession, user_id: UUID) -> list[CaseData]:
        session = sqla_session(session)
        statement = select(CaseData).where(cases_table.c.user_id == user_id).order_by(cases_table.c.create_date.desc())
        result = await session.scalars(statement)
        cases = list(result.all())
        return cases

    @staticmethod
    async def add(session: AsyncSession, user_id: UUID, case_name: str) -> UUID:
        session = sqla_session(session)
        statement = insert(cases_table).values(user_id=user_id, name=case_name).returning(cases_table.c.id)
        result = await session.execute(statement)
        case_id = result.scalar_one()
        return case_id

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID, case_id: UUID) -> None:
        session = sqla_session(session)
        statement = (
            delete(cases_table)
            .where(cases_table.c.id == case_id, cases_table.c.user_id == user_id)
            .returning(cases_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise CaseNotFound


class SqlaCaseDocumentsRepository:
    @staticmethod
    async def list_by_case_id(session: AsyncSession, user_id: UUID, case_id: UUID) -> list[CaseDocument]:
        session = sqla_session(session)
        statement = select(CaseDocument).where(
            case_documents_table.c.case_id == case_id, case_documents_table.c.user_id == user_id
        )
        result = await session.scalars(statement)
        case_documents = list(result.all())

        return case_documents

    @staticmethod
    async def add(session: AsyncSession, user_id: UUID, case_id: UUID, new_document: NewCaseDocument) -> UUID:
        session = sqla_session(session)
        await check_case_exists(session, user_id, case_id)
        statement = (
            insert(case_documents_table)
            .values(case_id=case_id, user_id=user_id, **TypeAdapter(NewCaseDocument).dump_python(new_document))
            .returning(case_documents_table.c.id)
        )
        try:
            result = await session.execute(statement)
        except IntegrityError:
            raise CaseNotFound
        case_article_id = result.scalar_one()
        return case_article_id

    @staticmethod
    async def delete(session: AsyncSession, user_id: UUID, case_id: UUID, article_id: UUID) -> None:
        session = sqla_session(session)
        statement = (
            delete(case_documents_table)
            .where(
                case_documents_table.c.id == article_id,
                case_documents_table.c.case_id == case_id,
                case_documents_table.c.user_id == user_id,
            )
            .returning(case_documents_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise CaseNotFound
