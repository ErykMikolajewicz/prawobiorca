import argparse
import subprocess
import sys
import time
from pathlib import Path

CLUSTER_CONFIG = Path("deploy/kind/cluster.yaml")
LLM_MODELS_DIR = Path(".llm-models")
DEV_VOLUMES = ("pg-data", "rustfs-data")
DEV_VOLUMES_DIR = "/var/lib/dev-volumes"
DEV_CONTAINERS = ("postgres_db_prawobiorca", "rustfs")
API_READY_TIMEOUT = 120

CLUSTERS = {"local": "prawobiorca", "e2e": "prawobiorca-e2e"}
STOP_COMMANDS = {"prawobiorca": "just run-locally-down", "prawobiorca-e2e": "just run-e2e-env-down"}
IMAGES = {
    "local": ("core", "web", "embedding", "extraction"),
    "e2e": ("core", "web", "embedding"),
}
SHARES_DEV_VOLUMES = {"local": True, "e2e": False}


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


def running_dev_containers() -> list[str]:
    result = subprocess.run(["podman", "ps", "--format", "{{.Names}}"], capture_output=True, text=True, check=True)
    return [name for name in result.stdout.split() if name in DEV_CONTAINERS]


def volume_mountpoint(volume: str) -> str:
    subprocess.run(["podman", "volume", "create", "--ignore", volume], capture_output=True, check=True)
    result = subprocess.run(
        ["podman", "volume", "inspect", volume, "--format", "{{.Mountpoint}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def mounts_dev_volumes(cluster: str) -> bool:
    result = subprocess.run(
        ["podman", "container", "inspect", node(cluster), "--format", "{{range .Mounts}}{{.Destination}} {{end}}"],
        capture_output=True,
        text=True,
        check=True,
    )
    return all(f"{DEV_VOLUMES_DIR}/{volume}" in result.stdout.split() for volume in DEV_VOLUMES)


def cluster_config(shares_dev_volumes: bool) -> str:
    config = CLUSTER_CONFIG.read_text()
    if not shares_dev_volumes:
        return config
    return config + "".join(
        f"      - hostPath: {volume_mountpoint(volume)}\n        containerPath: {DEV_VOLUMES_DIR}/{volume}\n"
        for volume in DEV_VOLUMES
    )


def ensure_cluster(cluster: str, shares_dev_volumes: bool):
    for other, stop_command in STOP_COMMANDS.items():
        if other != cluster and node_running(other):
            raise SystemExit(f"Cluster {other} is running and uses the same ports 8080 and 9000. Run: {stop_command}")
    if shares_dev_volumes and (containers := running_dev_containers()):
        raise SystemExit(f"just dev is running and uses the same volumes. Run: podman stop {' '.join(containers)}")

    LLM_MODELS_DIR.mkdir(exist_ok=True)
    if not cluster_exists(cluster):
        subprocess.run(
            ["kind", "create", "cluster", "--name", cluster, "--config", "/dev/stdin"],
            input=cluster_config(shares_dev_volumes),
            text=True,
            check=True,
        )
        return
    if shares_dev_volumes and not mounts_dev_volumes(cluster):
        raise SystemExit(f"Cluster {cluster} was created without the volumes of just dev. Run: just run-locally-reset")
    if not node_running(cluster):
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

    ensure_cluster(cluster, SHARES_DEV_VOLUMES[environment])

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
