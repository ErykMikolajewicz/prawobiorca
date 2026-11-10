from fastapi.concurrency import run_in_threadpool

from core_service.infrastructure.ai_services.prompt_templates import PROMPTS_DIR


class PromptsApplicationTemplateInstructionsProvider:
    async def get_default_instructions(self) -> str:
        return await run_in_threadpool(
            (PROMPTS_DIR / "application_template_instructions.md").read_text, encoding="utf-8"
        )
