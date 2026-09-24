from dataclasses import dataclass
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True)
class CreateUserData:
    username: str
    hashed_password: bytes


class StudentData(BaseModel):
    user_id: UUID = Field(alias="userId")
    user_name: str = Field(alias="userName")
    student_id: str = Field(pattern=r"^\d{6}$", alias="studentId")
    department: str = Field(default="Wydział Informatyki i Telekomunikacji")
    semester: str = Field(default="4")
    title: str = Field(default="inż.")

    model_config = ConfigDict(populate_by_name=True)
