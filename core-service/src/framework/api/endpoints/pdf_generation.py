import io
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from src.app.dtos.user import StudentData
from src.app.use_cases.generate_pdf import GenerateCasePDF
from src.domain.exceptions.cases import LLMGenerationError
from src.framework.dependencies.authentication import require_logged_user
from src.framework.dependencies.pdf_generation import get_generate_case_pdf_use_case

logger = logging.getLogger("app.pdf")

pdf_router = APIRouter(tags=["pdf"], dependencies=(Depends(require_logged_user),), prefix="/api")


class GenerateCasePDFRequest(BaseModel):
    description: str
    case_id: UUID = Field(alias="caseId")
    user_name: str = Field(default="Student PWr", alias="userName")
    student_id: str = Field(default="000000", alias="studentId")
    department: str = Field(default="Wydział Informatyki i Telekomunikacji")
    semester: str = Field(default="4")
    title: str = Field(default="inż.")

    model_config = ConfigDict(populate_by_name=True)


@pdf_router.post("/case/generate-pdf")
async def generate_case_pdf(
    request_data: GenerateCasePDFRequest,
    user_id: Annotated[UUID, Depends(require_logged_user)],
    generate_case_pdf_use_case: Annotated[GenerateCasePDF, Depends(get_generate_case_pdf_use_case)],
):
    logger.info(f"Rozpoczęto generowanie PDF dla sprawy {request_data.case_id}")

    student_data = StudentData(
        user_id=user_id,
        user_name=request_data.user_name,
        student_id=request_data.student_id,
        department=request_data.department,
        semester=request_data.semester,
        title=request_data.title,
    )

    # zapisywanie plików poza kodem źródłowym backendu, aby uniknąć restartów w trybie dev-reload
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    # BASE_DIR = prawobiorca/core-service/src/framework/api/endpoints ->  prawobiorca/core-service
    base_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    wnioski_dir = base_dir / "storage" / "wnioski"
    os.makedirs(wnioski_dir, exist_ok=True)

    temp_pdf_path = os.path.join(wnioski_dir, f"wniosek_{timestamp}_{request_data.case_id}.pdf")

    try:
        pdf_path = await generate_case_pdf_use_case.execute(
            case_id=request_data.case_id,
            description=request_data.description,
            student_data=student_data,
            output_path=temp_pdf_path,
        )
    except LLMGenerationError as e:
        logger.error(f"Błąd generowania tekstu przez LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Błąd generowania tekstu: {str(e)}")
    except Exception as e:
        logger.error(f"Nieoczekiwany błąd generowania wniosku PDF: {e}")
        raise HTTPException(status_code=500, detail="Wystąpił nieoczekiwany błąd serwera podczas kompilacji PDF.")

    logger.info(f"PDF wyrenderowany pomyślnie i zapisany w: {pdf_path}")

    with open(pdf_path, "rb") as f:
        pdf_content = f.read()

    # zwracanie strumienia pliku pdf do frontendu
    return StreamingResponse(
        io.BytesIO(pdf_content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=wniosek_{request_data.case_id}.pdf"},
    )
