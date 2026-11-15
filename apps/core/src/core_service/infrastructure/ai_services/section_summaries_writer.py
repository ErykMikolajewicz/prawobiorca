import logging
import re

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from core_service.domain.consts import MAX_SECTION_SUMMARY_LABEL_LENGTH, MAX_SECTION_SUMMARY_LENGTH
from core_service.domain.value_objects.sections import SectionSummariesBatch, SectionSummary
from core_service.infrastructure.ai_services.llm_chat import LlmChat
from core_service.infrastructure.ai_services.prompt_templates import prompts_env
from core_service.shared.exceptions import ServiceUnavailable

logger = logging.getLogger(__name__)

SECTION_SUMMARIES_MAX_TOKENS = 2000

CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$")


class GeneratedSectionSummary(BaseModel):
    number: int = Field(alias="numer")
    label: str = Field(alias="etykieta")
    summary: str = Field(alias="opis")


generated_summaries_adapter = TypeAdapter(list[GeneratedSectionSummary])


class LlmSectionSummariesWriter:
    def __init__(self, llm_chat: LlmChat):
        self._llm_chat = llm_chat

    async def write(self, batch: SectionSummariesBatch) -> list[SectionSummary]:
        system_prompt = prompts_env.get_template("section_summaries.md").render(
            chapter=batch.chapter,
            sections=batch.sections,
        )
        user_prompt = "Podaj etykiety i opisy przepisów."

        response = await self._llm_chat.generate_text(system_prompt, user_prompt, SECTION_SUMMARIES_MAX_TOKENS)

        try:
            generated_summaries = generated_summaries_adapter.validate_json(CODE_FENCE_PATTERN.sub("", response))
        except ValidationError as e:
            raise ServiceUnavailable() from e

        sections_by_number = dict(enumerate(batch.sections, start=1))
        summaries = [
            SectionSummary(
                section_id=sections_by_number[generated.number].id,
                label=generated.label.strip()[:MAX_SECTION_SUMMARY_LABEL_LENGTH],
                summary=generated.summary.strip()[:MAX_SECTION_SUMMARY_LENGTH],
            )
            for generated in generated_summaries
            if generated.number in sections_by_number
        ]

        if len(summaries) < len(batch.sections):
            logger.warning("LLM summarized %s of %s sections!", len(summaries), len(batch.sections))

        return summaries
