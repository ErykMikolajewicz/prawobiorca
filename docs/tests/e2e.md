# E2E tests

Automated E2E tests provide a small smoke test of the deployed application.
The Playwright scenario registers and logs in a user, creates a case, searches a legal act and adds
a result to the case. Keep detailed rules and error cases in backend and frontend tests.

See the [search scenario](https://github.com/WMS-DEV/prawobiorca/blob/main/apps/web/e2e/search.spec.ts)
for the current steps. For full flows including AI processing and DOCX generation,
use the [manual E2E scenario](manual_e2e_test.md).

## Environment

Tests use built `core` and `web` images in a dedicated kind cluster, `prawobiorca-e2e`, through the
gateway at `http://localhost:8080`. The cluster is deployed from the `e2e` overlay: the local
environment with `extraction` and the LLM scaled to zero. Real embedding and object storage services
support the search flow. The environment prepares a public legal act from stored extraction output,
avoiding a dependency on live extraction and LLM generation for this smoke test. The `core-e2e-seed`
Job runs the seeding script from the built `core` image, so no backend Python environment is needed
on the host.

Each run registers a uniquely named user. The cluster has its own database and object storage,
separate from `just run-locally`. Both clusters use ports 8080 and 9000, so only one of them can
run at a time. See the [E2E overlay](https://github.com/WMS-DEV/prawobiorca/blob/main/deploy/overlays/e2e/kustomization.yaml)
for service configuration.

## Running locally

Install frontend dependencies with `pnpm install` in `apps/web` and ensure Podman, kind and kubectl
are available. From the repository root:

```bash
just run-e2e-env
cd apps/web
pnpm test:e2e
```

`just run-e2e-env` creates the cluster if needed, builds the images and loads the changed ones.
After the run, return to the repository root and delete the cluster with `just run-e2e-env-down`.

## CI

E2E runs in the release repository on pushes to `main` and before deployment.
It does not run on PRs in the source repository.
See [E2E in CI/CD](../ci_cd.md#e2e-e2eyml) for execution and failure reports.
