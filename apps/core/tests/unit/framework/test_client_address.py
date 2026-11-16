import pytest

from core_service.framework.dependencies.client_address import UNKNOWN_ADDRESS, resolve_client_ip

PEER_ADDRESS = "10.0.0.5"
CLIENT_ADDRESS = "203.0.113.7"
LOAD_BALANCER_ADDRESS = "34.120.0.1"


def test_peer_address_without_trusted_proxies():
    assert resolve_client_ip(PEER_ADDRESS, [CLIENT_ADDRESS], 0) == PEER_ADDRESS


def test_address_added_by_single_trusted_proxy():
    assert resolve_client_ip(PEER_ADDRESS, [CLIENT_ADDRESS], 1) == CLIENT_ADDRESS


def test_address_sent_by_client_is_ignored():
    forwarded_for = [f"1.2.3.4, {CLIENT_ADDRESS}, {LOAD_BALANCER_ADDRESS}"]

    assert resolve_client_ip(PEER_ADDRESS, forwarded_for, 2) == CLIENT_ADDRESS


def test_addresses_from_repeated_headers_are_joined():
    assert resolve_client_ip(PEER_ADDRESS, ["1.2.3.4", f"{CLIENT_ADDRESS}, {LOAD_BALANCER_ADDRESS}"], 2) == (
        CLIENT_ADDRESS
    )


@pytest.mark.parametrize(
    "forwarded_for", [[], [LOAD_BALANCER_ADDRESS], ["not-an-address, 34.120.0.1"]], ids=("none", "too few", "invalid")
)
def test_peer_address_when_forwarded_address_is_missing(forwarded_for):
    assert resolve_client_ip(PEER_ADDRESS, forwarded_for, 2) == PEER_ADDRESS


def test_ipv6_address_is_reduced_to_its_network():
    assert resolve_client_ip(PEER_ADDRESS, ["2001:db8:1:2:3:4:5:6"], 1) == "2001:db8:1:2::"


def test_ipv4_mapped_address_is_reduced_to_ipv4():
    assert resolve_client_ip(f"::ffff:{CLIENT_ADDRESS}", [], 0) == CLIENT_ADDRESS


@pytest.mark.parametrize("peer_address", [None, "testclient"], ids=("missing", "invalid"))
def test_unknown_address(peer_address):
    assert resolve_client_ip(peer_address, [], 0) == UNKNOWN_ADDRESS
