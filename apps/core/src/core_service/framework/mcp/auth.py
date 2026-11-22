from collections.abc import Callable
from uuid import UUID

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken
from mcp.server.mcpserver.exceptions import ToolError

from core_service.application.use_cases.oauth import AuthenticateMcpToken
from core_service.domain.value_objects.users import Caller
from core_service.framework.dependencies.oauth import get_oauth_tokens_repo
from core_service.framework.mcp.dependencies import McpDependencies


class McpTokenVerifier:
    def __init__(self, get_dependencies: Callable[[], McpDependencies]):
        self.get_dependencies = get_dependencies

    async def verify_token(self, token: str) -> AccessToken | None:
        authenticate_mcp_token = AuthenticateMcpToken(self.get_dependencies().session_maker, get_oauth_tokens_repo())
        owner = await authenticate_mcp_token.execute(token)
        if owner is None:
            return None

        return AccessToken(
            token=token,
            client_id=str(owner.client_id),
            scopes=[],
            resource=owner.resource,
            expires_at=int(owner.access_valid_until.timestamp()),
            subject=str(owner.user_id),
        )


def get_mcp_caller() -> Caller:
    access_token = get_access_token()
    if access_token is None or access_token.subject is None:
        raise ToolError("Brak uwierzytelnienia.")

    return Caller(user_id=UUID(access_token.subject), is_admin=True, mcp_client_id=UUID(access_token.client_id))
