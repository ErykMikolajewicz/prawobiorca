from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Response, status

from src.app.dtos.applications import NewApplication
from src.app.dtos.cases import CaseData, CaseDocument, NewCaseDocument
from src.app.use_cases.applications import GenerateApplication
from src.app.use_cases.cases import (
    AddCase,
    AddCaseDocument,
    DeleteCase,
    DeleteCaseDocument,
    ListCaseDocuments,
    ListCases,
)
from src.domain.exceptions.cases import CaseNotFound
from src.framework.dependencies.applications import get_generate_application
from src.framework.dependencies.authentication import authorize_user, require_logged_user
from src.framework.dependencies.cases import (
    get_add_case_document,
    get_add_user_case,
    get_delete_case_document,
    get_delete_user_case,
    get_list_case_documents,
    get_list_user_cases,
)

cases_router = APIRouter(tags=["cases"], dependencies=(Depends(authorize_user),), prefix="/api")


@cases_router.get(
    "/user/cases",
    response_model=list[CaseData],
)
async def get_cases_list(
    list_cases: Annotated[ListCases, Depends(get_list_user_cases)],
    user_id: Annotated[UUID, Depends(require_logged_user)],
) -> list[CaseData]:
    return await list_cases.execute(user_id)


@cases_router.post("/user/cases")
async def add_case(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    add_user_case_: Annotated[AddCase, Depends(get_add_user_case)],
    case_name: Annotated[str, Form(..., alias="caseName")],
) -> UUID:
    case_id = await add_user_case_.execute(user_id, case_name)
    return case_id


@cases_router.delete(
    "/user/cases/{caseId}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No case with that id!"},
    },
)
async def delete_user_case(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    delete_user_case_: Annotated[DeleteCase, Depends(get_delete_user_case)],
    case_id: Annotated[UUID, Path(alias="caseId")],
):
    try:
        await delete_user_case_.execute(user_id, case_id)
    except CaseNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No case with that id!")


@cases_router.post(
    "/user/cases/{caseId}/documents",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "No case with that id!"},
    },
)
async def add_case_document(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    add_case_document_: Annotated[AddCaseDocument, Depends(get_add_case_document)],
    case_id: Annotated[UUID, Path(alias="caseId")],
    new_document: NewCaseDocument,
):
    try:
        await add_case_document_.execute(user_id, case_id, new_document)
    except CaseNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No case with that id!")


@cases_router.get(
    "/user/cases/{caseId}/documents",
    response_model=list[CaseDocument],
)
async def get_case_documents(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    list_case_documents: Annotated[ListCaseDocuments, Depends(get_list_case_documents)],
    case_id: Annotated[UUID, Path(alias="caseId")],
) -> list[CaseDocument]:
    return await list_case_documents.execute(user_id, case_id)


@cases_router.delete("/user/cases/documents/{documentId}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_case_document(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    delete_case_document_: Annotated[DeleteCaseDocument, Depends(get_delete_case_document)],
    document_id: Annotated[UUID, Path(alias="documentId")],
):
    await delete_case_document_.execute(user_id, document_id)


@cases_router.post(
    "/user/cases/{caseId}/application",
    response_class=Response,
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
                    "schema": {"type": "string", "format": "binary"}
                }
            }
        },
        status.HTTP_503_SERVICE_UNAVAILABLE: {"description": "Service unavailable!"},
    },
)
async def generate_application(
    user_id: Annotated[UUID, Depends(require_logged_user)],
    generate_application_: Annotated[GenerateApplication, Depends(get_generate_application)],
    case_id: Annotated[UUID, Path(alias="caseId")],
    new_application: NewApplication,
) -> Response:
    document = await generate_application_.execute(user_id, case_id, new_application)
    return Response(
        content=document,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename=wniosek_{case_id}.docx"},
    )
