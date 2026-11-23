export VIRTUAL_ENV := ""
export KIND_EXPERIMENTAL_PROVIDER := "podman"
export PYTHONUNBUFFERED := "1"

[working-directory: 'apps/core']
dev:
    uv run scripts/dev.py

run-locally:
    uv run --no-default-groups scripts/local/run.py local

run-locally-down:
    kubectl --context kind-prawobiorca scale deployment --all --replicas=0
    kubectl --context kind-prawobiorca delete pod --all
    podman stop --time 0 prawobiorca-control-plane

# Deletes the cluster; the database and object storage stay in the volumes shared with just dev, LLM models in .llm-models.
run-locally-reset:
    kind delete cluster --name prawobiorca

run-e2e-env:
    uv run --no-default-groups scripts/local/run.py e2e

run-e2e-env-down:
    kind delete cluster --name prawobiorca-e2e

[positional-arguments]
deploy *args:
    uv run --no-default-groups scripts/deploy.py "$@"

# Active scan: use only with a disposable E2E database.
dast:
    uv run --no-default-groups scripts/dast/run.py

[working-directory: 'apps/core']
test:
    uv run pytest tests/unit

mutation := "uv run --project apps/core --locked --group mutation scripts/mutation.py"

[positional-arguments]
test-mutation +args:
    {{mutation}} run "$@"

[positional-arguments]
mutation-results *args:
    {{mutation}} results "$@"

mutation-show mutant:
    {{mutation}} show {{quote(mutant)}}

mutation-browse:
    {{mutation}} browse

[positional-arguments]
mutation-report *args:
    {{mutation}} report "$@"

[working-directory: 'apps/web']
[positional-arguments]
test-mutation-frontend *args:
    pnpm test:mutation "$@"

[working-directory: 'apps/web']
mutation-report-frontend:
    pnpm mutation:report

[working-directory: 'apps/core']
test-integration:
    uv run pytest tests/integration

[working-directory: 'apps/extraction']
test-extraction:
    uv run --group test pytest tests

[working-directory: 'apps/core']
cov:
    uv run pytest tests/unit tests/integration --cov=src/core_service --cov-config=coverage.toml

build-core:
    podman image build --tag=prawobiorca/core apps/core

build-extraction:
    podman image build --tag=prawobiorca/extraction apps/extraction

build-embedding:
    podman image build --tag=prawobiorca/embedding apps/embedding

build-web:
    podman image build --tag=prawobiorca/web apps/web

build-images: build-core build-extraction build-embedding build-web

[working-directory: 'apps/core']
upgrade-db:
    uv run alembic upgrade head

[working-directory: 'apps/core']
seed:
    uv run scripts/seed_relational_db.py

[working-directory: 'apps/core']
init-regulations:
    uv run scripts/init_regulations.py

[working-directory: 'apps/core']
export-openapi:
    uv run scripts/export_openapi.py

[working-directory: 'apps/web']
generate-api-client:
    pnpm generate:api-client

api-types: export-openapi generate-api-client

init-db: upgrade-db seed init-regulations

[working-directory: 'apps/core']
type-check-backend:
    uv run ty check

type-check-scripts:
    uv run --only-group lint --only-group cloud ty check

[working-directory: 'apps/core']
lint-imports-backend:
    uv run lint-imports

[working-directory: 'apps/extraction']
type-check-extraction:
    uv run --group dev --group test ty check

check-backend: && lint-imports-backend type-check-backend type-check-scripts test
    uv run --only-group lint ruff check .
    uv run --only-group lint ruff format --check
    uv run --only-group lint complexipy .

actionlint := "docker.io/rhysd/actionlint:1.7.12@sha256:b1934ee5f1c509618f2508e6eb47ee0d3520686341fec936f3b79331f9315667"
hadolint := "docker.io/hadolint/hadolint:v2.15.1@sha256:32dac94127fd60b7b7e3fbfc65e1383b9b5e25c9bfd7b8536de7a539fe68a12d"
trivy := "docker.io/aquasec/trivy:0.76.2@sha256:8f6bb947dbc528902e11f2f5be52f7b519f6a39d5d148f41166f2040499768fb"

check-workflows:
    uv run --only-group workflows zizmor --offline .github
    podman run --rm -v "$PWD:/repo:ro" -w /repo {{actionlint}}

check-containers:
    podman run --rm -v "$PWD:/repo:ro" -w /repo {{hadolint}} hadolint apps/*/Containerfile

scan-image image engine="podman":
    mkdir -p .cache/trivy
    rm -f .cache/trivy/image.tar
    {{engine}} image save --output .cache/trivy/image.tar {{image}}
    podman run --rm -v "$PWD:/repo:ro" -v "$PWD/.cache/trivy:/repo/.cache/trivy" -w /repo {{trivy}} image \
        --cache-dir .cache/trivy/cache --scanners vuln --severity HIGH,CRITICAL --exit-code 1 \
        --ignorefile .trivyignore.yaml --input .cache/trivy/image.tar

check-deployment:
    mkdir -p .cache/deployment
    just deploy local --render > /dev/null
    just deploy e2e --render > /dev/null
    just deploy gcp --render --image core=prawobiorca/core:check --image web=prawobiorca/web:check > .cache/deployment/gcp.yaml
    uv run --only-group deployment checkov --file .cache/deployment/gcp.yaml

[working-directory: 'apps/web']
check-frontend:
    pnpm check
    pnpm type-check
    pnpm test:unit --run --coverage

audit-backend:
    uv audit --frozen --preview-features audit-command --ignore-until-fixed PYSEC-2026-1325
    uv audit --frozen --preview-features audit-command --directory apps/core
    uv audit --frozen --preview-features audit-command --directory apps/extraction

[working-directory: 'apps/web']
audit-frontend:
    pnpm audit --prod
    pnpm audit --dev --audit-level high

audit-licenses:
    uv run --no-default-groups scripts/check_licenses.py

audit: audit-backend audit-frontend audit-licenses

release version:
    #!/usr/bin/env bash
    set -euo pipefail
    source_sha=$(gh api repos/WMS-DEV/prawobiorca/commits/main --jq .sha)
    release_sha=$(gh api repos/ErykMikolajewicz/prawobiorca/commits/main --jq .sha)
    if [ "$source_sha" != "$release_sha" ]; then
        echo "Mirror is out of date: WMS-DEV/prawobiorca main is $source_sha, ErykMikolajewicz/prawobiorca main is $release_sha" >&2
        exit 1
    fi
    gh release create {{version}} -R ErykMikolajewicz/prawobiorca --target "$release_sha" --generate-notes
