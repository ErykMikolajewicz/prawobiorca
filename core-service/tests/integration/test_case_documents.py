from fastapi import status
from sqlalchemy import insert, select

from src.infrastructure.relational_db.schemas.cases import case_documents_table, cases_table
from src.shared.consts import ACCESS_COOKIE_NAME
from tests.consts import ACCESS_TOKEN, ADMIN_ID, USER_ID


async def test_add_case_document(
    client, override_session_maker, session_maker, override_authorize_normal_user, set_user, clean_user
):
    async with session_maker.begin() as session:
        statement = (
            insert(cases_table)
            .values(
                {"user_id": USER_ID, "name": "Case with document"},
            )
            .returning(cases_table.c.id)
        )
        case_id = await session.scalar(statement)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.post(
        f"/api/user/cases/{case_id}/documents",
        json={"presentationName": "document.pdf", "content": "Document content", "header": "Art. 1"},
    )

    assert response.status_code == status.HTTP_201_CREATED

    async with session_maker() as session:
        statement = select(case_documents_table).where(case_documents_table.c.case_id == case_id)
        result = await session.execute(statement)
    case_document = result.one_or_none()

    assert case_document is not None
    assert case_document.case_id == case_id
    assert case_document.user_id == USER_ID
    assert case_document.presentation_name == "document.pdf"
    assert case_document.content == "Document content"
    assert case_document.header == "Art. 1"


async def test_delete_case_document(
    client, override_session_maker, session_maker, override_authorize_normal_user, set_user, clean_user
):
    async with session_maker.begin() as session:
        create_case_stmt = (
            insert(cases_table)
            .values(
                {"user_id": USER_ID, "name": "Case with document to delete"},
            )
            .returning(cases_table.c.id)
        )
        case_id = await session.scalar(create_case_stmt)

        create_document_stmt = (
            insert(case_documents_table)
            .values(
                {
                    "case_id": case_id,
                    "user_id": USER_ID,
                    "presentation_name": "document-to-delete.pdf",
                    "content": "Document content to delete",
                }
            )
            .returning(case_documents_table.c.id)
        )
        document_id = await session.scalar(create_document_stmt)

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.delete(f"/api/user/cases/documents/{document_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    async with session_maker() as session:
        statement = select(case_documents_table).where(case_documents_table.c.id == document_id)
        result = await session.execute(statement)
    deleted_document = result.one_or_none()

    assert deleted_document is None


async def test_get_case_documents(
    client,
    override_session_maker,
    session_maker,
    override_authorize_normal_user,
    set_user,
    clean_user,
    set_admin_user,
    clean_admin_user,
):
    async with session_maker.begin() as session:
        create_cases_stmt = (
            insert(cases_table)
            .values(
                [
                    {"user_id": USER_ID, "name": "Case with documents"},
                    {"user_id": USER_ID, "name": "Other user case"},
                ]
            )
            .returning(cases_table.c.id)
        )
        target_case_id, other_case_id = (await session.scalars(create_cases_stmt)).all()

        create_documents_stmt = (
            insert(case_documents_table)
            .values(
                [
                    {
                        "case_id": target_case_id,
                        "user_id": USER_ID,
                        "presentation_name": "first-document.pdf",
                        "content": "First document content",
                        "header": "Art. 1",
                    },
                    {
                        "case_id": target_case_id,
                        "user_id": USER_ID,
                        "presentation_name": "second-document.pdf",
                        "content": "Second document content",
                        "header": None,
                    },
                    {
                        "case_id": other_case_id,
                        "user_id": USER_ID,
                        "presentation_name": "other-case-document.pdf",
                        "content": "Other case document content",
                        "header": None,
                    },
                    {
                        "case_id": target_case_id,
                        "user_id": ADMIN_ID,
                        "presentation_name": "other-user-document.pdf",
                        "content": "Other user document content",
                        "header": None,
                    },
                ]
            )
            .returning(case_documents_table.c.id)
        )
        first_document_id, second_document_id, _, _ = (await session.scalars(create_documents_stmt)).all()

    client.cookies.set(ACCESS_COOKIE_NAME, ACCESS_TOKEN)

    response = await client.get(f"/api/user/cases/{target_case_id}/documents")

    assert response.status_code == status.HTTP_200_OK
    assert sorted(response.json(), key=lambda document: document["presentationName"]) == [
        {
            "id": str(first_document_id),
            "caseId": str(target_case_id),
            "presentationName": "first-document.pdf",
            "content": "First document content",
            "header": "Art. 1",
        },
        {
            "id": str(second_document_id),
            "caseId": str(target_case_id),
            "presentationName": "second-document.pdf",
            "content": "Second document content",
            "header": None,
        },
    ]
