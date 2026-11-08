from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints
from pydantic.alias_generators import to_camel
from pydantic.dataclasses import dataclass

from src.domain.services.security import url_safe_authorization_token_length


class AuthTokens(BaseModel):
    access_token: str
    access_expires_in: int
    refresh_token: Annotated[
        str,
        StringConstraints(
            min_length=url_safe_authorization_token_length, max_length=url_safe_authorization_token_length
        ),
    ]
    refresh_expires_in: int


@dataclass(config=ConfigDict(alias_generator=to_camel, validate_by_name=True))
class CurrentUser:
    is_admin: bool
