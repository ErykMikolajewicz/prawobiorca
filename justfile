export VIRTUAL_ENV := ""

[working-directory: 'core-service']
dev:
    uv run scripts/dev.py

run-locally:
    uv run scripts/local/run.py

run-locally-down:
    uv run scripts/local/stop.py

run-e2e-env:
    uv run scripts/local/run_e2e.py

[working-directory: 'core-service']
test:
    uv run pytest tests/unit

[working-directory: 'core-service']
test-integration:
    uv run pytest tests/integration

[working-directory: 'extraction-service']
test-extraction:
    uv run --group test pytest tests/integration

[working-directory: 'core-service']
cov:
    uv run coverage erase
    uv run pytest tests/unit --cov=src --cov-config=coverage.toml
    uv run coverage report -m --skip-covered --fail-under=90 --sort=Cover --rcfile=coverage.toml

build-app:
    podman image build --tag=prawobiorca-backend core-service

build-extraction-service:
    podman image build --tag=extraction-service extraction-service

build-embedding-service:
    podman image build --tag=embedding-service embedding-service

build-frontend:
    podman image build --tag=prawobiorca-frontend prawobiorca-frontend

build-images: build-app build-extraction-service build-embedding-service build-frontend

[working-directory: 'core-service']
upgrade-db:
    uv run alembic upgrade head

[working-directory: 'core-service']
seed:
    uv run scripts/seed_relational_db.py

[working-directory: 'core-service']
init-regulations:
    uv run scripts/init_regulations.py

[working-directory: 'core-service']
init-e2e-regulation:
    uv run scripts/init_e2e_regulation.py

[working-directory: 'core-service']
export-openapi:
    uv run scripts/export_openapi.py

[working-directory: 'prawobiorca-frontend']
generate-api-client:
    pnpm generate:api-client

api-types: export-openapi generate-api-client

init-db: upgrade-db seed init-regulations

[working-directory: 'core-service']
type-check-backend:
    uv run ty check

type-check-scripts:
    uv run ty check

[working-directory: 'extraction-service']
type-check-extraction:
    uv run --group dev --group test ty check

check-backend: && type-check-backend type-check-scripts cov
    uv run ruff check .
    uv run ruff format --check
    uv run complexipy .

check-workflows:
    uv run zizmor --offline .github
    uv run actionlint

check-containers:
    uv run hadolint */Containerfile

check-deployment:
    uv run --group deployment checkov --directory deploy/gcp

[working-directory: 'prawobiorca-frontend']
check-frontend:
    pnpm check
    pnpm type-check
    pnpm test:unit --run --coverage

audit-backend:
    uv audit --frozen --preview-features audit-command --ignore-until-fixed PYSEC-2026-1325
    uv audit --frozen --preview-features audit-command --directory core-service
    uv audit --frozen --preview-features audit-command --directory extraction-service

[working-directory: 'prawobiorca-frontend']
audit-frontend:
    pnpm audit --prod
    pnpm audit --dev --audit-level high

audit-licenses:
    uv run scripts/check_licenses.py

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
