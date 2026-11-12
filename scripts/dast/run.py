"""Scan the disposable local E2E instance. Never point this at a shared database."""

import json
import secrets
import shutil
import subprocess
import urllib.request
from pathlib import Path

TARGET = "http://localhost:8080"
# Pinned scanner release; update after validating the plan with the new image.
ZAP_IMAGE = "ghcr.io/zaproxy/zaproxy:2.17.0"
WORK_DIR = Path(".cache/dast")
EXCLUDED_PATHS = {
    "/api/auth/login",
    "/api/auth/logout",
    "/api/auth/refresh",
    "/api/accounts/register",
}
EXCLUDED_SUFFIXES = ("/confirm-upload", "/preparation-retry", "/description-generation")


def scan_path(path: str) -> bool:
    return (
        path.startswith("/api/")
        and path not in EXCLUDED_PATHS
        and not path.endswith(EXCLUDED_SUFFIXES)
        and not (path.startswith("/api/cases/") and "/applications" in path)
    )


def prepare() -> Path:
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    report_dir = WORK_DIR / "report"
    # Remove stale reports so an unsuccessful scan cannot publish last run's results.
    if report_dir.exists():
        shutil.rmtree(report_dir)
    report_dir.mkdir()
    schema = json.loads(Path("apps/core/openapi.json").read_text())
    schema["servers"] = [{"url": TARGET}]
    schema["paths"] = {path: item for path, item in schema["paths"].items() if scan_path(path)}
    (WORK_DIR / "openapi.json").write_text(json.dumps(schema))
    shutil.copyfile(Path(__file__).with_name("plan.yaml"), WORK_DIR / "plan.yaml")

    username = f"dast-{secrets.token_hex(8)}"
    password = f"Aa1!{secrets.token_hex(12)}"
    request = urllib.request.Request(
        f"{TARGET}/api/accounts/register",
        data=json.dumps({"username": username, "password": password}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.status != 201:
            raise RuntimeError(f"DAST user registration returned {response.status}")
    credentials = WORK_DIR / "credentials.env"
    credentials.write_text(f"DAST_USERNAME={username}\nDAST_PASSWORD={password}\n")
    credentials.chmod(0o600)
    return credentials


def main() -> None:
    credentials = prepare()
    try:
        subprocess.run(
            [
                "podman",
                "run",
                "--rm",
                "--name",
                "prawobiorca-dast",
                "--network=host",
                # Map the runner's UID to the image's zap user (also on GitHub-hosted runners).
                "--userns=keep-id:uid=1000,gid=1000",
                "--env-file",
                str(credentials),
                "-v",
                f"{WORK_DIR.resolve()}:/zap/wrk:rw",
                ZAP_IMAGE,
                "zap.sh",
                "-cmd",
                "-port",
                "8090",
                "-autorun",
                "/zap/wrk/plan.yaml",
            ],
            check=True,
            timeout=35 * 60,
        )
        for name in ("report.html", "report.json"):
            if not (WORK_DIR / "report" / name).is_file():
                raise RuntimeError(f"ZAP did not generate {name}")
    finally:
        credentials.unlink(missing_ok=True)
        subprocess.run(["podman", "rm", "-f", "--ignore", "prawobiorca-dast"], check=False)


if __name__ == "__main__":
    main()
