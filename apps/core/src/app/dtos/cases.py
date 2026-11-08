from uuid import UUID

from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from src.app.dtos.search import SearchResultElement, SearchResultHighlight
from src.shared.consts import MAX_FILENAME_LENGTH, MIN_FILENAME_LENGTH


@dataclass(config=ConfigDict(alias_generator=to_camel))
class NewCaseDocument:
    presentation_name: str = Field(min_length=1)
    content: str = Field(min_length=1)
    header: str | None = None
    elements: list[SearchResultElement] = Field(default_factory=list)
    highlight: SearchResultHighlight | None = None


@dataclass
class CaseData:
    id: UUID
    name: str


@dataclass(config=ConfigDict(alias_generator=to_camel, json_schema_serialization_defaults_required=True))
class CaseDocument:
    id: UUID
    case_id: UUID
    presentation_name: str = Field(min_length=MIN_FILENAME_LENGTH, max_length=MAX_FILENAME_LENGTH)
    content: str = Field(min_length=1)
    header: str | None = None
    elements: list[SearchResultElement] = Field(default_factory=list)
    highlight: SearchResultHighlight | None = None
