"""Common pytest fixtures for integration tests.

These fixtures handle container initialization of the extraction service.
"""

import os
import subprocess
from collections.abc import Generator

import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.wait_strategies import HttpWaitStrategy

from tests.consts import EXTRACTION_SERVICE_IMAGE_TAG, EXTRACTION_SERVICE_PORT, STARTUP_TIMEOUT


@pytest.fixture(scope="session", autouse=True)
def configure_podman():
    subprocess.run(["systemctl", "--user", "enable", "--now", "podman.socket"], check=True)

    uid = os.getuid()
    podman_sock = f"unix:///run/user/{uid}/podman/podman.sock"

    os.environ["DOCKER_HOST"] = podman_sock


@pytest.fixture(scope="session")
def extraction_service_container() -> Generator[DockerContainer]:
    wait_strategy = HttpWaitStrategy(
        EXTRACTION_SERVICE_PORT,
        "/health",
    ).with_startup_timeout(STARTUP_TIMEOUT)

    with (
        DockerContainer(EXTRACTION_SERVICE_IMAGE_TAG)
        .with_exposed_ports(EXTRACTION_SERVICE_PORT)
        .waiting_for(wait_strategy)
    ) as extraction_service:
        yield extraction_service


@pytest.fixture(scope="session")
def parse_regulation_url(extraction_service_container: DockerContainer) -> str:
    host = extraction_service_container.get_container_host_ip()
    port = extraction_service_container.get_exposed_port(EXTRACTION_SERVICE_PORT)

    return f"http://{host}:{port}/parse-regulation"
