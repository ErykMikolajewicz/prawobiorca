from src.domain.value_objects.application_templates import ApplicationTemplateDescriptionSource
from src.infrastructure.ai_services.llm_chat import LlmChat
from src.infrastructure.ai_services.prompt_templates import prompts_env
from src.shared.consts import MAX_APPLICATION_TEMPLATE_DESCRIPTION_LENGTH


class ApplicationTemplateDescriptionWriter:
    def __init__(self, llm_chat: LlmChat):
        self._llm_chat = llm_chat

    async def write(self, description_source: ApplicationTemplateDescriptionSource) -> str:
        system_prompt = prompts_env.get_template("application_template_description.md").render(
            name=description_source.name,
            instructions=description_source.instructions,
            field_labels=description_source.field_labels,
            content=description_source.content,
        )
        user_prompt = "Podaj opis szablonu."

        description = await self._llm_chat.generate_text(system_prompt, user_prompt)

        return description[:MAX_APPLICATION_TEMPLATE_DESCRIPTION_LENGTH]
