import pytest

from core_service.domain.services.oauth import build_redirect_url, is_redirect_uri_allowed, verify_pkce_s256

ALLOWED_REDIRECT_URIS = ("https://claude.ai/api/mcp/auth_callback", "http://localhost/callback")

CODE_VERIFIER = "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
CODE_CHALLENGE = "E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM"


@pytest.mark.parametrize(
    "redirect_uri",
    [
        "https://claude.ai/api/mcp/auth_callback",
        "http://localhost/callback",
        "http://localhost:3118/callback",
    ],
    ids=("exact", "loopback", "loopback with port"),
)
def test_redirect_uri_allowed(redirect_uri):
    assert is_redirect_uri_allowed(redirect_uri, ALLOWED_REDIRECT_URIS)


@pytest.mark.parametrize(
    "redirect_uri",
    [
        "https://claude.ai:8443/api/mcp/auth_callback",
        "https://claude.ai/api/mcp/auth_callback?next=/",
        "https://attacker.example/api/mcp/auth_callback",
        "https://localhost:3118/callback",
        "http://127.0.0.1:3118/callback",
        "http://localhost:3118/other",
        "http://localhost:3118/callback?next=/",
        "http://localhost:3118/callback#fragment",
        "http://user@localhost:3118/callback",
        "http://localhost.attacker.example:3118/callback",
        "http://[localhost/callback",
        "http://localhost:port/callback",
        "http://localhost:65536/callback",
    ],
    ids=(
        "other port",
        "added query",
        "other host",
        "loopback other scheme",
        "loopback other host",
        "loopback other path",
        "loopback query",
        "loopback fragment",
        "loopback user info",
        "loopback subdomain",
        "invalid authority",
        "non-numeric port",
        "port out of range",
    ),
)
def test_redirect_uri_not_allowed(redirect_uri):
    assert not is_redirect_uri_allowed(redirect_uri, ALLOWED_REDIRECT_URIS)


def test_verify_pkce_s256():
    assert verify_pkce_s256(CODE_VERIFIER, CODE_CHALLENGE)


@pytest.mark.parametrize(
    "code_verifier",
    ["x" * 43, CODE_VERIFIER[:42], CODE_VERIFIER + "ż", CODE_VERIFIER + "x" * 86],
    ids=("other verifier", "too short", "forbidden character", "too long"),
)
def test_verify_pkce_s256_with_invalid_verifier(code_verifier):
    assert not verify_pkce_s256(code_verifier, CODE_CHALLENGE)


@pytest.mark.parametrize(
    ("redirect_uri", "expected_url"),
    [
        ("https://claude.ai/callback", "https://claude.ai/callback?code=abc&state=x+y"),
        ("https://claude.ai/callback?tenant=1", "https://claude.ai/callback?tenant=1&code=abc&state=x+y"),
    ],
    ids=("without query", "with query"),
)
def test_build_redirect_url(redirect_uri, expected_url):
    assert build_redirect_url(redirect_uri, {"code": "abc", "state": "x y", "error": None}) == expected_url
