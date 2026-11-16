from ipaddress import IPv6Address, IPv6Network, ip_address
from typing import Annotated

from fastapi import Depends, Request

from core_service.shared.settings.application import app_settings

UNKNOWN_ADDRESS = "unknown"

IPV6_CLIENT_PREFIX_LENGTH = 64


def _normalize_address(address: str) -> str | None:
    try:
        parsed_address = ip_address(address)
    except ValueError:
        return None

    if isinstance(parsed_address, IPv6Address):
        if parsed_address.ipv4_mapped is not None:
            return str(parsed_address.ipv4_mapped)
        network = IPv6Network((parsed_address, IPV6_CLIENT_PREFIX_LENGTH), strict=False)
        return str(network.network_address)

    return str(parsed_address)


def resolve_client_ip(peer_address: str | None, forwarded_for: list[str], trusted_proxies_count: int) -> str:
    forwarded_addresses = [address.strip() for header in forwarded_for for address in header.split(",")]

    client_address = None
    if 0 < trusted_proxies_count <= len(forwarded_addresses):
        client_address = _normalize_address(forwarded_addresses[-trusted_proxies_count])
    if client_address is None and peer_address is not None:
        client_address = _normalize_address(peer_address)

    return client_address or UNKNOWN_ADDRESS


def get_trusted_proxies_count() -> int:
    return app_settings.TRUSTED_PROXIES_COUNT


def get_client_ip(request: Request, trusted_proxies_count: Annotated[int, Depends(get_trusted_proxies_count)]) -> str:
    peer_address = request.client.host if request.client is not None else None
    return resolve_client_ip(peer_address, request.headers.getlist("x-forwarded-for"), trusted_proxies_count)
