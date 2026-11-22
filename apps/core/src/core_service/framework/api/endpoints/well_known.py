from fastapi import APIRouter

from core_service.shared.settings.oauth import oauth_settings

well_known_router = APIRouter(prefix="/.well-known", include_in_schema=False)


@well_known_router.get("/oauth-authorization-server")
async def get_authorization_server_metadata() -> dict[str, str | list[str]]:
    public_url = oauth_settings.PUBLIC_URL
    return {
        "issuer": public_url,
        "authorization_endpoint": f"{public_url}/api/oauth/authorize",
        "token_endpoint": f"{public_url}/api/oauth/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "code_challenge_methods_supported": ["S256"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
    }
