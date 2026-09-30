from enum import StrEnum
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field

from src.domain.value_objects.legal_units import UnitType


class SearchResultElement(BaseModel):
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    text: str
    subsection: str | None = None


class SearchResultHighlight(BaseModel):
    start_element: int
    start_offset: int
    end_element: int
    end_offset: int


class SearchResult(BaseModel):
    model_config = ConfigDict(json_schema_serialization_defaults_required=True)

    id: UUID
    score: float = Field(ge=-1, le=1)
    header: str | None = None
    text: str
    unit_type: UnitType | None = None
    unit_number: str | None = None
    unit_path: list[str] | None = None
    elements: list[SearchResultElement] | None = None
    highlight: SearchResultHighlight | None = None


class SearchOrder(StrEnum):
    DOCUMENT = "document"
    SCORE = "score"


class SearchParams(BaseModel):
    threshold: float = Query(ge=-1, le=1)
    limit: int | None = Query(default=None, gt=0)
    query: str = Query()
    order_by: SearchOrder = Query(default=SearchOrder.DOCUMENT)
