export VIRTUAL_ENV := ""

[working-directory: 'apps/core']
dev:
    uv run scripts/dev.py

run-locally:
    uv run scripts/local/run.py

run-locally-down:
    uv run scripts/local/stop.py

run-e2e-env:
    uv run scripts/local/run_e2e.py

[working-directory: 'apps/core']
test:
    uv run pytest tests/unit

[working-directory: 'apps/core']
test-integration:
    uv run pytest tests/integration

[working-directory: 'apps/extraction']
test-extraction:
    uv run --group test pytest tests/integration

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
init-e2e-regulation:
    uv run scripts/init_e2e_regulation.py

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
    uv run ty check

[working-directory: 'apps/core']
lint-imports-backend:
    uv run lint-imports

[working-directory: 'apps/extraction']
type-check-extraction:
    uv run --group dev --group test ty check

check-backend: && lint-imports-backend type-check-backend type-check-scripts test
    uv run ruff check .
    uv run ruff format --check
    uv run complexipy .

check-workflows:
    uv run zizmor --offline .github
    uv run actionlint

check-containers:
    uv run hadolint apps/*/Containerfile

check-deployment:
    uv run --group deployment checkov --directory deploy/gcp

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
