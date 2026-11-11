# E2E tests

Automated E2E tests provide a small smoke test of the deployed application.
The Playwright scenario registers and logs in a user, creates a case, searches a legal act and adds
a result to the case. Keep detailed rules and error cases in backend and frontend tests.

See the [search scenario](https://github.com/WMS-DEV/prawobiorca/blob/main/apps/web/e2e/search.spec.ts)
for the current steps. For full flows including AI processing and DOCX generation,
use the [manual E2E scenario](manual_e2e_test.md).

## Environment

Tests use built `core` and `web` images through the local ingress at `http://localhost:8080`.
Real embedding and object storage services support the search flow. The environment prepares a public
legal act from stored extraction output, avoiding a dependency on live extraction, LLM generation
or background workers for this smoke test.

Each run registers a uniquely named user. The environment shares volumes with `just run-locally`,
so the prepared legal act remains in the local database between runs.
See the [environment setup](https://github.com/WMS-DEV/prawobiorca/blob/main/scripts/local/run_e2e.py)
for service configuration.

## Running locally

Install frontend dependencies with `pnpm install` in `apps/web` and ensure Podman is available.
From the repository root:

```bash
just build-core
just build-web
just run-e2e-env
cd apps/web
pnpm test:e2e
```

After the run, return to the repository root and stop the environment with `just run-locally-down`.

## CI

E2E runs in the release repository on pushes to `main` and before deployment.
It does not run on PRs in the source repository.
See [E2E in CI/CD](../ci_cd.md#e2e-e2eyml) for execution and failure reports.
