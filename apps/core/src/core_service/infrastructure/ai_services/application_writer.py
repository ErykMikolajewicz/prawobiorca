from core_service.application.dtos.application_templates import ApplicationTemplateRepresentation
from core_service.application.dtos.applications import NewApplication
from core_service.application.dtos.cases import CaseDocument
from core_service.domain.services.application_fields import get_ai_field_values
from core_service.infrastructure.ai_services.llm_chat import LlmChat
from core_service.infrastructure.ai_services.prompt_templates import prompts_env


class LlmApplicationWriter:
    def __init__(self, llm_chat: LlmChat):
        self._llm_chat = llm_chat

    async def write(
        self,
        new_application: NewApplication,
        template: ApplicationTemplateRepresentation,
        legal_basis: list[CaseDocument],
    ) -> str:
        system_prompt = prompts_env.get_template("application.md").render(
            instructions=template.instructions,
            application_fields=[
                f"{label}: {value}"
                for label, value in get_ai_field_values(template.fields, new_application.field_values)
            ],
            situation_description=new_application.description,
            pinned_articles=[f"{document.presentation_name}: {document.content}" for document in legal_basis],
        )
        user_prompt = "Napisz formalne pismo na podstawie powyższych informacji."

        return await self._llm_chat.generate_text(system_prompt, user_prompt)

    async def write_name(self, new_application: NewApplication) -> str:
        system_prompt = prompts_env.get_template("application_name.md").render(
            situation_description=new_application.description,
        )
        user_prompt = "Podaj nazwę wniosku."

        return await self._llm_chat.generate_text(system_prompt, user_prompt)
