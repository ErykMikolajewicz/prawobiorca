from unittest.mock import create_autospec
from uuid import UUID

import pytest

from core_service.application.dtos.applications import NewApplication
from core_service.application.dtos.cases import CaseDocument
from core_service.domain.consts import MAX_APPLICATION_TEMPLATE_DESCRIPTION_LENGTH, MAX_REGULATION_DESCRIPTION_LENGTH
from core_service.domain.entities.application_template import ApplicationTemplate
from core_service.domain.value_objects.application_templates import (
    ApplicationTemplateDescriptionSource,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from core_service.domain.value_objects.regulations import RegulationDescriptionSource, RegulationHeading
from core_service.infrastructure.ai_services.application_template_description_writer import (
    LlmApplicationTemplateDescriptionWriter,
)
from core_service.infrastructure.ai_services.application_writer import LlmApplicationWriter
from core_service.infrastructure.ai_services.llm_chat import LlmChat
from core_service.infrastructure.ai_services.regulation_description_writer import LlmRegulationDescriptionWriter
from tests.mocks import get_awaited_argument

TEMPLATE_ID = UUID("6f7a8b9c-0d1e-4f2a-8b3c-4d5e6f7a8b9c")
CASE_ID = UUID("4b5c6d7e-8f9a-4b0c-9d1e-2f3a4b5c6d7e")

NEW_APPLICATION = NewApplication(
    template_id=TEMPLATE_ID,
    description="Proszę o urlop dziekański z powodu choroby.",
    field_values={"student_id": "123456", "pesel": "90010112345"},
)

TEMPLATE = ApplicationTemplate(
    id=TEMPLATE_ID,
    name="Wniosek o urlop",
    status=ApplicationTemplateStatus.PUBLISHED,
    fields=[
        ApplicationTemplateField(name="student_id", label="Numer albumu"),
        ApplicationTemplateField(name="pesel", label="PESEL", pass_to_ai=False),
    ],
    instructions="Sporządź wniosek do dziekana.",
)

CASE_DOCUMENT = CaseDocument(
    id=UUID("5d6e7f8a-9b0c-4d1e-8f2a-3b4c5d6e7f8a"),
    case_id=CASE_ID,
    presentation_name="Regulamin studiów",
    content="§ 20. Student może otrzymać urlop dziekański.",
)


@pytest.fixture
def llm_chat():
    llm_chat = create_autospec(LlmChat)
    llm_chat.generate_text.return_value = "Odpowiedź."
    return llm_chat


async def test_application_prompt_contains_application_data_allowed_for_ai(llm_chat):
    await LlmApplicationWriter(llm_chat).write(NEW_APPLICATION, TEMPLATE, [CASE_DOCUMENT])

    system_prompt = get_awaited_argument(llm_chat.generate_text, "system_prompt")
    assert "Sporządź wniosek do dziekana." in system_prompt
    assert "Numer albumu: 123456" in system_prompt
    assert "Proszę o urlop dziekański z powodu choroby." in system_prompt
    assert "Regulamin studiów: § 20. Student może otrzymać urlop dziekański." in system_prompt
    assert "90010112345" not in system_prompt
    assert get_awaited_argument(llm_chat.generate_text, "user_prompt").strip()


async def test_application_name_prompt_contains_situation_description(llm_chat):
    name = await LlmApplicationWriter(llm_chat).write_name(NEW_APPLICATION)

    assert name == "Odpowiedź."
    system_prompt = get_awaited_argument(llm_chat.generate_text, "system_prompt")
    assert "Proszę o urlop dziekański z powodu choroby." in system_prompt
    assert get_awaited_argument(llm_chat.generate_text, "user_prompt").strip()


async def test_regulation_description_is_limited(llm_chat):
    llm_chat.generate_text.return_value = "a" * (MAX_REGULATION_DESCRIPTION_LENGTH + 1)
    description_source = RegulationDescriptionSource(
        presentation_name="Regulamin studiów",
        headings=[RegulationHeading(text="Urlopy", level=0)],
        beginning="§ 1. Regulamin określa organizację studiów.",
    )

    description = await LlmRegulationDescriptionWriter(llm_chat).write(description_source)

    assert len(description) == MAX_REGULATION_DESCRIPTION_LENGTH
    system_prompt = get_awaited_argument(llm_chat.generate_text, "system_prompt")
    assert "Regulamin studiów" in system_prompt
    assert "Urlopy" in system_prompt
    assert description_source.beginning in system_prompt
    assert get_awaited_argument(llm_chat.generate_text, "user_prompt").strip()


async def test_application_template_description_is_limited(llm_chat):
    llm_chat.generate_text.return_value = "a" * (MAX_APPLICATION_TEMPLATE_DESCRIPTION_LENGTH + 1)
    description_source = ApplicationTemplateDescriptionSource(
        name="Wniosek o urlop",
        instructions="Sporządź wniosek do dziekana.",
        field_labels=["Numer albumu"],
        content="Dziekan Wydziału\n{{ student_id }}",
    )

    description = await LlmApplicationTemplateDescriptionWriter(llm_chat).write(description_source)

    assert len(description) == MAX_APPLICATION_TEMPLATE_DESCRIPTION_LENGTH
    system_prompt = get_awaited_argument(llm_chat.generate_text, "system_prompt")
    assert "Wniosek o urlop" in system_prompt
    assert "Numer albumu" in system_prompt
    assert description_source.instructions in system_prompt
    assert description_source.content in system_prompt
    assert get_awaited_argument(llm_chat.generate_text, "user_prompt").strip()
