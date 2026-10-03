# Project Workflow

## 1. Team Collaboration

When additional team members join the project:

- **Jira** is introduced for task and story management.
- **Definition of Done:**
    - A story is considered complete when its status is changed in Jira by project manager, 
    - or after passing code review and integration tests (for backend-only features).

## 2. Branching Model (Git)

The repository maintains the following branches:

- `develop` – Main development branch where developers merge their changes.
- `<jira number>` – Per task/subtask branches for implementing individual functionalities.
- `main` – Main production branch for production releases.

## 3. Workflow

- **Task Creation in Jira**  
    Project Manager creates a new story (feature/task) in Jira.

- **Working on the Task**  
    A branch `<jira number>` is created e.g. 55, 78.  
    The developer implements the feature and prepares unit tests.

- **Merging to develop**  
    After development and initial testing, the feature branch is merged (PR) into `develop`.

- **Integration Testing**  
    A designated developer prepares integration tests for new or modified components.

- **E2E/Manual Testing**  
    After successful E2E/manual testing, the approved code is merged into `main`.

- **Production Release**  
    Code from `main` is deployed to the production environment according to business needs (e.g., new features, critical fixes).

### 3.1 Exceptions

- Branches may be created directly from `main`, and dedicated test branches may be used for urgent fixes observed in production; however, all changes must undergo full testing and code review before merging.
- Optionally, Test Driven Development (TDD) can be applied—writing tests before code—though not required for every task.

## 4. Additional Guidelines

- Every change must undergo code review (including test quality).
- Automated tests run on every PR to `develop` and `main`.
- Commit messages follow the **Conventional Commits** specification.
- Every feature branch is named according to the Jira task number and description.
- Documentation is updated as needed, at the latest in the sprint following feature implementation.

## 5. Commit Standard: Conventional Commits

**Format:**

`<type>: <description>`


**Common commit types:**

- `feature` – New functionality
- `bugfix` – Bug fix
- `chore` – Technical changes (e.g., dependency upgrades)
- `docs` – Documentation changes
- `refactor` – Code refactoring, including performance improvements
- `test` – Add or improve tests
- `style` – Changes that don’t affect logic (e.g., formatting, whitespace)

**Versioning and Commits:**

- `bugfix`, `docs`, `test`, `style` – Increment the patch version (X.Y.Z)
- `feature`, `refactor`, `chore` – Increment the minor version (X.Y.Z)
- **Breaking changes:** Increment the major version (X.Y.Z). Breaking changes should be prepared over several commits on a dedicated branch.

## 6. CI/CD

Pipelines are defined with GitHub Actions in `.github/workflows/`.

### 6.1 CI (`ci.yml`)

Runs on every push to `develop` and on every PR to `develop` and `main`:

- **backend** – `just check-backend`: Ruff lint and format check, unit tests with coverage (fails below 90%).
- **integration** – integration tests (`just test-integration`).
- **frontend** – `just check-frontend`: `pnpm check`, `pnpm type-check` and unit tests with Vitest.
- **api-types** – regenerates `core-service/openapi.json` and `prawobiorca-frontend/src/api/generated/` with `just api-types` and fails if they differ from the committed files.
- **e2e** – runs only on PRs to `main`: builds the backend and frontend images, deploys them with `just run-e2e-env` and runs the Playwright tests (see [Tests](tests/tests.md#e2e-tests)). On failure it prints the backend and nginx logs and uploads the Playwright report as an artifact.

When the API contract changes, run `just api-types` and commit the generated files (the commit hook does it automatically for changes in `core-service/src/`).

The e2e job pulls `embedding-service` from `ghcr.io/erykmikolajewicz/embedding-service:latest` instead of building it. The image is public and pushed manually; push it again whenever `embedding-service/Containerfile` changes:

```bash
podman login ghcr.io -u ErykMikolajewicz
podman tag localhost/embedding-service:latest ghcr.io/erykmikolajewicz/embedding-service:latest
podman push ghcr.io/erykmikolajewicz/embedding-service:latest
```

### 6.2 CD (`cd.yml`)

Runs on every push to `main` and deploys to GKE:

- Detects whether the backend (`core-service/`) or the frontend (`prawobiorca-frontend/`) changed, together with their manifests in `deploy/gcp/`.
- Builds only the changed images and pushes them to Artifact Registry, tagged with the commit SHA and `latest`.
- For the backend, runs the migrations job first, then rolls out `prawobiorca-backend` and `prawobiorca-worker`; for the frontend, rolls out `prawobiorca-frontend`.

GitHub authenticates to GCP with Workload Identity Federation, configured once by `scripts/cloud/github_cicd_init.sh`.

Other components are not deployed by CD: the rest of the cluster (configuration, PostgreSQL) is applied by `scripts/cloud/deploy_app.sh`, and the Cloud Run services (`extraction-service`, `embedding-service`, `embedding-batch-service`) by their own scripts in `scripts/cloud/`.
