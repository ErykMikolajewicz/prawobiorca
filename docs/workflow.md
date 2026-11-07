# Project Workflow

## 1. Team Collaboration

When additional team members join the project:

- **Jira** is introduced for task and story management.
- **Definition of Done:**
    - A story is considered complete when its status is changed in Jira by project manager, 
    - or after passing code review and integration tests (for backend-only features).

## 2. Branching Model (Git)

The repository maintains the following branches:

- `main` – The only long-lived branch. Developers merge their changes directly into it, and it must always be ready to release.
- `<jira number>` – Per task/subtask branches for implementing individual functionalities.

## 3. Workflow

- **Task Creation in Jira**  
    Project Manager creates a new story (feature/task) in Jira.

- **Working on the Task**  
    A branch `<jira number>` is created e.g. 55, 78.  
    The developer implements the feature and prepares unit tests.

- **Integration Testing**  
    A designated developer prepares integration tests for new or modified components.

- **Merging to main**  
    After development and testing, the feature branch is merged (PR) into `main` in `WMS-DEV/prawobiorca`.

- **E2E/Manual Testing**  
    E2E tests run automatically on `main` in the release repository after the merge. Manual testing is done as needed.

- **Production Release**  
    A release from `main` is deployed to the production environment according to business needs (e.g., new features, critical fixes), see [CD](#63-cd-cdyml).

### 3.1 Exceptions

- Dedicated test branches may be used for urgent fixes observed in production; however, all changes must undergo full testing and code review before merging.
- Optionally, Test Driven Development (TDD) can be applied—writing tests before code—though not required for every task.

## 4. Additional Guidelines

- Every change must undergo code review (including test quality).
- Unit and integration tests run on every PR to `main` and every push to `main`.
- Branch protection is not available in `WMS-DEV/prawobiorca` on the current GitHub plan, so nothing blocks a direct push to `main`. Use PRs anyway and never force-push `main`.
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

Pipelines are defined with GitHub Actions in `.github/workflows/`. The code lives in two repositories, with the same workflow files in both. A `github.repository_id` condition limits each job to one of them:

- `WMS-DEV/prawobiorca` (private, id `1120768327`) – the source of truth. All development happens here: branches, PRs, unit and integration tests, and the dependency audit.
- `ErykMikolajewicz/prawobiorca` (public, id `989302666`) – the release repository. It receives `main` from the mirror, runs the E2E tests and deploys to GCP. Nobody develops or pushes here directly.

### 6.1 CI (`ci.yml`)

Runs in `WMS-DEV/prawobiorca` on every PR to `main` and every push to `main`:

- **backend** – `just check-backend`: Ruff lint and format check, type checking of `core-service` and `scripts/` with ty (configured in `core-service/pyproject.toml` and the root `pyproject.toml`), unit tests with coverage (fails below 90%).
- **integration** – integration tests (`just test-integration`), including a check that the Alembic migrations match the SQLAlchemy schemas.
- **extraction** – `just type-check-extraction`: type checking of `extraction-service` with ty. It is a separate job, because it installs the heavy service dependencies (docling, torch) and runs only when `extraction-service/` changes.
- **frontend** – `just check-frontend`: `pnpm check`, `pnpm type-check` and unit tests with Vitest and coverage (thresholds in `vitest.config.ts`).
- **api-types** – regenerates `core-service/openapi.json` and `prawobiorca-frontend/src/api/generated/` with `just api-types` and fails if they differ from the committed files.
- **workflows** – `just check-workflows`: security audit of `.github/` with zizmor (configured in `.github/zizmor.yml`) and workflow linting with actionlint.
- **containers** – `just check-containers`: linting of every `Containerfile` with hadolint. Ignored rules are listed in `.hadolint.yaml`: `DL3008` (apt package versions are not pinned, as Debian removes old versions from its repositories), `DL3059` (consecutive `RUN` instructions are kept separate for layer caching) and `DL3066` (non-numeric user names).
- **deployment** – `just check-deployment`: checks of the Kubernetes manifests in `deploy/gcp/` with checkov, installed in the separate `deployment` dependency group, as it pulls many packages. The manifests in `deploy/local/` are not checked, but they keep the same security settings as their GCP counterparts. Checks skipped in `.checkov.yaml`:
    - `CKV_K8S_14`, `CKV_K8S_43` – images use the `latest` tag instead of a digest, CD replaces it with the commit SHA.
    - `CKV_K8S_15` – the image pull policy is left default, as every deployed image has an immutable tag.
    - `CKV_K8S_21` – all resources live in the `default` namespace.
    - `CKV2_K8S_6` – there are no network policies.

    Checks skipped for a single resource are marked with a `checkov.io/skip<n>` annotation with the reason: probes of the worker, which has no HTTP endpoint, and the UID of postgres, which runs as the `postgres` user of the image (UID 999), the owner of the existing data.

Every action in `.github/` is pinned to a full commit SHA, with its exact version in a comment (`uses: actions/checkout@<sha> # v7.0.1`). When updating an action, change both. Every job declares its own `permissions`, and `actions/checkout` runs with `persist-credentials: false`. Accepted zizmor findings are marked with `# zizmor: ignore[<audit>]` on the reported line:

- `artipacked` in the `changes` job of `ci.yml` – `dorny/paths-filter` fetches the base commit with git on push events, so the checkout keeps its credentials.
- `cache-poisoning` in `e2e.yml` – known and postponed.

When the API contract changes, run `just api-types` and commit the generated files (the commit hook does it automatically for changes in `core-service/src/`).

The integration tests pull PostgreSQL with pgvector from `ghcr.io/erykmikolajewicz/pgvector:0.8.4-pg18-trixie` instead of Docker Hub, to avoid its unauthenticated pull rate limit. The image is a public copy of `pgvector/pgvector:0.8.4-pg18-trixie`, pushed manually; push a new tag and update `POSTGRES_IMAGE_VERSION` in `core-service/tests/integration/conftest.py` when changing the version:

```bash
podman pull docker.io/pgvector/pgvector:0.8.4-pg18-trixie
podman tag docker.io/pgvector/pgvector:0.8.4-pg18-trixie ghcr.io/erykmikolajewicz/pgvector:0.8.4-pg18-trixie
podman push ghcr.io/erykmikolajewicz/pgvector:0.8.4-pg18-trixie
```

The `audit.yml` workflow checks dependencies for known vulnerabilities in `WMS-DEV/prawobiorca`: weekly, on demand, and on PRs to `main` that change dependency files. Accepted findings in the `deployment` dependency group, pulled in by checkov:

- `asteval` – checkov pins a vulnerable version, so `override-dependencies` in `pyproject.toml` forces the fixed one.
- `ecdsa` (`PYSEC-2026-1325`) – there is no fixed version, so `just audit-backend` ignores it with `--ignore-until-fixed` and reports it again once a fix is released. The vulnerability affects signing, while checkov only verifies signatures of external checks with it.

### 6.2 E2E (`e2e.yml`)

Runs only in the release repository, on every push to `main` and as the first step of every release. It builds the backend and frontend images, deploys them with `just run-e2e-env` and runs the Playwright tests (see [Tests](tests/tests.md#e2e-tests)). On failure it prints the backend and nginx logs and uploads the Playwright report as an artifact.

The result is not reported back to `WMS-DEV/prawobiorca`. The release repository is public, so its logs can be shared with developers by a link.

The job pulls `embedding-service` from `ghcr.io/erykmikolajewicz/embedding-service:latest` instead of building it. The image is public and pushed manually; push it again whenever `embedding-service/Containerfile` changes:

```bash
podman login ghcr.io -u ErykMikolajewicz
podman tag localhost/embedding-service:latest ghcr.io/erykmikolajewicz/embedding-service:latest
podman push ghcr.io/erykmikolajewicz/embedding-service:latest
```

### 6.3 CD (`cd.yml`)

Runs only in the release repository, when a release is published. Pushes to `main` do not deploy, and neither do prereleases. To release:

```bash
just release v1.2.3
```

The recipe fails if `main` differs between the repositories, which means the mirror is out of date. Otherwise it creates a release from `main` in the release repository. The release then goes through these steps:

- Runs the E2E tests on the released commit.
- Waits for approval in the `production` environment of the release repository.
- Builds both images and pushes them to Artifact Registry, tagged with the commit SHA and `latest`.
- Runs the migrations job, then rolls out `prawobiorca-backend`, `prawobiorca-worker` and `prawobiorca-frontend`.

The `production` environment accepts only `v*` tags and requires the approval of the repository owner. This approval is the protection against an unwanted deployment, because `MIRROR_TOKEN` is readable by the administrators of `WMS-DEV/prawobiorca` and allows creating releases, but not approving deployments.

To roll back, create a new release from the previous commit (`just release` always uses `main`):

```bash
gh release create v1.2.4 -R ErykMikolajewicz/prawobiorca --target <commit sha> --generate-notes
```

The migrations job of an older image fails if the database already has a newer migration. In that case, release a fix instead of rolling back.

GitHub authenticates to GCP with Workload Identity Federation, limited to the `production` environment and configured once by `scripts/cloud/github_cicd_init.sh`.

Other components are not deployed by CD: the rest of the cluster (configuration, PostgreSQL) is applied by `scripts/cloud/deploy_app.sh`, and the Cloud Run services (`extraction-service`, `embedding-service`, `embedding-batch-service`) by their own scripts in `scripts/cloud/`.

### 6.4 Mirror (`mirror.yml`)

On every push to `main` in `WMS-DEV/prawobiorca`, the branch is pushed to the release repository, which starts the E2E tests there. Other branches are not mirrored. Everything merged to `main` becomes public.

The push is not forced, so it fails when `main` in `WMS-DEV/prawobiorca` was force-pushed or the release repository got its own commits. Failures are not visible in the release repository, so `just release` checks that both repositories are on the same commit.

The workflow authenticates with the `MIRROR_TOKEN` secret of `WMS-DEV/prawobiorca`: a fine-grained PAT for `ErykMikolajewicz/prawobiorca` with `Contents` and `Workflows` read and write permissions. It must be renewed before it expires.

Local remotes: `origin` points to `WMS-DEV/prawobiorca`, `release` to the release repository and is fetch-only:

```bash
git remote add release https://github.com/ErykMikolajewicz/prawobiorca.git
git remote set-url --push release no_push
```
