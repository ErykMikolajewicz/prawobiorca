from pathlib import Path

from jinja2 import Environment, FileSystemLoader

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

    async def write(self, new_application: NewApplication, legal_basis: list[CaseDocument]) -> str:
        system_prompt = prompts_env.get_template(f"applications/{new_application.application_type.lower()}.md").render(
            user_name=new_application.user_name,
            student_id=new_application.student_id,
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
