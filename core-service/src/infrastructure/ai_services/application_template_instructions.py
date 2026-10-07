import anyio

from src.infrastructure.ai_services.application_writer import PROMPTS_DIR


class PromptsApplicationTemplateInstructionsProvider:
    async def get_default_instructions(self) -> str:
        return await anyio.Path(PROMPTS_DIR / "application_template_instructions.md").read_text(encoding="utf-8")
