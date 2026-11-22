import asyncio
from collections.abc import AsyncGenerator
from typing import Any
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

import pytest
from fastapi import status
from httpx2 import AsyncClient

from core_service.framework.mcp.dependencies import McpDependencies
from core_service.framework.mcp.server import mcp_app, mcp_server

RESOURCE_URL = "http://localhost:8080/api/mcp"
REDIRECT_URI = "https://claude.ai/api/mcp/auth_callback"
CODE_VERIFIER = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
CODE_CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"
STATE = "client-state"

MCP_HEADERS = {"Host": "localhost:8080", "Accept": "application/json, text/event-stream"}


def build_consent(client_id: UUID, redirect_uri: str = REDIRECT_URI) -> dict[str, str]:
    return {
        "resource": RESOURCE_URL,
        "clientId": str(client_id),
        "redirectUri": redirect_uri,
        "codeChallenge": CODE_CHALLENGE,
        "state": STATE,
    }


async def create_oauth_client(admin_client: AsyncClient, name: str = "Claude") -> tuple[UUID, str]:
    response = await admin_client.post("/api/oauth-clients", json={"name": name})
    assert response.status_code == status.HTTP_201_CREATED
    created_client = response.json()
    return UUID(created_client["id"]), created_client["secret"]


async def grant_authorization_code(admin_client: AsyncClient, client_id: UUID) -> str:
    response = await admin_client.post("/api/oauth/consent", json=build_consent(client_id))
    assert response.status_code == status.HTTP_200_OK
    query = parse_qs(urlsplit(response.json()["redirectUrl"]).query)
    return query["code"][0]


async def request_tokens(client: AsyncClient, client_id: UUID, secret: str, **form: str) -> Any:
    return await client.post(
        "/api/oauth/token",
        data={"resource": RESOURCE_URL, "client_id": str(client_id), "client_secret": secret, **form},
    )


async def exchange_code(client: AsyncClient, client_id: UUID, secret: str, code: str) -> Any:
    return await request_tokens(
        client,
        client_id,
        secret,
        grant_type="authorization_code",
        code=code,
        redirect_uri=REDIRECT_URI,
        code_verifier=CODE_VERIFIER,
    )


@pytest.fixture
async def oauth_client(admin_client) -> tuple[UUID, str]:
    return await create_oauth_client(admin_client)


@pytest.fixture
async def mcp_access_token(admin_client, client, oauth_client) -> str:
    client_id, secret = oauth_client
    code = await grant_authorization_code(admin_client, client_id)
    response = await exchange_code(client, client_id, secret, code)
    return response.json()["access_token"]


@pytest.fixture(scope="session")
async def mcp_session_manager() -> AsyncGenerator[None]:
    started, stopped = asyncio.Event(), asyncio.Event()

    async def run_session_manager() -> None:
        async with mcp_server.session_manager.run():
            started.set()
            await stopped.wait()

    task = asyncio.create_task(run_session_manager())
    await started.wait()
    yield
    stopped.set()
    await task


@pytest.fixture
def mcp_dependencies(mcp_session_manager, session_maker, mock_texts_embedder) -> None:
    mcp_app.state.dependencies = McpDependencies(session_maker, mock_texts_embedder)


async def call_mcp_tool(client: AsyncClient, access_token: str | None, tool: str, arguments: dict[str, Any]) -> Any:
    headers = {**MCP_HEADERS}
    if access_token is not None:
        headers["Authorization"] = f"Bearer {access_token}"
    return await client.post(
        "/api/mcp",
        headers=headers,
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": tool, "arguments": arguments}},
    )
