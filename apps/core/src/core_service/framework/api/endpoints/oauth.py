import base64
from typing import Annotated
from urllib.parse import unquote_plus, urlencode
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import ValidationError

from core_service.application.dtos.oauth import (
    AuthorizationRedirect,
    AuthorizationRequest,
    AuthorizationRequestDetails,
    OAuthClientCredentials,
    OAuthTokens,
)
from core_service.application.use_cases.oauth import (
    AuthorizeOAuthClient,
    ExchangeAuthorizationCode,
    GetAuthorizationRequestDetails,
    RefreshOAuthTokens,
)
from core_service.domain.exceptions.oauth import (
    InvalidAuthorizationRequest,
    InvalidClientCredentials,
    InvalidGrant,
    InvalidTarget,
)
from core_service.domain.value_objects.users import Caller
from core_service.framework.consts import OAUTH_CONSENT_PAGE_PATH
from core_service.framework.dependencies.authentication import get_caller
from core_service.framework.dependencies.oauth import (
    get_authorize_oauth_client,
    get_exchange_authorization_code,
    get_get_authorization_request_details,
    get_refresh_oauth_tokens,
)

oauth_router = APIRouter(tags=["oauth"], prefix="/api/oauth")

NO_STORE_HEADERS = {"Cache-Control": "no-store"}


def create_oauth_error(error: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> JSONResponse:
    return JSONResponse({"error": error}, status_code=status_code, headers=NO_STORE_HEADERS)


def get_requested_resource(resources: list[str] | None) -> str | None:
    if resources is None:
        return None
    if len(resources) != 1:
        raise InvalidTarget
    return resources[0]


def parse_client_credentials(
    authorization: str | None, client_id: str | None, client_secret: str | None
) -> OAuthClientCredentials:
    scheme, _, encoded_credentials = (authorization or "").partition(" ")
    if authorization is not None:
        if scheme.lower() != "basic":
            raise InvalidClientCredentials
        try:
            decoded_credentials = base64.b64decode(encoded_credentials, validate=True).decode("utf-8")
        except ValueError:
            raise InvalidClientCredentials
        encoded_client_id, _, encoded_secret = decoded_credentials.partition(":")
        basic_id = unquote_plus(encoded_client_id)
        if client_id is not None and client_id != basic_id:
            raise InvalidClientCredentials
        client_id, client_secret = basic_id, unquote_plus(encoded_secret)

    if client_id is None or not client_secret:
        raise InvalidClientCredentials
    try:
        return OAuthClientCredentials(client_id=UUID(client_id), secret=client_secret)
    except ValueError:
        raise InvalidClientCredentials


@oauth_router.get("/authorize", include_in_schema=False)
async def authorize(
    get_authorization_request_details: Annotated[
        GetAuthorizationRequestDetails, Depends(get_get_authorization_request_details)
    ],
    response_type: str | None = None,
    client_id: str | None = None,
    redirect_uri: str | None = None,
    code_challenge: str | None = None,
    code_challenge_method: str | None = None,
    resource: Annotated[list[str] | None, Query()] = None,
    state: str | None = None,
) -> RedirectResponse:
    if response_type != "code" or code_challenge_method != "S256":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported authorization request!")

    try:
        request = AuthorizationRequest.model_validate(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "code_challenge": code_challenge,
                "resource": get_requested_resource(resource),
                "state": state,
            }
        )
        await get_authorization_request_details.execute(request)
    except ValidationError, InvalidAuthorizationRequest, InvalidTarget:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization request!")

    query = urlencode(request.model_dump(mode="json", by_alias=True, exclude_none=True))
    return RedirectResponse(f"{OAUTH_CONSENT_PAGE_PATH}?{query}", status_code=status.HTTP_302_FOUND)


@oauth_router.get(
    "/consent",
    response_model=AuthorizationRequestDetails,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid authorization request!"},
    },
)
async def get_consent_details(
    get_authorization_request_details: Annotated[
        GetAuthorizationRequestDetails, Depends(get_get_authorization_request_details)
    ],
    request: Annotated[AuthorizationRequest, Query()],
) -> AuthorizationRequestDetails:
    try:
        return await get_authorization_request_details.execute(request)
    except InvalidAuthorizationRequest:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization request!")


@oauth_router.post(
    "/consent",
    response_model=AuthorizationRedirect,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Invalid authorization request!"},
    },
)
async def grant_consent(
    caller: Annotated[Caller, Depends(get_caller)],
    authorize_oauth_client: Annotated[AuthorizeOAuthClient, Depends(get_authorize_oauth_client)],
    request: AuthorizationRequest,
) -> AuthorizationRedirect:
    try:
        return await authorize_oauth_client.execute(caller, request)
    except InvalidAuthorizationRequest:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid authorization request!")


@oauth_router.post("/token", include_in_schema=False)
async def issue_tokens(
    exchange_authorization_code: Annotated[ExchangeAuthorizationCode, Depends(get_exchange_authorization_code)],
    refresh_oauth_tokens: Annotated[RefreshOAuthTokens, Depends(get_refresh_oauth_tokens)],
    grant_type: Annotated[str | None, Form()] = None,
    resource: Annotated[list[str] | None, Form()] = None,
    authorization: Annotated[str | None, Header()] = None,
    client_id: Annotated[str | None, Form()] = None,
    client_secret: Annotated[str | None, Form()] = None,
    code: Annotated[str | None, Form()] = None,
    redirect_uri: Annotated[str | None, Form()] = None,
    code_verifier: Annotated[str | None, Form()] = None,
    refresh_token: Annotated[str | None, Form()] = None,
) -> JSONResponse:
    if not grant_type or (authorization is not None and client_secret is not None):
        return create_oauth_error("invalid_request")
    tokens: OAuthTokens
    try:
        target = get_requested_resource(resource)
        credentials = parse_client_credentials(authorization, client_id, client_secret)
        if grant_type == "authorization_code":
            if code is None or redirect_uri is None or code_verifier is None:
                return create_oauth_error("invalid_request")
            tokens = await exchange_authorization_code.execute(credentials, code, code_verifier, redirect_uri, target)
        elif grant_type == "refresh_token":
            if refresh_token is None:
                return create_oauth_error("invalid_request")
            tokens = await refresh_oauth_tokens.execute(credentials, refresh_token, target)
        else:
            return create_oauth_error("unsupported_grant_type")
    except InvalidClientCredentials:
        response = create_oauth_error("invalid_client", status.HTTP_401_UNAUTHORIZED)
        response.headers["WWW-Authenticate"] = 'Basic realm="oauth/token"'
        return response
    except InvalidTarget:
        return create_oauth_error("invalid_target")
    except InvalidGrant:
        return create_oauth_error("invalid_grant")

    return JSONResponse(tokens.model_dump(), headers=NO_STORE_HEADERS)
