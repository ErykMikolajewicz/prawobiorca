from dataclasses import dataclass
from uuid import UUID

from src.app.dtos.applications import NewApplication
from src.app.interfaces.cases import CaseDocumentsRepository
from src.app.interfaces.relational import SessionMaker
from src.app.ports.applications import ApplicationRenderer, ApplicationWriter


@dataclass
class GenerateApplication:
    session_maker: SessionMaker
    case_documents_repo: CaseDocumentsRepository
    application_writer: ApplicationWriter
    application_renderer: ApplicationRenderer

    async def execute(self, user_id: UUID, case_id: UUID, new_application: NewApplication) -> bytes:
        async with self.session_maker() as session:
            legal_basis = await self.case_documents_repo.list_by_case_id(session, user_id, case_id)
        content = await self.application_writer.write(new_application, legal_basis)
        return await self.application_renderer.render(new_application, content)
