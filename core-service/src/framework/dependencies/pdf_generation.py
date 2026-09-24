import os

from fastapi import Depends

from src.app.interfaces.cases import CaseDocumentsRepository
from src.app.interfaces.pdf_generation import LLMClient, PDFRenderer
from src.app.interfaces.relational import SessionMaker
from src.app.use_cases.generate_pdf import GenerateCasePDF
from src.framework.dependencies.cases import get_case_documents_repo
from src.framework.dependencies.relational import get_session_maker
from src.infrastructure.ai.ollama_client import OllamaClient
from src.infrastructure.ai.openvino_client import OpenVINOClient
from src.infrastructure.pdf.html_renderer import HTMLToPDFRenderer


def get_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "openvino").lower()
    if provider in ("openvino", "openai"):
        return OpenVINOClient()
    return OllamaClient()


def get_pdf_renderer() -> PDFRenderer:
    return HTMLToPDFRenderer()


def get_generate_case_pdf_use_case(
    session_maker: SessionMaker = Depends(get_session_maker),
    case_documents_repo: CaseDocumentsRepository = Depends(get_case_documents_repo),
    llm_client: LLMClient = Depends(get_llm_client),
    pdf_renderer: PDFRenderer = Depends(get_pdf_renderer),
) -> GenerateCasePDF:
    return GenerateCasePDF(session_maker, case_documents_repo, llm_client, pdf_renderer)
