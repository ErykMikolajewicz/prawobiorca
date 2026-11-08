from collections.abc import Iterable
from typing import Protocol

from src.domain.value_objects.legal_units import RegulationElement
from src.domain.value_objects.regulations import RegulationDescriptionSource


class RegulationSplitter(Protocol):
    async def split(self, regulation: bytes) -> Iterable[RegulationElement]: ...


class RegulationDescriptionWriter(Protocol):
    async def write(self, description_source: RegulationDescriptionSource) -> str: ...
