from dataclasses import dataclass
from uuid import UUID


@dataclass
class OrganizationFilter:
    organization_id: UUID
    suborganization_id: UUID | None = None
