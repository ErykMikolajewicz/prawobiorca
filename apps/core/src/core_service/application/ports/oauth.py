from datetime import datetime
from typing import Protocol
from uuid import UUID

from core_service.application.dtos.oauth import OAuthClientData
from core_service.application.ports.relational import AsyncSession
from core_service.domain.value_objects.oauth import AuthorizationGrant, OAuthTokenHashes, OAuthTokenOwner


class OAuthClientsRepository(Protocol):
    async def list_all(self, session: AsyncSession) -> list[OAuthClientData]: ...

    async def add(self, session: AsyncSession, name: str, secret_hash: str) -> UUID: ...

    async def delete(self, session: AsyncSession, client_id: UUID) -> None: ...

    async def get_name(self, session: AsyncSession, client_id: UUID) -> str | None: ...

    async def get_secret_hash(self, session: AsyncSession, client_id: UUID) -> str | None: ...


class OAuthAuthorizationCodesRepository(Protocol):
    async def add(
        self, session: AsyncSession, code_hash: str, grant: AuthorizationGrant, valid_until: datetime
    ) -> None: ...

    async def take(self, session: AsyncSession, code_hash: str, now: datetime) -> AuthorizationGrant | None: ...

    async def delete_expired(self, session: AsyncSession, now: datetime) -> None: ...


class OAuthTokensRepository(Protocol):
    async def add(
        self, session: AsyncSession, client_id: UUID, user_id: UUID, resource: str, hashes: OAuthTokenHashes
    ) -> None: ...

    async def rotate(
        self,
        session: AsyncSession,
        client_id: UUID,
        resource: str,
        refresh_token_hash: str,
        now: datetime,
        hashes: OAuthTokenHashes,
    ) -> bool: ...

    async def get_owner(
        self, session: AsyncSession, access_token_hash: str, now: datetime
    ) -> OAuthTokenOwner | None: ...

    async def delete_expired(self, session: AsyncSession, now: datetime) -> None: ...
