import json
from unittest.mock import create_autospec

import pytest
from httpx2 import AsyncClient, MockTransport, Response
from openai import AsyncOpenAI

from core_service.infrastructure.ai_services.llm_chat import LlmChat
from core_service.infrastructure.ai_services.llm_cost_limiter import LlmCostLimiter
from core_service.shared.exceptions import ServiceUnavailable


def create_llm_chat(handler, cost_limiter: LlmCostLimiter | None = None) -> LlmChat:
    client = AsyncOpenAI(
        base_url="http://llm.local/v1",
        api_key="unused",
        max_retries=0,
        http_client=AsyncClient(transport=MockTransport(handler)),
    )
    return LlmChat(client, "model", temperature=0.2, top_p=0.9, max_tokens=100, cost_limiter=cost_limiter)


def create_completion(choices: list[dict]) -> dict:
    return {
        "id": "completion-id",
        "object": "chat.completion",
        "created": 0,
        "model": "model",
        "choices": choices,
        "usage": {"prompt_tokens": 120, "completion_tokens": 30, "total_tokens": 150},
    }


def create_choice(content: str | None) -> dict:
    return {"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}


@pytest.fixture
def cost_limiter():
    return create_autospec(LlmCostLimiter)


async def test_generate_text_returns_answer_and_records_usage(cost_limiter):
    requests = []

    def handler(request):
        requests.append(request)
        return Response(200, json=create_completion([create_choice("  Szanowni Państwo,\n")]))

    text = await create_llm_chat(handler, cost_limiter).generate_text("Jesteś asystentem.", "Napisz pismo.")

    assert text == "Szanowni Państwo,"
    assert json.loads(requests[0].content)["messages"] == [
        {"role": "system", "content": "Jesteś asystentem."},
        {"role": "user", "content": "Napisz pismo."},
    ]
    cost_limiter.record.assert_awaited_once_with(120, 30)


async def test_generate_text_over_cost_limit_does_not_call_llm(cost_limiter):
    requests = []
    cost_limiter.check.side_effect = ServiceUnavailable

    with pytest.raises(ServiceUnavailable):
        await create_llm_chat(requests.append, cost_limiter).generate_text("System.", "Pytanie.")

    assert requests == []


@pytest.mark.parametrize(
    ("status_code", "body"),
    [
        (503, {}),
        (200, create_completion([])),
        (200, create_completion([create_choice(None)])),
        (200, create_completion([create_choice("")])),
    ],
    ids=("error status", "no choices", "no content", "empty content"),
)
async def test_generate_text_without_answer_raises_service_unavailable(status_code, body):
    llm_chat = create_llm_chat(lambda request: Response(status_code, json=body))

    with pytest.raises(ServiceUnavailable):
        await llm_chat.generate_text("System.", "Pytanie.")
