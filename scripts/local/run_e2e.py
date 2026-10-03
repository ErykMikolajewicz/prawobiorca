import subprocess
import time
import urllib.request

from manifests import BACKEND, E2E_MANIFESTS, MIGRATIONS
from run import play_manifest, wait_for_migrations, wait_for_postgres

EMBEDDING_SERVICE_HEALTH_URL = "http://localhost:8081/v2/health/ready"
EMBEDDING_SERVICE_READY_TIMEOUT = 120
APPLICATION_URL = "http://localhost:8080/openapi.json"
APPLICATION_READY_TIMEOUT = 60


def wait_for_url(url: str, timeout: int, service_name: str):
    for _ in range(timeout):
        try:
            with urllib.request.urlopen(url):
                return
        except OSError:
            time.sleep(1)
    raise RuntimeError(f"{service_name} is not ready.")


def main():
    subprocess.run(["podman", "network", "create", "--ignore", "prawobiorca-net"], check=True)

    print("Deploying e2e environment with podman kube play...")
    for manifest, configmaps in E2E_MANIFESTS:
        if manifest == MIGRATIONS:
            wait_for_postgres()
        if manifest == BACKEND:
            wait_for_url(EMBEDDING_SERVICE_HEALTH_URL, EMBEDDING_SERVICE_READY_TIMEOUT, "Embedding service")
            subprocess.run(["just", "init-e2e-regulation"], check=True)
        play_manifest(manifest, configmaps)
        if manifest == MIGRATIONS:
            wait_for_migrations()

    wait_for_url(APPLICATION_URL, APPLICATION_READY_TIMEOUT, "Application")

    print("\nE2E environment is running at http://localhost:8080")
    print("To stop the deployment run: just run-locally-down")


if __name__ == "__main__":
    main()
