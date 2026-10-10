from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from src.shared.consts import MAX_ORGANIZATION_NAME_LENGTH, MAX_ORGANIZATION_SHORT_NAME_LENGTH


class NewOrganization(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel)

    name: str = Field(min_length=1, max_length=MAX_ORGANIZATION_NAME_LENGTH)
    short_name: str = Field(min_length=1, max_length=MAX_ORGANIZATION_SHORT_NAME_LENGTH)


class NewSuborganization(BaseModel):
    name: str = Field(min_length=1, max_length=MAX_ORGANIZATION_NAME_LENGTH)


@dataclass
class SuborganizationData:
    id: UUID
    name: str


@dataclass(config=ConfigDict(alias_generator=to_camel, validate_by_name=True))
class OrganizationData:
    id: UUID
    name: str
    short_name: str
    suborganizations: list[SuborganizationData]
