import base64
from urllib.parse import parse_qs, urlsplit

import pytest
from fastapi import status
from sqlalchemy import select, update

from core_service.infrastructure.relational_db.schemas.oauth import oauth_clients_table
from core_service.infrastructure.relational_db.schemas.users import users_table
from tests.consts import ADMIN_ID, UNKNOWN_ID
from tests.integration.fixtures.oauth import (
    CODE_CHALLENGE,
    CODE_VERIFIER,
    REDIRECT_URI,
    RESOURCE_URL,
    STATE,
    build_consent,
    create_oauth_client,
    exchange_code,
    grant_authorization_code,
    request_tokens,
)


def build_authorize_params(client_id, redirect_uri: str = REDIRECT_URI, **params: str) -> dict[str, str]:
    return {
        "resource": RESOURCE_URL,
        "response_type": "code",
        "client_id": str(client_id),
        "redirect_uri": redirect_uri,
        "code_challenge": CODE_CHALLENGE,
        "code_challenge_method": "S256",
        "state": STATE,
        **params,
    }


async def test_manage_oauth_clients(admin_client, session_maker):
    client_id, secret = await create_oauth_client(admin_client, "Claude")

    async with session_maker() as session:
        secret_hash = await session.scalar(select(oauth_clients_table.c.secret_hash))
    assert secret not in secret_hash

    response = await admin_client.get("/api/oauth-clients")
    assert response.status_code == status.HTTP_200_OK
    assert [(client["id"], client["name"]) for client in response.json()] == [(str(client_id), "Claude")]

    response = await admin_client.delete(f"/api/oauth-clients/{client_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = await admin_client.delete(f"/api/oauth-clients/{client_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [("GET", "/api/oauth-clients", None), ("POST", "/api/oauth-clients", {"name": "Claude"})],
    ids=("list", "create"),
)
async def test_oauth_clients_as_normal_user(user_client, client, method, path, body):
    response = await user_client.request(method, path, json=body)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    response = await client.request(method, path, json=body)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_authorization_server_metadata(client):
    response = await client.get("/.well-known/oauth-authorization-server")

    assert response.status_code == status.HTTP_200_OK
    metadata = response.json()
    assert metadata["issuer"] == "http://localhost:8080"
    assert metadata["token_endpoint"] == "http://localhost:8080/api/oauth/token"
    assert metadata["code_challenge_methods_supported"] == ["S256"]


async def test_authorize_redirects_to_consent_page(client, oauth_client):
    client_id, _ = oauth_client

    response = await client.get("/api/oauth/authorize", params=build_authorize_params(client_id))

    assert response.status_code == status.HTTP_302_FOUND
    location = urlsplit(response.headers["location"])
    assert location.path == "/oauth/consent"
    assert parse_qs(location.query) == {key: [value] for key, value in build_consent(client_id).items()}


@pytest.mark.parametrize(
    ("redirect_uri", "params"),
    [
        ("https://attacker.example/callback", {}),
        (REDIRECT_URI, {"code_challenge_method": "plain"}),
        (REDIRECT_URI, {"response_type": "token"}),
        (REDIRECT_URI, {"code_challenge": "too-short"}),
    ],
    ids=("not allowed redirect uri", "plain challenge", "implicit flow", "invalid challenge"),
)
async def test_authorize_with_invalid_request(client, oauth_client, redirect_uri, params):
    client_id, _ = oauth_client

    response = await client.get(
        "/api/oauth/authorize", params=build_authorize_params(client_id, redirect_uri, **params)
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_authorize_unknown_client(client):
    response = await client.get("/api/oauth/authorize", params=build_authorize_params(UNKNOWN_ID))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_get_consent_details(admin_client, oauth_client):
    client_id, _ = oauth_client

    response = await admin_client.get("/api/oauth/consent", params=build_consent(client_id))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"clientName": "Claude"}


@pytest.mark.parametrize("port", [3118, 49152])
async def test_grant_consent_to_loopback_redirect_uri(admin_client, oauth_client, port):
    client_id, _ = oauth_client
    redirect_uri = f"http://localhost:{port}/callback"

    response = await admin_client.post("/api/oauth/consent", json=build_consent(client_id, redirect_uri))

    assert response.status_code == status.HTTP_200_OK
    redirect_url = urlsplit(response.json()["redirectUrl"])
    assert f"{redirect_url.scheme}://{redirect_url.netloc}{redirect_url.path}" == redirect_uri
    assert parse_qs(redirect_url.query)["state"] == [STATE]


async def test_grant_consent_as_normal_user(admin_client, user_client, oauth_client):
    client_id, _ = oauth_client

    response = await user_client.post("/api/oauth/consent", json=build_consent(client_id))

    assert response.status_code == status.HTTP_403_FORBIDDEN


async def test_exchange_code_and_refresh_tokens(admin_client, client, oauth_client):
    client_id, secret = oauth_client
    code = await grant_authorization_code(admin_client, client_id)

    response = await exchange_code(client, client_id, secret, code)

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["Cache-Control"] == "no-store"
    tokens = response.json()
    assert tokens["token_type"] == "Bearer"
    assert tokens["expires_in"] == 3600

    basic_credentials = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    response = await client.post(
        "/api/oauth/token",
        headers={"Authorization": f"Basic {basic_credentials}"},
        data={"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["refresh_token"] != tokens["refresh_token"]

    response = await request_tokens(
        client, client_id, secret, grant_type="refresh_token", refresh_token=tokens["refresh_token"]
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"error": "invalid_grant"}


async def test_exchange_code_twice(admin_client, client, oauth_client):
    client_id, secret = oauth_client
    code = await grant_authorization_code(admin_client, client_id)
    await exchange_code(client, client_id, secret, code)

    response = await exchange_code(client, client_id, secret, code)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"error": "invalid_grant"}


@pytest.mark.parametrize(
    ("form", "expected_error"),
    [
        ({"code_verifier": "x" * 43}, "invalid_grant"),
        ({"redirect_uri": "http://localhost:3118/callback"}, "invalid_grant"),
        ({"code": "unknown"}, "invalid_grant"),
        ({"grant_type": "password"}, "unsupported_grant_type"),
    ],
    ids=("wrong verifier", "other redirect uri", "unknown code", "unsupported grant"),
)
async def test_exchange_invalid_code(admin_client, client, oauth_client, form, expected_error):
    client_id, secret = oauth_client
    code = await grant_authorization_code(admin_client, client_id)
    valid_form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": CODE_VERIFIER,
    }

    response = await request_tokens(client, client_id, secret, **{**valid_form, **form})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"error": expected_error}


