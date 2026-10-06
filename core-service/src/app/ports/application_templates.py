from typing import Protocol


class ApplicationTemplateInspector(Protocol):
    async def get_variables(self, template: bytes) -> set[str]: ...
