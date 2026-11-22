from datetime import datetime
from uuid import UUID

from sqlalchemy import delete, insert, select, update

from core_service.application.dtos.oauth import OAuthClientData
from core_service.application.ports.relational import AsyncSession
from core_service.domain.exceptions.oauth import OAuthClientNotFound
from core_service.domain.value_objects.oauth import AuthorizationGrant, OAuthTokenHashes, OAuthTokenOwner
from core_service.infrastructure.relational_db.schemas.oauth import (
    oauth_authorization_codes_table,
    oauth_clients_table,
    oauth_tokens_table,
)
from core_service.infrastructure.relational_db.schemas.users import users_table
from core_service.infrastructure.relational_db.session import sqla_session


class SqlaOAuthClientsRepository:
    @staticmethod
    async def list_all(session: AsyncSession) -> list[OAuthClientData]:
        session = sqla_session(session)
        statement = select(
            oauth_clients_table.c.id, oauth_clients_table.c.name, oauth_clients_table.c.create_date
        ).order_by(oauth_clients_table.c.create_date)
        result = await session.execute(statement)
        return [OAuthClientData(id=row.id, name=row.name, create_date=row.create_date) for row in result]

    @staticmethod
    async def add(session: AsyncSession, name: str, secret_hash: str) -> UUID:
        session = sqla_session(session)
        statement = (
            insert(oauth_clients_table).values(name=name, secret_hash=secret_hash).returning(oauth_clients_table.c.id)
        )
        result = await session.execute(statement)
        return result.scalar_one()

    @staticmethod
    async def delete(session: AsyncSession, client_id: UUID) -> None:
        session = sqla_session(session)
        statement = (
            delete(oauth_clients_table).where(oauth_clients_table.c.id == client_id).returning(oauth_clients_table.c.id)
        )
        result = await session.execute(statement)

        if result.scalar_one_or_none() is None:
            raise OAuthClientNotFound

    @staticmethod
    async def get_name(session: AsyncSession, client_id: UUID) -> str | None:
        session = sqla_session(session)
        statement = select(oauth_clients_table.c.name).where(oauth_clients_table.c.id == client_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_secret_hash(session: AsyncSession, client_id: UUID) -> str | None:
        session = sqla_session(session)
        statement = select(oauth_clients_table.c.secret_hash).where(oauth_clients_table.c.id == client_id)
        result = await session.execute(statement)
        return result.scalar_one_or_none()


class SqlaOAuthAuthorizationCodesRepository:
    @staticmethod
    async def add(session: AsyncSession, code_hash: str, grant: AuthorizationGrant, valid_until: datetime) -> None:
        session = sqla_session(session)
        statement = insert(oauth_authorization_codes_table).values(
            code_hash=code_hash,
            client_id=grant.client_id,
            user_id=grant.user_id,
            redirect_uri=grant.redirect_uri,
            code_challenge=grant.code_challenge,
            resource=grant.resource,
            valid_until=valid_until,
        )
        await session.execute(statement)

    @staticmethod
    async def take(session: AsyncSession, code_hash: str, now: datetime) -> AuthorizationGrant | None:
        session = sqla_session(session)
        statement = (
            delete(oauth_authorization_codes_table)
            .where(
                oauth_authorization_codes_table.c.code_hash == code_hash,
                oauth_authorization_codes_table.c.valid_until > now,
            )
            .returning(
                oauth_authorization_codes_table.c.client_id,
                oauth_authorization_codes_table.c.user_id,
                oauth_authorization_codes_table.c.redirect_uri,
                oauth_authorization_codes_table.c.code_challenge,
                oauth_authorization_codes_table.c.resource,
            )
        )
        result = await session.execute(statement)
        row = result.one_or_none()
        if row is None:
            return None

        return AuthorizationGrant(
            client_id=row.client_id,
            user_id=row.user_id,
            redirect_uri=row.redirect_uri,
            code_challenge=row.code_challenge,
            resource=row.resource,
        )

    @staticmethod
    async def delete_expired(session: AsyncSession, now: datetime) -> None:
        session = sqla_session(session)
        statement = delete(oauth_authorization_codes_table).where(oauth_authorization_codes_table.c.valid_until <= now)
        await session.execute(statement)


class SqlaOAuthTokensRepository:
    @staticmethod
    async def add(
        session: AsyncSession, client_id: UUID, user_id: UUID, resource: str, hashes: OAuthTokenHashes
    ) -> None:
        session = sqla_session(session)
        statement = insert(oauth_tokens_table).values(
            client_id=client_id,
            user_id=user_id,
            resource=resource,
            access_token_hash=hashes.access_token_hash,
            access_valid_until=hashes.access_valid_until,
            refresh_token_hash=hashes.refresh_token_hash,
            refresh_valid_until=hashes.refresh_valid_until,
        )
        await session.execute(statement)

    @staticmethod
    async def rotate(
        session: AsyncSession,
        client_id: UUID,
        resource: str,
        refresh_token_hash: str,
        now: datetime,
        hashes: OAuthTokenHashes,
    ) -> bool:
        session = sqla_session(session)
        statement = (
            update(oauth_tokens_table)
            .where(
                oauth_tokens_table.c.client_id == client_id,
                oauth_tokens_table.c.resource == resource,
                oauth_tokens_table.c.refresh_token_hash == refresh_token_hash,
                oauth_tokens_table.c.refresh_valid_until > now,
            )
            .values(
                access_token_hash=hashes.access_token_hash,
                access_valid_until=hashes.access_valid_until,
                refresh_token_hash=hashes.refresh_token_hash,
                refresh_valid_until=hashes.refresh_valid_until,
            )
            .returning(oauth_tokens_table.c.id)
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_owner(session: AsyncSession, access_token_hash: str, now: datetime) -> OAuthTokenOwner | None:
        session = sqla_session(session)
        statement = (
            select(
                oauth_tokens_table.c.client_id,
                oauth_tokens_table.c.user_id,
                oauth_tokens_table.c.access_valid_until,
                users_table.c.is_admin,
                oauth_tokens_table.c.resource,
            )
            .join(users_table, users_table.c.id == oauth_tokens_table.c.user_id)
            .where(
                oauth_tokens_table.c.access_token_hash == access_token_hash,
                oauth_tokens_table.c.access_valid_until > now,
            )
        )
        result = await session.execute(statement)
        row = result.one_or_none()
        if row is None:
            return None

        return OAuthTokenOwner(
            client_id=row.client_id,
            user_id=row.user_id,
            is_admin=row.is_admin,
            resource=row.resource,
            access_valid_until=row.access_valid_until,
        )

    @staticmethod
    async def delete_expired(session: AsyncSession, now: datetime) -> None:
        session = sqla_session(session)
        statement = delete(oauth_tokens_table).where(oauth_tokens_table.c.refresh_valid_until <= now)
        await session.execute(statement)
