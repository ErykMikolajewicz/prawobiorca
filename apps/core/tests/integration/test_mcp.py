from decimal import Decimal

import pytest
from fastapi import status
from sqlalchemy import select, update

from core_service.application.services.usage import get_usage_day
from core_service.domain.services.usage import MCP_BUDGET_KEY
from core_service.domain.value_objects.regulations import RegulationPreparationStatus
from core_service.infrastructure.relational_db.schemas.oauth import oauth_tokens_table
from core_service.infrastructure.relational_db.schemas.usage_budgets import usage_budgets_table
from core_service.infrastructure.relational_db.schemas.usage_tariff import usage_tariff_table
from core_service.infrastructure.relational_db.schemas.users import users_table
from tests.consts import ADMIN_ID, UNKNOWN_ID, USER_ID
from tests.integration.fixtures.ai_services import QUERY_VECTOR
from tests.integration.fixtures.oauth import MCP_HEADERS, call_mcp_tool
from tests.integration.fixtures.regulations import insert_regulation, insert_section


async def test_mcp_without_token(client, mcp_dependencies):
    response = await call_mcp_tool(client, None, "search_regulations", {"query": "stypendium"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert (
        'resource_metadata="http://localhost:8080/.well-known/oauth-protected-resource/api/mcp"'
        in (response.headers["WWW-Authenticate"])
    )


async def test_mcp_with_invalid_token(client, mcp_dependencies):
    response = await call_mcp_tool(client, "invalid", "search_regulations", {"query": "stypendium"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_protected_resource_metadata(client):
    response = await client.get("/.well-known/oauth-protected-resource/api/mcp")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["resource"] == "http://localhost:8080/api/mcp"
    assert response.json()["authorization_servers"] == ["http://localhost:8080"]


async def test_search_regulations_tool(client, session_maker, mcp_dependencies, mcp_access_token):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, "Regulamin studiów", description_vector=QUERY_VECTOR)

    response = await call_mcp_tool(client, mcp_access_token, "search_regulations", {"query": "stypendium"})

    assert response.status_code == status.HTTP_200_OK
    result = response.json()["result"]
    assert result["isError"] is False
    assert f"Regulamin studiów (id: {regulation_id})" in result["content"][0]["text"]


async def test_search_regulation_tool(client, session_maker, mcp_dependencies, mcp_access_token):
    async with session_maker.begin() as session:
        regulation_id = await insert_regulation(session, None, preparation_status=RegulationPreparationStatus.PREPARED)
        await insert_section(session, regulation_id, "Student ma prawo do stypendium.", [QUERY_VECTOR])

    response = await call_mcp_tool(
        client, mcp_access_token, "search_regulation", {"regulation_id": str(regulation_id), "query": "stypendium"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["result"]["content"][0]["text"] == (
        "## Art. 1 (trafność: 1.00)\nStudent ma prawo do stypendium."
    )


async def test_mcp_search_is_charged_from_monthly_budget(client, session_maker, mcp_dependencies, mcp_access_token):
    await call_mcp_tool(client, mcp_access_token, "search_regulations", {"query": "stypendium"})

    async with session_maker() as session:
        result = await session.execute(select(usage_budgets_table))
    assert [(row.budget_key, row.day, row.spent) for row in result] == [
        (MCP_BUDGET_KEY, get_usage_day().replace(day=1), Decimal("0.03"))
    ]


async def test_mcp_search_over_monthly_limit(client, session_maker, mcp_dependencies, mcp_access_token):
    async with session_maker.begin() as session:
        await session.execute(update(usage_tariff_table).values(mcp_monthly_limit=Decimal("0.01")))

    response = await call_mcp_tool(client, mcp_access_token, "search_regulations", {"query": "stypendium"})

    result = response.json()["result"]
    assert result["isError"] is True
    assert "limit" in result["content"][0]["text"]


async def test_mcp_token_of_former_administrator(client, session_maker, mcp_dependencies, mcp_access_token):
    async with session_maker.begin() as session:
        await session.execute(update(users_table).where(users_table.c.id == ADMIN_ID).values(is_admin=False))

    response = await call_mcp_tool(client, mcp_access_token, "search_regulations", {"query": "stypendium"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_deleted_oauth_client_tokens_are_rejected(
    admin_client, client, oauth_client, mcp_dependencies, mcp_access_token
):
    client_id, _ = oauth_client
    await admin_client.delete(f"/api/oauth-clients/{client_id}")

    response = await call_mcp_tool(client, mcp_access_token, "search_regulations", {"query": "stypendium"})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_rest_routing_with_mcp(client):
    response = await client.get("/api/regulations/")
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"].endswith("/api/regulations")
    response = await client.patch("/health/liveness")
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert "GET" in response.headers["Allow"]


@pytest.mark.parametrize("resource", [None, "https://other.example/api/mcp"])
async def test_access_token_requires_issued_audience(
    client, session_maker, mcp_dependencies, mcp_access_token, resource
):
    async with session_maker.begin() as session:
        await session.execute(update(oauth_tokens_table).values(resource=resource))

    response = await call_mcp_tool(client, mcp_access_token, "search_regulations", {"query": "stypendium"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    ("headers", "expected_status"),
    [
        ({"Origin": "http://localhost:8080"}, status.HTTP_401_UNAUTHORIZED),
        ({"Origin": "https://unknown.example"}, status.HTTP_403_FORBIDDEN),
        ({"Host": "unknown.example"}, status.HTTP_421_MISDIRECTED_REQUEST),
    ],
)
async def test_transport_headers_before_authentication(client, headers, expected_status):
    response = await client.get("/api/mcp", headers={**MCP_HEADERS, **headers})
    assert response.status_code == expected_status


async def test_browse_toc_then_read_section(
    client, session_maker, mcp_dependencies, mcp_access_token, mock_texts_embedder
):
    header = "Rozdział 2 > Art. 10a Stypendia"
    body = "1. Pierwszy ustęp.\n2. Drugi ustęp.\n1) punkt pierwszy."
    async with session_maker.begin() as session:
        regulation = await insert_regulation(session, None, preparation_status=RegulationPreparationStatus.PREPARED)
        second = await insert_section(
            session, regulation, "Dalsza treść.", [QUERY_VECTOR], section_order=1, header=None
        )
        first = await insert_section(
            session,
            regulation,
            body,
            [QUERY_VECTOR],
            header=header,
            summary_label="Stypendia",
            summary="Warunki przyznania stypendium.",
        )

    args = {"regulation_id": str(regulation)}
    response = await call_mcp_tool(client, mcp_access_token, "get_regulation_toc", {**args, "limit": 1})
    page = response.json()["result"]["structuredContent"]
    assert page == {
        "entries": [
            {
                "section_id": str(first),
                "header": header,
                "summary_label": "Stypendia",
                "summary": "Warunki przyznania stypendium.",
            }
        ],
        "next_offset": 1,
    }
    response = await call_mcp_tool(
        client, mcp_access_token, "get_regulation_toc", {**args, "limit": 1, "offset": page["next_offset"]}
    )
    assert response.json()["result"]["structuredContent"] == {
        "entries": [{"section_id": str(second), "header": None, "summary_label": None, "summary": None}],
        "next_offset": None,
    }

    for selector in [{"section_id": page["entries"][0]["section_id"]}, {"citation": " art.10a. "}]:
        response = await call_mcp_tool(client, mcp_access_token, "get_regulation_section", {**args, **selector})
        assert response.json()["result"]["content"][0]["text"] == f"## {header}\n{body}"
    mock_texts_embedder.embed_queries.assert_not_awaited()
    async with session_maker() as session:
        assert (await session.execute(select(usage_budgets_table))).first() is None


async def test_repeated_paragraph_returns_choices(client, session_maker, mcp_dependencies, mcp_access_token):
    async with session_maker.begin() as session:
        regulation = await insert_regulation(session, ADMIN_ID, preparation_status=RegulationPreparationStatus.PREPARED)
        choices = []
        for order, header in enumerate(["§ 7", "Załącznik nr 1 > § 7. Warunki", "§ 70", "§ 7a", "§ 7¹", "Art. 7"]):
            section = await insert_section(
                session, regulation, "Treść przepisu.", [QUERY_VECTOR], order, ADMIN_ID, header=header
            )
            if order < 2:
                choices.append(f"{header} (section_id: {section})")
    response = await call_mcp_tool(
        client, mcp_access_token, "get_regulation_section", {"regulation_id": str(regulation), "citation": "§7"}
    )
    result = response.json()["result"]
    assert result["isError"] is False
    assert result["content"][0]["text"].splitlines()[1:] == choices


@pytest.mark.parametrize(
    ("tool", "selector"), [("get_regulation_toc", {}), ("get_regulation_section", {"citation": "Art. 1"})]
)
async def test_browse_requires_access_and_prepared_act(
    client, session_maker, user, mcp_dependencies, mcp_access_token, tool, selector
):
    async with session_maker.begin() as session:
        private = await insert_regulation(session, USER_ID, preparation_status=RegulationPreparationStatus.PREPARED)
        pending = await insert_regulation(session, None, "W przygotowaniu")
    for regulation, message in [
        (private, "Nie znaleziono aktu"),
        (UNKNOWN_ID, "Nie znaleziono aktu"),
        (pending, "nie jest jeszcze przygotowany"),
    ]:
        response = await call_mcp_tool(client, mcp_access_token, tool, {"regulation_id": str(regulation), **selector})
        result = response.json()["result"]
        assert result["isError"]
        assert message in result["content"][0]["text"]


async def test_section_selector_must_resolve_in_requested_act(
    client, session_maker, mcp_dependencies, mcp_access_token
):
    async with session_maker.begin() as session:
        target = await insert_regulation(session, None, preparation_status=RegulationPreparationStatus.PREPARED)
        other = await insert_regulation(session, None, preparation_status=RegulationPreparationStatus.PREPARED)
        section = await insert_section(session, other, "Inny akt.", [QUERY_VECTOR])
    for selector in [
        {},
        {"section_id": str(section), "citation": "Art. 1"},
        {"section_id": str(section)},
        {"citation": "Art. 1"},
    ]:
        response = await call_mcp_tool(
            client, mcp_access_token, "get_regulation_section", {"regulation_id": str(target), **selector}
        )
        assert response.json()["result"]["isError"]
