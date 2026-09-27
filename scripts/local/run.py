import subprocess
import time
from pathlib import Path

from manifests import MANIFESTS, MIGRATIONS

IGNORED_DIRS = {".venv", "__pycache__"}
POSTGRES_CONTAINER = "postgres-postgres"
MIGRATIONS_CONTAINER = "prawobiorca-migrations-prawobiorca-migrations"
POSTGRES_READY_TIMEOUT = 60

IMAGES = (
    (
        "prawobiorca-backend",
        "core-service",
        (
            "core-service/Containerfile",
            "core-service/pyproject.toml",
            "core-service/uv.lock",
            "core-service/src",
            "core-service/alembic",
            "core-service/alembic.ini",
        ),
    ),
    ("extraction-service", "extraction-service", ("extraction-service",)),
    ("embedding-service", "embedding-service", ("embedding-service/Containerfile",)),
    (
        "prawobiorca-frontend",
        "prawobiorca-frontend",
        (
            "prawobiorca-frontend/Containerfile",
            "prawobiorca-frontend/package.json",
            "prawobiorca-frontend/pnpm-lock.yaml",
            "prawobiorca-frontend/src",
        ),
    ),
)


def image_created_at(name: str) -> float | None:
    result = subprocess.run(
        ["podman", "image", "inspect", name, "--format", "{{.Created.Unix}}"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return float(result.stdout.strip())


def newest_source_change(sources: tuple[str, ...]) -> float:
    newest = 0.0
    for source in sources:
        path = Path(source)
        if path.is_file():
            newest = max(newest, path.stat().st_mtime)
            continue
        for entry in path.rglob("*"):
            if IGNORED_DIRS & set(entry.parts) or not entry.is_file():
                continue
            newest = max(newest, entry.stat().st_mtime)
    return newest


def build_images():
    for name, context, sources in IMAGES:
        created_at = image_created_at(f"localhost/{name}:latest") or image_created_at(f"{name}:latest")
        if created_at is None:
            print(f"Building {name} image...")
        elif newest_source_change(sources) > created_at:
            print(f"Sources changed since {name} image was built, rebuilding...")
        else:
            continue
        subprocess.run(["podman", "image", "build", f"--tag={name}", context], check=True)


def wait_for_postgres():
    for _ in range(POSTGRES_READY_TIMEOUT):
        result = subprocess.run(
            ["podman", "exec", POSTGRES_CONTAINER, "pg_isready", "-h", "localhost", "-U", "postgres"],
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("Postgres is not ready.")


def wait_for_migrations():
    result = subprocess.run(["podman", "wait", MIGRATIONS_CONTAINER], capture_output=True, text=True, check=True)
    if result.stdout.strip() != "0":
        raise RuntimeError(f"Migrations failed, check logs: podman logs {MIGRATIONS_CONTAINER}")


def play_manifest(manifest: Path, configmaps: tuple[Path, ...]):
    print(f"Applying {manifest.name}...")
    command = ["podman", "kube", "play", "--replace", "--network", "prawobiorca-net"]
    for configmap in configmaps:
        command += ["--configmap", str(configmap)]
    command.append(str(manifest))
    subprocess.run(command, check=True)


def main():
    build_images()

    subprocess.run(["podman", "network", "create", "--ignore", "prawobiorca-net"], check=True)

    print("Deploying local environment with podman kube play...")
    for manifest, configmaps in MANIFESTS:
        if manifest == MIGRATIONS:
            wait_for_postgres()
        play_manifest(manifest, configmaps)
        if manifest == MIGRATIONS:
            wait_for_migrations()

    print("\nLocal deployment is running.")
    print("Nginx Ingress available at http://localhost:8080")
    print("  - Frontend: http://localhost:8080/")
    print("  - API:      http://localhost:8080/api")
    print("  - Docs:     http://localhost:8080/docs")
    print("  - OpenAPI:  http://localhost:8080/openapi.json")
    print("  - Storage:  http://localhost:8080/storage/")
    print("\nTo stop the deployment run: poe run_locally_down")


if __name__ == "__main__":
    main()
