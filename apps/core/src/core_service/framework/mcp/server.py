from collections.abc import Awaitable, Callable
from contextlib import AsyncExitStack
from typing import Annotated
from urllib.parse import urlsplit
from uuid import UUID

from mcp.server.auth.settings import AuthSettings
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.server.transport_security import TransportSecurityMiddleware, TransportSecuritySettings
from pydantic import Field
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from core_service.application.dtos.regulations import RegulationRepresentation, RegulationSearchResult
from core_service.application.dtos.search import SearchOrder, SearchParams, SearchResult
from core_service.application.services.usage import UsageCharger
from core_service.application.use_cases.regulations import GetRegulation, SearchRegulation, SearchRegulations
from core_service.domain.exceptions.access import AccessForbidden, LoginRequired
from core_service.domain.exceptions.limits import UsageLimitExceeded
from core_service.domain.exceptions.regulations import RegulationNotFound, RegulationsNotPreparedToSearch
from core_service.domain.value_objects.regulations import RegulationScope, RegulationType
from core_service.framework.consts import MCP_PATH
from core_service.framework.dependencies.regulations import get_regulation_repository, get_sections_repository
from core_service.framework.dependencies.usage import get_usage_budgets_repo, get_usage_tariff_repo
from core_service.framework.mcp.auth import McpTokenVerifier, get_mcp_caller
from core_service.framework.mcp.dependencies import McpDependencies
from core_service.shared.exceptions import ServiceUnavailable
from core_service.shared.settings.oauth import oauth_settings

SEARCH_THRESHOLD = 0.5


def get_mcp_dependencies() -> McpDependencies:
    return mcp_app.state.dependencies


mcp_server = MCPServer(
    name="Prawobiorca",
    instructions=(
        "Semantic search engine of Polish legal acts and university regulations. "
        "Find relevant acts with search_regulations, then search inside a chosen act with search_regulation "
        "and cite its articles and paragraphs."
    ),
    token_verifier=McpTokenVerifier(get_mcp_dependencies),
    auth=AuthSettings(
        issuer_url=oauth_settings.PUBLIC_URL,
        resource_server_url=f"{oauth_settings.PUBLIC_URL}{MCP_PATH}",
        validate_token_resource=True,
    ),
)


def create_usage_charger() -> UsageCharger:
    return UsageCharger(get_usage_budgets_repo(), get_usage_tariff_repo())


def format_regulation(regulation: RegulationRepresentation) -> str:
    lines = [f"{regulation.presentation_name} (id: {regulation.id})"]
    if regulation.regulation_type is not None:
        lines.append(f"Typ: {regulation.regulation_type}")
    if regulation.description:
        lines.append(regulation.description)
    return "\n".join(lines)


def format_regulation_search_result(result: RegulationSearchResult) -> str:
    return f"{format_regulation(result.regulation)}\nTrafność: {result.score:.2f}"


def format_section_search_result(result: SearchResult) -> str:
    header = result.header or "Fragment"
    return f"## {header} (trafność: {result.score:.2f})\n{result.text}"


def format_results(results: list[str]) -> str:
    return "\n\n".join(results) if results else "Nie znaleziono pasujących wyników."


@mcp_server.tool(description="Search Polish legal acts and regulations semantically. Returns matching acts with ids.")
async def search_regulations(
    query: Annotated[str, Field(min_length=1, description="What the user is looking for, in Polish.")],
    regulation_type: Annotated[RegulationType | None, Field(description="Optional type of the act.")] = None,
    scope: Annotated[RegulationScope, Field(description="PUBLIC acts or PRIVATE acts of the user.")] = (
        RegulationScope.PUBLIC
    ),
) -> str:
    dependencies = get_mcp_dependencies()
    search_regulations_ = SearchRegulations(
        dependencies.session_maker, dependencies.texts_embedder, get_regulation_repository(), create_usage_charger()
    )
    try:
        results = await search_regulations_.execute(
            get_mcp_caller(), scope, regulation_type, None, query, SEARCH_THRESHOLD
        )
    except UsageLimitExceeded:
        raise ToolError("Miesięczny limit wyszukiwań przez MCP został wyczerpany.")
    except ServiceUnavailable:
        raise ToolError("Wyszukiwarka jest chwilowo niedostępna, spróbuj ponownie za chwilę.")
    except LoginRequired, AccessForbidden:
        raise ToolError("Brak dostępu do wybranych aktów prawnych.")

    return format_results([format_regulation_search_result(result) for result in results])


