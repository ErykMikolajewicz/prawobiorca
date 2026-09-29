from pathlib import Path

LOCAL_K8S_DIR = Path("deploy/local")

BACKEND_CONFIG = LOCAL_K8S_DIR / "config.yaml"
NGINX_CONFIG = LOCAL_K8S_DIR / "nginx-config.yaml"

MIGRATIONS = LOCAL_K8S_DIR / "prawobiorca-migrations.yaml"
BACKEND = LOCAL_K8S_DIR / "prawobiorca-backend.yaml"

MANIFESTS: tuple[tuple[Path, tuple[Path, ...]], ...] = (
    (LOCAL_K8S_DIR / "secrets.yaml", ()),
    (LOCAL_K8S_DIR / "postgres.yaml", ()),
    (LOCAL_K8S_DIR / "redis.yaml", ()),
    (LOCAL_K8S_DIR / "rustfs.yaml", ()),
    (LOCAL_K8S_DIR / "embedding-service.yaml", ()),
    (LOCAL_K8S_DIR / "extraction-service.yaml", ()),
    (LOCAL_K8S_DIR / "llm-service.yaml", ()),
    (MIGRATIONS, (BACKEND_CONFIG,)),
    (BACKEND, (BACKEND_CONFIG,)),
    (LOCAL_K8S_DIR / "prawobiorca-worker.yaml", (BACKEND_CONFIG,)),
    (LOCAL_K8S_DIR / "prawobiorca-frontend.yaml", ()),
    (LOCAL_K8S_DIR / "nginx.yaml", (NGINX_CONFIG,)),
)

E2E_MANIFESTS: tuple[tuple[Path, tuple[Path, ...]], ...] = (
    (LOCAL_K8S_DIR / "secrets.yaml", ()),
    (LOCAL_K8S_DIR / "postgres.yaml", ()),
    (LOCAL_K8S_DIR / "redis.yaml", ()),
    (LOCAL_K8S_DIR / "rustfs.yaml", ()),
    (LOCAL_K8S_DIR / "embedding-service.yaml", ()),
    (MIGRATIONS, (BACKEND_CONFIG,)),
    (BACKEND, (BACKEND_CONFIG,)),
    (LOCAL_K8S_DIR / "prawobiorca-frontend.yaml", ()),
    (LOCAL_K8S_DIR / "nginx.yaml", (NGINX_CONFIG,)),
)
