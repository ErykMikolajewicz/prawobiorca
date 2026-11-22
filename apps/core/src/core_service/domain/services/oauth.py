import base64
import hashlib
import hmac
import re
from collections.abc import Collection
from urllib.parse import urlencode, urlsplit

LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1"})

PKCE_VALUE_PATTERN = r"^[A-Za-z0-9\-._~]{43,128}$"


def is_redirect_uri_allowed(redirect_uri: str, allowed_redirect_uris: Collection[str]) -> bool:
    try:
        uri = urlsplit(redirect_uri)
        port = uri.port
    except ValueError:
        return False

    if not uri.hostname or uri.username is not None or "#" in redirect_uri or uri.scheme not in {"http", "https"}:
        return False
    if redirect_uri in allowed_redirect_uris:
        return True
    if uri.hostname not in LOOPBACK_HOSTS or port is None:
        return False

    # Only the port may differ from the registered loopback callback.
    for allowed_uri in allowed_redirect_uris:
        registered = urlsplit(allowed_uri)
        if registered.hostname == uri.hostname and registered.username is None and not registered.query:
            with_port = registered._replace(netloc=f"{uri.hostname}:{port}")
            if redirect_uri == with_port.geturl():
                return True
    return False


def verify_pkce_s256(code_verifier: str, code_challenge: str) -> bool:
    if re.fullmatch(PKCE_VALUE_PATTERN, code_verifier) is None:
        return False

    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    expected_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return hmac.compare_digest(expected_challenge, code_challenge)


def build_redirect_url(redirect_uri: str, parameters: dict[str, str | None]) -> str:
    query = urlencode({name: value for name, value in parameters.items() if value is not None})
    separator = "&" if urlsplit(redirect_uri).query else "?"
    return f"{redirect_uri}{separator}{query}"