@mcp_server.tool(description="Search inside one legal act. Returns the most relevant articles and paragraphs.")
async def search_regulation(
    regulation_id: Annotated[UUID, Field(description="Id of the act returned by search_regulations.")],
    query: Annotated[str, Field(min_length=1, description="What to find in the act, in Polish.")],
    limit: Annotated[int, Field(gt=0, le=50, description="Maximum number of fragments.")] = 10,
) -> str:
    dependencies = get_mcp_dependencies()
    search_regulation_ = SearchRegulation(
        dependencies.session_maker,
        dependencies.texts_embedder,
        get_sections_repository(),
        get_regulation_repository(),
        create_usage_charger(),
    )
    search_params = SearchParams(threshold=SEARCH_THRESHOLD, limit=limit, query=query, order_by=SearchOrder.SCORE)
    try:
        results = await search_regulation_.execute(get_mcp_caller(), regulation_id, search_params)
    except UsageLimitExceeded:
        raise ToolError("Miesięczny limit wyszukiwań przez MCP został wyczerpany.")
    except ServiceUnavailable:
        raise ToolError("Wyszukiwarka jest chwilowo niedostępna, spróbuj ponownie za chwilę.")
    except RegulationNotFound, LoginRequired, AccessForbidden:
        raise ToolError(f"Nie znaleziono aktu prawnego o id {regulation_id}.")
    except RegulationsNotPreparedToSearch as error:
        raise ToolError(f"Akt prawny {error.regulations_name} nie jest jeszcze przygotowany do wyszukiwania.")

    return format_results([format_section_search_result(result) for result in results])


@mcp_server.tool(description="Get the name, type and description of one legal act.")
async def get_regulation_details(
    regulation_id: Annotated[UUID, Field(description="Id of the act returned by search_regulations.")],
) -> str:
    get_regulation = GetRegulation(get_mcp_dependencies().session_maker, get_regulation_repository())
    try:
        regulation = await get_regulation.execute(get_mcp_caller(), regulation_id)
    except RegulationNotFound, LoginRequired, AccessForbidden:
        raise ToolError(f"Nie znaleziono aktu prawnego o id {regulation_id}.")

    return format_regulation(regulation)


transport_security = TransportSecuritySettings(
    allowed_hosts=[urlsplit(oauth_settings.PUBLIC_URL).netloc],
    allowed_origins=[oauth_settings.PUBLIC_URL],
)


class McpTransportHeaders:
    """Check transport headers before the SDK challenges unauthenticated requests."""

    def __init__(self, app: ASGIApp):
        self.app = app
        self.security = TransportSecurityMiddleware(transport_security)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        response = await self.security.validate_request(Request(scope))
        if response is not None:
            await response(scope, receive, send)
        else:
            await self.app(scope, receive, send)


mcp_app = mcp_server.streamable_http_app(
    streamable_http_path=MCP_PATH,
    stateless_http=True,
    json_response=True,
    transport_security=transport_security,
)


async def init_mcp_server(dependencies: McpDependencies) -> Callable[[], Awaitable[None]]:
    mcp_app.state.dependencies = dependencies
    exit_stack = AsyncExitStack()
    await exit_stack.enter_async_context(mcp_server.session_manager.run())
    return exit_stack.aclose
