import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from fastapi import FastAPI, File, Request, UploadFile

from src.models import DocumentItem
from src.services import extract_document_items


@asynccontextmanager
async def lifespan(application: FastAPI):
    accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU)

    pipeline_options = PdfPipelineOptions()
    pipeline_options.accelerator_options = accelerator_options

    application.state.converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )
    application.state.converter.initialize_pipeline(InputFormat.PDF)
    yield


app = FastAPI(title="ExtractionService", lifespan=lifespan)


@app.post("/parse-regulation", response_model=list[DocumentItem])
def parse_pdf(file: Annotated[UploadFile, File(...)], request: Request) -> list[DocumentItem]:
    converter = request.app.state.converter
    with tempfile.NamedTemporaryFile("wb", suffix=".pdf", delete=False) as temp_file:
        file_content = file.file.read()
        temp_file.write(file_content)
        file_path = Path(temp_file.name)

    try:
        result = converter.convert(file_path)
    finally:
        file_path.unlink()

    texts = result.document.texts
    return extract_document_items(texts)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
