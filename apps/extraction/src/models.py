from pydantic import BaseModel


class DocumentItem(BaseModel):
    label: str
    text: str
