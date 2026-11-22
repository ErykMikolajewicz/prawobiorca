from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from core_service.application.dtos.names import Name
from core_service.domain.consts import MAX_OAUTH_CLIENT_NAME_LENGTH, MAX_REDIRECT_URI_LENGTH
from core_service.domain.services.oauth import PKCE_VALUE_PATTERN


class NewOAuthClient(BaseModel):
    name: Name = Field(min_length=1, max_length=MAX_OAUTH_CLIENT_NAME_LENGTH)


@dataclass(config=ConfigDict(alias_generator=to_camel, validate_by_name=True))
class OAuthClientData:
    id: UUID
    name: str
    create_date: datetime


@dataclass
class CreatedOAuthClient:
    id: UUID
    secret: str


class AuthorizationRequest(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, validate_by_name=True)

    client_id: UUID
    redirect_uri: str = Field(min_length=1, max_length=MAX_REDIRECT_URI_LENGTH)
    resource: str
    code_challenge: Annotated[str, StringConstraints(pattern=PKCE_VALUE_PATTERN)]
    state: str | None = Field(default=None, max_length=MAX_REDIRECT_URI_LENGTH)


@dataclass(config=ConfigDict(alias_generator=to_camel, validate_by_name=True))
class AuthorizationRequestDetails:
    client_name: str


@dataclass(config=ConfigDict(alias_generator=to_camel, validate_by_name=True))
class AuthorizationRedirect:
    redirect_url: str


@dataclass(frozen=True)
class OAuthClientCredentials:
    client_id: UUID
    secret: str


class OAuthTokens(BaseModel):
    access_token: str
    token_type: str = "Bearer"  # noqa: S105
    expires_in: int
    refresh_token: str
