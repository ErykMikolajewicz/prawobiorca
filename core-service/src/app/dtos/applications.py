from pydantic import ConfigDict, Field
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from src.domain.value_objects.applications import ApplicationType


@dataclass(config=ConfigDict(alias_generator=to_camel))
class NewApplication:
    description: str = Field(min_length=1)
    user_name: str = Field(min_length=1)
    student_id: str = Field(pattern=r"^\d{6}$")
    department: str = Field(min_length=1)
    semester: str = Field(min_length=1)
    title: str = Field()
    application_type: ApplicationType = Field(default=ApplicationType.OTHER)
