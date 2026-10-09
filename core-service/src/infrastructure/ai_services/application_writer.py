from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from src.app.dtos.application_templates import ApplicationTemplateRepresentation
from src.app.dtos.applications import NewApplication
from src.app.dtos.cases import CaseDocument
from src.infrastructure.ai_services.llm_chat import LlmChat

PROMPTS_DIR = Path(__file__).parent / "prompts"

prompts_env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    autoescape=False,  # noqa: S701
    trim_blocks=True,
    lstrip_blocks=True,
)


class ApplicationWriter:
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
                f"{field.label}: {new_application.field_values[field.name]}"
                for field in template.fields
                if field.pass_to_ai and new_application.field_values.get(field.name)
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
