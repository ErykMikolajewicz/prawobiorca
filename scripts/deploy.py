import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

OVERLAYS_DIR = Path("deploy/overlays")
PHASE_LABEL = "deploy-phase"
APP_PHASE = "app"
IMAGE_PATTERN = re.compile(r"(?P<name>[\w-]+)=(?P<repository>.+?)(?::(?P<tag>[\w.-]+)|@(?P<digest>sha256:[0-9a-f]+))")
ROLLOUT_TIMEOUT = 300
JOB_TIMEOUT = 600
JOB_POLL_INTERVAL = 2


@dataclass(frozen=True)
class Environment:
    job_phases: tuple[str, ...]
    context: str | None = None


ENVIRONMENTS = {
    "gcp": Environment(job_phases=("migrations",)),
    "local": Environment(job_phases=("migrations", "bucket"), context="kind-prawobiorca"),
    "e2e": Environment(job_phases=("migrations", "bucket", "seed"), context="kind-prawobiorca-e2e"),
}


class DeploymentError(Exception):
    pass


def image_override(image: str) -> dict[str, str]:
    match = IMAGE_PATTERN.fullmatch(image)
    if match is None:
        raise argparse.ArgumentTypeError(f"expected <name>=<repository>:<tag> or <name>=<repository>@<digest>: {image}")
    override = {"name": f"prawobiorca/{match['name']}", "newName": match["repository"]}
    if match["digest"]:
        return override | {"digest": match["digest"]}
    return override | {"newTag": match["tag"]}


def resolve_context(environment: str, requested: str | None) -> str:
    required = ENVIRONMENTS[environment].context
    if required is None:
        if requested is None:
            raise SystemExit(f"Deploying {environment} requires an explicit --context.")
        return requested
    if requested not in (None, required):
        raise SystemExit(f"{environment} can be deployed only to the {required} context.")
    return required


def render(environment: str, images: list[dict[str, str]], directory: Path) -> Path:
    overlay = os.path.relpath(OVERLAYS_DIR / environment, directory)
    kustomization = {"resources": [overlay], "images": images}
    (directory / "kustomization.yaml").write_text(json.dumps(kustomization))
    manifests = directory / "manifests.yaml"
    with manifests.open("w") as output:
        subprocess.run(
            ["kubectl", "kustomize", "--load-restrictor", "LoadRestrictionsNone", str(directory)],
            check=True,
            stdout=output,
        )
    return manifests


def kubectl(context: str, *arguments: str):
    subprocess.run(["kubectl", "--context", context, *arguments], check=True)


def kubectl_output(context: str, *arguments: str) -> str:
    command = ["kubectl", "--context", context, *arguments]
    return subprocess.run(command, check=True, stdout=subprocess.PIPE, text=True).stdout


def apply(context: str, manifests: Path, selector: str) -> list[str]:
    resources = kubectl_output(
        context, "apply", "--filename", str(manifests), "--selector", selector, "--output", "name"
    ).split()
    print("\n".join(resources))
    return resources


def wait_for_rollouts(context: str, resources: list[str]):
    for resource in resources:
        if resource.startswith("deployment.apps/"):
            kubectl(context, "rollout", "status", resource, f"--timeout={ROLLOUT_TIMEOUT}s")


def wait_for_job(context: str, job: str):
    deadline = time.monotonic() + JOB_TIMEOUT
    while time.monotonic() < deadline:
        conditions = kubectl_output(
            context, "get", job, "--output", "jsonpath={.status.conditions[?(@.status=='True')].type}"
        ).split()
        if "Complete" in conditions:
            return
        if "Failed" in conditions:
            raise DeploymentError(f"{job} failed.")
        time.sleep(JOB_POLL_INTERVAL)
    raise DeploymentError(f"{job} did not finish in {JOB_TIMEOUT} seconds.")


def run_job(context: str, manifests: Path, phase: str):
    selector = f"{PHASE_LABEL}={phase}"
    kubectl(context, "delete", "--filename", str(manifests), "--selector", selector, "--ignore-not-found")
    (job,) = apply(context, manifests, selector)
    wait_for_job(context, job)


def deploy(context: str, manifests: Path, job_phases: tuple[str, ...]):
    print("Applying configuration and dependencies...")
    wait_for_rollouts(context, apply(context, manifests, f"!{PHASE_LABEL}"))
    for phase in job_phases:
        print(f"Running {phase}...")
        run_job(context, manifests, phase)
    print("Applying application...")
    wait_for_rollouts(context, apply(context, manifests, f"{PHASE_LABEL}={APP_PHASE}"))
    print("Deployment completed.")


def print_diagnostics(context: str):
    for arguments in (
        ("get", "pods", "--output", "wide"),
        ("get", "events", "--sort-by", ".lastTimestamp"),
        ("logs", "--selector", "app=prawobiorca", "--all-containers", "--prefix", "--tail", "50", "--ignore-errors"),
    ):
        subprocess.run(["kubectl", "--context", context, *arguments], check=False)


def main():
    parser = argparse.ArgumentParser(description="Deploy a Kustomize overlay from deploy/overlays.")
    parser.add_argument("environment", choices=ENVIRONMENTS)
    parser.add_argument(
        "--image",
        action="append",
        default=[],
        type=image_override,
        metavar="NAME=REFERENCE",
        help="image replacing the logical prawobiorca/NAME, for example core=registry/core:tag",
    )
    parser.add_argument("--context", help="kubectl context, required for gcp and fixed for the kind environments")
    parser.add_argument("--render", action="store_true", help="print the rendered manifests instead of deploying them")
    arguments = parser.parse_args()

    with tempfile.TemporaryDirectory() as directory:
        manifests = render(arguments.environment, arguments.image, Path(directory))
        if arguments.render:
            print(manifests.read_text(), end="")
            return

        context = resolve_context(arguments.environment, arguments.context)
        try:
            deploy(context, manifests, ENVIRONMENTS[arguments.environment].job_phases)
        except (subprocess.CalledProcessError, DeploymentError) as error:
            print_diagnostics(context)
            sys.exit(f"Deployment failed: {error}")


if __name__ == "__main__":
    main()
