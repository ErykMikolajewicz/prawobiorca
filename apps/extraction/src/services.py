from docling.datamodel.document import TextItem

from src.models import DocumentItem


def extract_document_items(documents: list[TextItem]) -> list[DocumentItem]:
    return [DocumentItem(label=document.label, text=document.orig) for document in documents]
