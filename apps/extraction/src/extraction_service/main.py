import tempfile
from contextlib import asynccontextmanager
from pathlib import Path
from shutil import copyfileobj
from typing import Annotated

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.backend_options import ThreadedDoclingParseBackendOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from fastapi import FastAPI, File, Request, UploadFile

from extraction_service.models import DocumentItem
from extraction_service.services import extract_document_items


@asynccontextmanager
async def lifespan(application: FastAPI):
    accelerator_options = AcceleratorOptions(device=AcceleratorDevice.CPU)

    pipeline_options = PdfPipelineOptions(
        accelerator_options=accelerator_options,
        ocr_options=RapidOcrOptions(backend="torch", lang=["iso:pl"]),
        ocr_batch_size=1,
        layout_batch_size=1,
        table_batch_size=1,
        queue_max_size=4,
    )

    application.state.converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_options,
                backend_options=ThreadedDoclingParseBackendOptions(parser_threads=2, max_concurrent_results=2),
            )
        }
    )
    application.state.converter.initialize_pipeline(InputFormat.PDF)
    yield


app = FastAPI(title="ExtractionService", lifespan=lifespan)


@app.post("/parse-regulation", response_model=list[DocumentItem])
def parse_pdf(file: Annotated[UploadFile, File(...)], request: Request) -> list[DocumentItem]:
    converter = request.app.state.converter
    with tempfile.TemporaryDirectory() as temp_dir:
        file_path = Path(temp_dir) / "document.pdf"
        with file_path.open("wb") as temp_file:
            copyfileobj(file.file, temp_file, length=1024 * 1024)
        result = converter.convert(file_path)

    texts = result.document.texts
    return extract_document_items(texts)


@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok"}
