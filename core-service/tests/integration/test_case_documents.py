from fastapi import status
from sqlalchemy import select

from src.infrastructure.relational_db.schemas.cases import case_documents_table
from tests.consts import ADMIN_ID, USER_ID
from tests.integration.fixtures.cases import insert_case, insert_case_document


async def test_add_case_document(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)

    response = await user_client.post(
        f"/api/cases/{case_id}/documents",
        json={
            "presentationName": "document.pdf",
            "content": "Document content",
            "header": "Art. 1",
            "elements": [{"text": "Document content", "subsection": "1."}],
            "highlight": {"start_element": 0, "end_element": 0},
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    async with session_maker() as session:
        result = await session.execute(select(case_documents_table).where(case_documents_table.c.case_id == case_id))
    case_document = result.one()

    assert case_document.user_id == USER_ID
    assert case_document.presentation_name == "document.pdf"
    assert case_document.content == "Document content"
    assert case_document.header == "Art. 1"
    assert case_document.elements == [{"text": "Document content", "subsection": "1."}]
    assert case_document.highlight == {"start_element": 0, "end_element": 0}


async def test_delete_case_document(user_client, session_maker):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        document_id = await insert_case_document(session, case_id)

    response = await user_client.delete(f"/api/cases/{case_id}/documents/{document_id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    async with session_maker() as session:
        deleted_document = await session.scalar(
            select(case_documents_table.c.id).where(case_documents_table.c.id == document_id)
        )

    assert deleted_document is None


async def test_get_case_documents(user_client, session_maker, admin):
    async with session_maker.begin() as session:
        case_id = await insert_case(session)
        other_case_id = await insert_case(session, name="Other case")

        first_document_id = await insert_case_document(
            session, case_id, presentation_name="first-document.pdf", content="First content", header="Art. 1"
        )
        second_document_id = await insert_case_document(
            session, case_id, presentation_name="second-document.pdf", content="Second content"
        )
        await insert_case_document(session, other_case_id, presentation_name="other-case-document.pdf")
        await insert_case_document(session, case_id, ADMIN_ID, presentation_name="other-user-document.pdf")

    response = await user_client.get(f"/api/cases/{case_id}/documents")

    assert response.status_code == status.HTTP_200_OK
    assert sorted(response.json(), key=lambda document: document["presentationName"]) == [
        {
            "id": str(first_document_id),
            "caseId": str(case_id),
            "presentationName": "first-document.pdf",
            "content": "First content",
            "header": "Art. 1",
            "elements": [],
            "highlight": None,
        },
        {
            "id": str(second_document_id),
            "caseId": str(case_id),
            "presentationName": "second-document.pdf",
            "content": "Second content",
            "header": None,
            "elements": [],
            "highlight": None,
        },
    ]
