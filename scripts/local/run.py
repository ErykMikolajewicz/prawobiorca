import argparse
import subprocess
import sys
import time
from pathlib import Path

CLUSTER_CONFIG = Path("deploy/kind/cluster.yaml")
LLM_MODELS_DIR = Path(".llm-models")
API_READY_TIMEOUT = 120

CLUSTERS = {"local": "prawobiorca", "e2e": "prawobiorca-e2e"}
STOP_COMMANDS = {"prawobiorca": "just run-locally-down", "prawobiorca-e2e": "just run-e2e-env-down"}
IMAGES = {
    "local": ("core", "web", "embedding", "extraction"),
    "e2e": ("core", "web", "embedding"),
}


def node(cluster: str) -> str:
    return f"{cluster}-control-plane"


def node_running(cluster: str) -> bool:
    result = subprocess.run(
        ["podman", "container", "inspect", node(cluster), "--format", "{{.State.Running}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() == "true"


def cluster_exists(cluster: str) -> bool:
    result = subprocess.run(["kind", "get", "clusters"], capture_output=True, text=True, check=True)
    return cluster in result.stdout.split()


def wait_for_api(cluster: str):
    for _ in range(API_READY_TIMEOUT):
        result = subprocess.run(
            ["kubectl", "--context", f"kind-{cluster}", "get", "--raw=/readyz"], capture_output=True, check=False
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError(f"Cluster {cluster} is not ready.")


def ensure_cluster(cluster: str):
    for other, stop_command in STOP_COMMANDS.items():
        if other != cluster and node_running(other):
            raise SystemExit(f"Cluster {other} is running and uses the same ports 8080 and 9000. Run: {stop_command}")

    LLM_MODELS_DIR.mkdir(exist_ok=True)
    if not cluster_exists(cluster):
        subprocess.run(["kind", "create", "cluster", "--name", cluster, "--config", str(CLUSTER_CONFIG)], check=True)
    elif not node_running(cluster):
        print(f"Starting cluster {cluster}...")
        subprocess.run(["podman", "start", node(cluster)], check=True)
        wait_for_api(cluster)


def build_image(name: str) -> tuple[str, str]:
    repository = f"localhost/prawobiorca/{name}"
    subprocess.run(["podman", "image", "build", f"--tag={repository}", f"apps/{name}"], check=True)
    image_id = subprocess.run(
        ["podman", "image", "inspect", repository, "--format", "{{.Id}}"], capture_output=True, text=True, check=True
    ).stdout
    return repository, f"{repository}:{image_id[:12]}"


def load_image(cluster: str, repository: str, reference: str):
    loaded = subprocess.run(
        ["podman", "exec", node(cluster), "crictl", "inspecti", "--quiet", reference], capture_output=True, check=False
    )
    if loaded.returncode == 0:
        return

    print(f"Loading {reference} into cluster {cluster}...")
    subprocess.run(["podman", "tag", repository, reference], check=True)
    try:
        with subprocess.Popen(["podman", "save", reference], stdout=subprocess.PIPE) as save:
            subprocess.run(
                ["kind", "load", "image-archive", "/dev/stdin", "--name", cluster], stdin=save.stdout, check=True
            )
        if save.returncode != 0:
            raise RuntimeError(f"Saving {reference} failed.")
    finally:
        subprocess.run(["podman", "untag", reference], check=True)


def main():
    parser = argparse.ArgumentParser(description="Run the application in a local kind cluster.")
    parser.add_argument("environment", choices=CLUSTERS)
    environment = parser.parse_args().environment
    cluster = CLUSTERS[environment]

    ensure_cluster(cluster)

    deploy = [sys.executable, "scripts/deploy.py", environment]
    for name in IMAGES[environment]:
        repository, reference = build_image(name)
        load_image(cluster, repository, reference)
        deploy += ["--image", f"{name}={reference}"]

    result = subprocess.run(deploy, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)

    print("\nThe application is running at http://localhost:8080")
    print("  - Frontend: http://localhost:8080/")
    print("  - API:      http://localhost:8080/api")
    print("  - Docs:     http://localhost:8080/docs")
    print("  - OpenAPI:  http://localhost:8080/openapi.json")
    print("  - Storage:  http://localhost:8080/storage/")
    print(f"\nTo stop it run: {STOP_COMMANDS[cluster]}")


if __name__ == "__main__":
    main()
