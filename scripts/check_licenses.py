import json
import re
import subprocess
import sys

PYTHON_PROJECTS = ("core-service", "extraction-service")
FRONTEND = "prawobiorca-frontend"
FORBIDDEN = re.compile(r"AGPL|Affero|(?<!L)GPL|GNU General Public|SSPL|Server Side Public", re.IGNORECASE)
UNKNOWN = {"", "unknown"}
ACCEPTED = {
    "taskiq-dependencies": "MIT in the LICENSE file, missing from the package metadata",
}


def python_licenses(project: str) -> list[tuple[str, str]]:
    output = subprocess.run(
        [
            "uv",
            "run",
            "--directory",
            project,
            "--isolated",
            "--locked",
            "--no-default-groups",
            "--with",
            "pip-licenses==5.5.*",
            "pip-licenses",
            "--format=json",
        ],
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    return [(package["Name"], package["License"]) for package in json.loads(output)]


def frontend_licenses() -> list[tuple[str, str]]:
    output = subprocess.run(
        ["pnpm", "licenses", "list", "--prod", "--json"],
        cwd=FRONTEND,
        check=True,
        stdout=subprocess.PIPE,
        text=True,
    ).stdout
    return [(package["name"], license) for license, packages in json.loads(output).items() for package in packages]


def is_allowed(license: str) -> bool:
    alternatives = re.split(r"\s+OR\s+|;", license.replace("(", "").replace(")", ""))
    return any(is_permitted(alternative.strip()) for alternative in alternatives)


def is_permitted(license: str) -> bool:
    return license.lower() not in UNKNOWN and not FORBIDDEN.search(license)


def main():
    packages = frontend_licenses()
    for project in PYTHON_PROJECTS:
        packages += python_licenses(project)

    forbidden = sorted(
        {(name, license) for name, license in packages if name not in ACCEPTED and not is_allowed(license)}
    )
    for name, license in forbidden:
        print(f"{name}: {license}")

    if forbidden:
        sys.exit(1)
    print("No forbidden licenses found.")


if __name__ == "__main__":
    main()
