from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchResultElement(BaseModel):
    text: str
    subsection: str | None


class SearchResultHighlight(BaseModel):
    start_element: int
    end_element: int


class SearchResult(BaseModel):
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    id: UUID
    score: float = Field(ge=-1, le=1)
    header: str | None = None
    text: str
    elements: list[SearchResultElement]
    highlight: SearchResultHighlight | None = None


class SearchOrder(StrEnum):
    DOCUMENT = "document"
    SCORE = "score"


class SearchParams(BaseModel):
    threshold: float = Field(ge=-1, le=1)
    limit: int | None = Field(default=None, gt=0)
    query: str
    order_by: SearchOrder = SearchOrder.DOCUMENT
