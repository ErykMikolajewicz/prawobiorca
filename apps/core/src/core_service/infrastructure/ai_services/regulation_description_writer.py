from core_service.domain.consts import MAX_REGULATION_DESCRIPTION_LENGTH
from core_service.domain.value_objects.regulations import RegulationDescriptionSource
from core_service.infrastructure.ai_services.llm_chat import LlmChat
from core_service.infrastructure.ai_services.prompt_templates import prompts_env


class LlmRegulationDescriptionWriter:
    def __init__(self, llm_chat: LlmChat):
        self._llm_chat = llm_chat

    async def write(self, description_source: RegulationDescriptionSource) -> str:
        system_prompt = prompts_env.get_template("regulation_description.md").render(
            presentation_name=description_source.presentation_name,
            headings=description_source.headings,
            beginning=description_source.beginning,
        )
        user_prompt = "Podaj opis dokumentu."

        description = await self._llm_chat.generate_text(system_prompt, user_prompt)

        return description[:MAX_REGULATION_DESCRIPTION_LENGTH]