async def test_exchange_code_with_wrong_secret(admin_client, client, oauth_client):
    client_id, _ = oauth_client
    code = await grant_authorization_code(admin_client, client_id)

    response = await exchange_code(client, client_id, "wrong-secret", code)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"error": "invalid_client"}


async def test_exchange_code_of_other_client(admin_client, client, oauth_client):
    client_id, _ = oauth_client
    other_client_id, other_secret = await create_oauth_client(admin_client, "Other")
    code = await grant_authorization_code(admin_client, client_id)

    response = await exchange_code(client, other_client_id, other_secret, code)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"error": "invalid_grant"}


async def test_demoted_admin_cannot_manage_clients_or_grant_consent(admin_client, oauth_client, session_maker):
    client_id, _ = oauth_client
    async with session_maker.begin() as session:
        await session.execute(update(users_table).where(users_table.c.id == ADMIN_ID).values(is_admin=False))

    for response in (
        await admin_client.get("/api/oauth-clients"),
        await admin_client.post("/api/oauth-clients", json={"name": "Another"}),
        await admin_client.post("/api/oauth/consent", json=build_consent(client_id)),
        await admin_client.delete(f"/api/oauth-clients/{client_id}"),
    ):
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("resource", [None, "https://other.example/api/mcp"])
async def test_authorize_requires_mcp_resource(client, oauth_client, resource):
    client_id, _ = oauth_client
    params = build_authorize_params(client_id)
    del params["resource"]
    if resource is not None:
        params["resource"] = resource
    response = await client.get("/api/oauth/authorize", params=params)
    assert response.status_code == status.HTTP_400_BAD_REQUEST


async def test_resource_binding_across_consent_exchange_and_refresh(client, admin_client, oauth_client):
    client_id, secret = oauth_client
    wrong_target = "https://other.example/api/mcp"
    consent = {**build_consent(client_id), "resource": wrong_target}
    assert (await admin_client.post("/api/oauth/consent", json=consent)).status_code == status.HTTP_400_BAD_REQUEST

    code = await grant_authorization_code(admin_client, client_id)
    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": CODE_VERIFIER,
    }
    for target in ({}, {"resource": wrong_target}):
        response = await client.post(
            "/api/oauth/token", data={"client_id": str(client_id), "client_secret": secret, **form, **target}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"error": "invalid_target"}

    tokens = (await exchange_code(client, client_id, secret, code)).json()
    refresh = {"grant_type": "refresh_token", "refresh_token": tokens["refresh_token"]}
    response = await request_tokens(client, client_id, secret, resource=wrong_target, **refresh)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"error": "invalid_target"}
    assert (await request_tokens(client, client_id, secret, **refresh)).status_code == status.HTTP_200_OK


async def test_token_endpoint_errors(client, oauth_client):
    client_id, secret = oauth_client
    form = {"client_id": str(client_id), "client_secret": secret}
    response = await client.post("/api/oauth/token", data=form)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"error": "invalid_request"}

    basic = base64.b64encode(f"{client_id}:{secret}".encode()).decode()
    response = await client.post(
        "/api/oauth/token", data={**form, "grant_type": "refresh_token"}, headers={"Authorization": f"Basic {basic}"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"error": "invalid_request"}

    response = await client.post(
        "/api/oauth/token", data={"grant_type": "refresh_token"}, headers={"Authorization": "Basic invalid"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"error": "invalid_client"}
    assert response.headers["WWW-Authenticate"].startswith("Basic ")
