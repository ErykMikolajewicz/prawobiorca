export VIRTUAL_ENV := ""

[working-directory: 'core-service']
dev:
    uv run ../scripts/local/dev.py

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
compare-prompts:
    uv run python tests/unit/ai/compare_prompts.py

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

check-backend: && cov
    uv run ruff check .
    uv run ruff format --check

[working-directory: 'prawobiorca-frontend']
check-frontend:
    pnpm check
    pnpm type-check
    pnpm test:unit --run
