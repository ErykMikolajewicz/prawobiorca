from typing import Protocol

from src.app.dtos.applications import NewApplication
from src.app.dtos.cases import CaseDocument


class ApplicationWriter(Protocol):
    async def write(self, new_application: NewApplication, legal_basis: list[CaseDocument]) -> str: ...


class ApplicationRenderer(Protocol):
    async def render(self, new_application: NewApplication, content: str) -> bytes: ...
