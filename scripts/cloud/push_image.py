import argparse
import subprocess

import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request

IMAGES_NAMES = (
    "core",
    "extraction",
    "embedding",
    "web",
)

parser = argparse.ArgumentParser(description="Script to actualize image in artifact registry.")

parser.add_argument("image_name", help="Name of image to deploy", choices=IMAGES_NAMES)
parser.add_argument("--tag", help="Image tag, default=latest", default="latest", required=False)
args = parser.parse_args()


PROJECT_ID = "prawobiorca"
LOCATION = "europe-central2"

source_creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
target_creds = impersonated_credentials.Credentials(
    source_credentials=source_creds,
    target_principal=f"prawobiorca-deployer@{PROJECT_ID}.iam.gserviceaccount.com",
    target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
    lifetime=3600,
)

target_creds.refresh(Request())
token = target_creds.token
if token is None:
    raise RuntimeError("Failed to obtain access token!")

registry_host = f"{LOCATION}-docker.pkg.dev"

image_name, tag = args.image_name, args.tag

remote_ref = f"{registry_host}/{PROJECT_ID}/prawobiorca-repo/{image_name}:{tag}"


login = subprocess.Popen(
    [
        "podman",
        "login",
        "-u",
        "oauth2accesstoken",
        "--password-stdin",
        f"https://{registry_host}",
    ],
    stdin=subprocess.PIPE,
)
stdout, stderr = login.communicate(input=token.encode("utf-8"))
if login.returncode != 0:
    raise RuntimeError("Podman login failed!")

subprocess.run(["podman", "tag", f"prawobiorca/{image_name}:{tag}", remote_ref], check=True)
subprocess.run(["podman", "push", remote_ref], check=True)

print(f"Success! Image pushed: {remote_ref}")
