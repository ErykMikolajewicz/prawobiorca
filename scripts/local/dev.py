import os
import signal
import subprocess
import time

RUSTFS_CORS_ALLOWED_ORIGINS = "http://localhost:4173,http://localhost:5173,http://localhost:8080"
WORKER_SHUTDOWN_TIMEOUT = 3
POSTGRES_READY_TIMEOUT = 60


def run_command(cmd):
    return subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)


def container_exists(name):
    result = run_command('podman ps -a --format "{{.Names}}"')
    return name in result.stdout.splitlines()


def container_running(name):
    result = run_command('podman ps --format "{{.Names}}"')
    return name in result.stdout.splitlines()


def run_container_if_not_running(name, args):
    if container_exists(name):
        if container_running(name):
            print(f"Container {name} is already running - pass.")
        else:
            print(f"Container {name} already exists, but not running, launching.")
            subprocess.run(["podman", "start", name], check=True)
    else:
        print(f"Create and launch container {name}.")
        cmd = f"podman run -d --name {name} {args}"
        subprocess.run(cmd, shell=True, check=True)


def wait_for_postgres(name):
    for _ in range(POSTGRES_READY_TIMEOUT):
        result = subprocess.run(
            ["podman", "exec", name, "pg_isready", "-h", "localhost", "-U", "postgres"],
            capture_output=True,
        )
        if result.returncode == 0:
            return
        time.sleep(1)
    raise RuntimeError("Postgres is not ready.")


def run_migrations():
    print("Running migrations.")
    subprocess.run(["alembic", "upgrade", "head"], check=True)


def run_worker():
    print("Launching taskiq worker.")
    # Own session, so Ctrl+C in the terminal does not reach the worker - stop_worker owns its lifecycle.
    return subprocess.Popen(
        ["taskiq", "worker", "src.framework.workers.regulations:broker", "--reload", "--reload-dir", "src"],
        start_new_session=True,
    )


def stop_worker(worker):
    print("Stopping taskiq worker.")
    # The whole group, because taskiq leaves worker and forkserver children behind.
    process_group = os.getpgid(worker.pid)
    os.killpg(process_group, signal.SIGTERM)
    try:
        worker.wait(timeout=WORKER_SHUTDOWN_TIMEOUT)
    except subprocess.TimeoutExpired:
        os.killpg(process_group, signal.SIGKILL)
        worker.wait()


def main():
    run_container_if_not_running(
        "postgres_db_prawobiorca",
        "-e POSTGRES_PASSWORD=postgres -p 127.0.0.1:5432:5432"
        " -v pg-data:/var/lib/postgresql pgvector:0.8.4-pg18-trixie",
    )
    wait_for_postgres("postgres_db_prawobiorca")
    run_migrations()

    run_container_if_not_running(
        "rustfs",
        f"-e RUSTFS_CORS_ALLOWED_ORIGINS={RUSTFS_CORS_ALLOWED_ORIGINS}"
        " -p 127.0.0.1:9000:9000 -p 127.0.0.1:9001:9001 -v rustfs-data:/data rustfs/rustfs:latest",
    )

    run_container_if_not_running(
        "embedding-service",
        "-p 127.0.0.1:8081:8080 embedding-service"
        " --model_path=/models/mmlw-retrieval-roberta-large-v2 --model_name=mmlw-retrieval-roberta-large-v2"
        " --task=embeddings --pooling=CLS --target_device=CPU --rest_port=8080",
    )
    run_container_if_not_running("extraction-service", "-p 127.0.0.1:8082:8080 extraction-service")
    source_model = os.getenv("OPENVINO_SOURCE_MODEL", "OpenVINO/Qwen2.5-7B-Instruct-int4-ov")
    model_name = os.getenv("OPENVINO_MODEL_NAME", "qwen-2.5-7b-it")
    run_container_if_not_running(
        "llm-service",
        "-p 127.0.0.1:8083:8080 --device /dev/dri"
        " --group-add $(stat -c '%g' /dev/dri/render* | head -n1) -v llm-model:/models"
        " docker.io/openvino/model_server:2026.3-gpu"
        f" --source_model={source_model} --model_name={model_name}"
        " --model_repository_path=/models --task=text_generation"
        " --target_device=AUTO --rest_port=8080",
    )
    run_container_if_not_running("redis", "-p 127.0.0.1:6379:6379 redis:8-alpine")

    worker = run_worker()
    try:
        subprocess.run(
            [
                "granian",
                "--port",
                "8000",
                "--host",
                "127.0.0.1",
                "--interface",
                "asgi",
                "--reload",
                "--access-log",
                "src.main:prawobiorca",
            ],
            check=True,
        )
    except KeyboardInterrupt:
        pass
    finally:
        stop_worker(worker)


if __name__ == "__main__":
    main()
