# CI/CD

GitHub Actions workflows live in `.github/workflows/` and are shared by two repositories. Jobs use `github.repository_id` to select where they run:

| Repository | Role |
| --- | --- |
| `WMS-DEV/prawobiorca` (private, `1120768327`) | Source of truth: development, PRs, CI, dependency audits and mutation tests. |
| `ErykMikolajewicz/prawobiorca` (public, `989302666`) | Receives `main` through the mirror, runs E2E and deploys to GCP. No direct development or pushes. |

## CI (`ci.yml`)

Runs on PRs and pushes to `main` in the source repository. The `changes` job selects checks by changed paths, including shared configuration and workflow files.

| Job | Command | Checks |
| --- | --- | --- |
| `backend` | `just check-backend` | Ruff lint/format, complexipy, import boundaries, ty for `core` and `scripts/`, unit tests. |
| `integration` | `just cov` | Unit and integration tests; at least 90% coverage of `apps/core/src`; Alembic/SQLAlchemy schema consistency. |
| `extraction` | `just type-check-extraction`, `just scan-image prawobiorca/extraction docker`, `just test-extraction` | ty, [image vulnerability scan](#image-vulnerability-scan) and integration tests against the service image, built with Buildx and cached in Actions. The local Buildx cache is pruned before the scan to free disk space. Uses the runner's Docker socket. |
| `frontend` | `just check-frontend` | `pnpm check`, type checking, Vitest with coverage thresholds from `vitest.config.ts`. |
| `api-types` | `just api-types` | Regenerated OpenAPI schema and frontend client must match committed files. |
| `workflows` | `just check-workflows` | zizmor security audit and actionlint (official image, pinned by digest in `justfile`). |
| `containers` | `just check-containers` | hadolint for all `Containerfile` files (official image, pinned by digest in `justfile`). |
| `deployment` | `just check-deployment` | Renders the `local`, `e2e` and `gcp` overlays, which detects broken patches, then runs checkov on the rendered `gcp` manifests, using the separate `deployment` dependency group. The security settings of `core`, the worker, `web`, migrations and PostgreSQL come from the shared base. |

When the API changes, commit the output of `just api-types`: `apps/core/openapi.json` and `apps/web/src/api/generated/`. The commit hook regenerates these for changes in `apps/core/src/`.

## Documentation (`docs.yml`)

Runs on PRs targeting `main` and pushes to `main` when `docs/`, `zensical.toml`, the root `pyproject.toml`,
`uv.lock` or the documentation workflow changes. It builds the site with `uv run --locked --only-group docs zensical build --clean --strict`;
warnings fail the check.

PRs only build the documentation. On pushes to `main`, the workflow also uploads the site artifact and deploys it
to GitHub Pages through the `github-pages` environment. PR runs use read-only repository permissions, and each
ref has its own concurrency group so a PR build cannot cancel publication from `main`.

See [Working on documentation](index.md#working-on-documentation) for local preview and build commands.

## Audits and mutation tests

- **`audit.yml`** runs every Saturday at 04:00 Europe/Warsaw, on demand and on PRs changing dependency or audit configuration files. It runs `just audit-backend`, `just audit-frontend` and `just audit-licenses`. Each job uploads its text output as a separate `audit-<backend|frontend|licenses>-<run id>-<attempt>` artifact, retained for 30 days, including when the audit fails.
- **License checks** cover Python runtime dependencies of `core` and `extraction` (pip-licenses) and frontend production dependencies (`pnpm licenses list --prod`). GPL, AGPL, SSPL and missing licenses fail; LGPL and MPL are allowed. A dual license passes if any alternative is allowed. Manually verified metadata omissions go in `ACCEPTED` in `scripts/check_licenses.py` (`taskiq-dependencies`: MIT).
- **`mutation.yml`** runs for `core` and the frontend every Saturday at 04:00 Europe/Warsaw and on demand. Download the report artifacts to inspect surviving mutations and diffs; see [Weekly Report](tests/mutation.md#weekly-report).

## DAST (`dast.yml`)

Runs every Saturday at 04:00 Europe/Warsaw and on demand in the **private source repository**.
It builds `core` and `web`, deploys the `e2e` overlay to a disposable kind cluster on the runner,
then runs `just dast`. No production credentials or external scan targets are used.

The [ZAP Automation Framework](https://www.zaproxy.org/docs/automate/automation-framework/)
plan lives in `scripts/dast/plan.yaml`; `scripts/dast/run.py` prepares a filtered copy of
`apps/core/openapi.json`, registers a unique ordinary user and starts the pinned ZAP container.
ZAP first scans as a guest, then imports and scans the API again as that user. Form login and
cookie sessions are verified through `/api/auth/me` during the scan; protected requests are
also checked before and after it. ZAP can log in again when the access token expires.

Active scanning is limited to 10 minutes as a guest and 15 minutes as a user, with two threads
and a delay between requests. These are bounded scans, not a guarantee that every rule finishes.
The scanner process has a 35-minute timeout and the whole workflow a 60-minute timeout.

Download the `dast-<run id>-<attempt>` artifact for HTML/JSON findings, scanner and application logs;
artifacts are retained for 30 days. Reports stay in the private repository and are not published
as issues or mirrored files. During initial rollout, findings are **report-only**: scanner,
setup and authentication errors fail the workflow, but vulnerability alerts do not. Review the
first reports before introducing alert-based failure thresholds or documented exceptions.
DAST is independent of the release workflow and does not block deployments.

### Scope and limitations

- Login, refresh, logout and registration are excluded from attack traffic to preserve scan
  sessions; registration and login still run as setup steps.
- Upload confirmation, processing retries, description generation and case applications are
  excluded because E2E does not run extraction or the LLM. These paths are removed before
  OpenAPI import as well as excluded from the scan context.
- The scan covers API traffic through the local nginx gateway. It does not crawl the Vue UI,
  check production TLS/GCP configuration, or exercise administrator-only functionality.
- Generated OpenAPI inputs do not guarantee valid IDs for existing objects. Some object routes
  will return validation or not-found responses. DAST does not replace integration tests for
  cross-user access or business rules.

### Local use

Use a **disposable database and object storage**: active scanning can create, modify and delete
records. `just run-e2e-env` uses its own `prawobiorca-e2e` cluster, so the data of
`just run-locally` is not affected; never scan the `just run-locally` environment itself.

```bash
just run-e2e-env
just dast
just run-e2e-env-down
```

Reports are written to `.cache/dast/report/`. The temporary credentials file is removed after the
scanner exits and is not uploaded; reports may contain the disposable user's session data.
Update `ZAP_IMAGE` in `scripts/dast/run.py`
and validate the plan when upgrading ZAP.

## E2E (`e2e.yml`)

Runs in the release repository on pushes to `main` and before each deployment. It builds `core` and `web`, scans the `core` image (see [Image vulnerability scan](#image-vulnerability-scan)), loads them into a kind cluster running on the runner's Docker, deploys the `e2e` overlay with `just deploy e2e` and runs Playwright. A failed deployment prints pod states, events and logs; failed tests add `core` and gateway logs and a Playwright report artifact. Results are visible in the public repository and are not reported back to the source repository. See [E2E tests](tests/e2e.md).

The cluster node pulls the `embedding` image from GHCR, pinned by digest in `EMBEDDING_IMAGE`; see [Manually maintained images](#manually-maintained-images) when updating it.

## CD (`cd.yml`)

To publish a production release from `main`:

```bash
just release v1.2.3
```

The command requires both repositories' `main` branches to point to the same commit. Publishing the release in the release repository starts CD; pushes and prereleases do not deploy.

1. Run E2E on the released commit.
2. Wait for the repository owner's approval in the `production` environment (only `v*` tags allowed).
3. Build `core` and `web`, then push them to Artifact Registry with commit SHA and `latest` tags.
4. Run `just deploy gcp` with the SHA tags, see [Deployment script](#deployment-script). Deployments do not run in parallel (`concurrency` group).

Production approval is the deployment safeguard: source repository administrators can read `MIRROR_TOKEN` and create releases, but cannot approve deployments. GCP authentication uses Workload Identity Federation restricted to `production`, configured by `scripts/cloud/github_cicd_init.sh`.

Cloud Run services (`extraction`, `embedding`, `embedding-batch`) are deployed separately with their own scripts in `scripts/cloud/`.

### Deployment script

`scripts/deploy.py` deploys every environment (`gcp`, `local`, `e2e`) from `deploy/overlays/`; see [Manifests](architecture/architecture.md#manifests-deploy):

```bash
just deploy gcp --context <kubectl context> --image core=<image> --image web=<image>
```

1. Render the overlay once with the given images; all later steps use the same output.
2. Apply configuration and dependencies (ConfigMap, Ingress, PostgreSQL, Services) and wait for their rollouts.
3. Run Jobs one by one (migrations; the bucket and seed Jobs in the kind environments): delete the previous Job, apply the new one and wait until it succeeds or fails.
4. Apply `core`, `core-worker` and `web` (and the gateway in the kind environments) and wait for their rollouts.

Steps are selected by the `deploy-phase` label of a resource; resources without it belong to step 2. On failure the script prints pod states, events and logs, and exits with a non-zero code. Applications are not updated when a Job fails.

The kubectl context is never taken from the current one: `local` and `e2e` deploy only to their kind clusters, `gcp` requires an explicit `--context`. `--render` prints the manifests without deploying, for example for `kubectl diff -f -`.

CD and manual deployments use the same script, so a release also applies configuration, Ingress and PostgreSQL changes. A configuration change creates a new `core-config-<hash>` ConfigMap; delete old ones manually when no rollback needs them.

### Rollback

Create a new release targeting the previous commit (`just release` always targets `main`):

```bash
gh release create v1.2.4 -R ErykMikolajewicz/prawobiorca --target <commit sha> --generate-notes
```

An older image's migrations fail if the database already has a newer migration. In that case, release a fix instead.

## Mirror (`mirror.yml`)

Every push to the source repository's `main` is mirrored to the release repository, triggering E2E. **Everything merged to `main` becomes public.** Other branches are not mirrored.

The push is not forced: divergent history makes it fail. Check failures in the source repository; `just release` also detects an outdated mirror. Authentication uses `MIRROR_TOKEN`, a fine-grained PAT for the release repository with `Contents` and `Workflows` read/write permissions. Renew it before expiry.

Locally, `origin` points to the source repository. Add the release repository as fetch-only:

```bash
git remote add release https://github.com/ErykMikolajewicz/prawobiorca.git
git remote set-url --push release no_push
```

## Maintenance

### Workflow security and accepted findings

Pin external actions to full commit SHAs with exact versions in comments; update both together. Declare permissions per job and use `persist-credentials: false` for checkout. Accepted zizmor findings use inline `# zizmor: ignore[<audit>]` comments:

- `artipacked` in CI's `changes` job: checkout keeps credentials so `dorny/paths-filter` can fetch the base commit on pushes.
- `cache-poisoning` in E2E: known and postponed.

Other accepted findings:

- **hadolint** (`.hadolint.yaml`): `DL3008` — Debian removes old apt versions; `DL3059` — separate `RUN` layers for caching; `DL3066` — non-numeric usernames.
- **checkov** (`.checkov.yaml`): `CKV_K8S_43` — images are deployed by immutable SHA tags, not digests; `CKV_K8S_15` — default pull policy with immutable tags; `CKV_K8S_21` — `default` namespace; `CKV2_K8S_6` — no network policies. Resource annotations explain worker probe exemptions (no HTTP endpoint) and PostgreSQL UID 999 (owns existing data).
- **Dependency audit**: checkov's `asteval` is overridden to a fixed version in `pyproject.toml`. `ecdsa` (`PYSEC-2026-1325`) is ignored with `--ignore-until-fixed`: it affects signing, while checkov only verifies external-check signatures. The audit reports it again once a fix exists.
- **Trivy** (`.trivyignore.yaml`): unfixed Debian packages of the Python base image; see [Image vulnerability scan](#image-vulnerability-scan).

### Image vulnerability scan

`just scan-image <image> [engine]` saves the image to `.cache/trivy/image.tar` with `podman` (default) or `docker` and scans its packages with Trivy (official image, pinned by digest in `justfile`). HIGH and CRITICAL findings fail the scan, including those without a fix. The `extraction` image is scanned in CI on PRs, the `core` image in E2E, so a vulnerable `core` image blocks the release. `web`, `embedding` and pgvector are not scanned.

```bash
just build-core
just scan-image prawobiorca/core
```

Exceptions live in `.trivyignore.yaml`. Add one only for a finding without a fix whose vulnerable code the services do not reach. Each entry needs a `statement` explaining why and an `expired_at` date, at most three months ahead. An expired entry fails the scan again: check whether Debian has released a fix, then remove the entry or extend it with a reviewed statement. The file is shared by all scanned images, so a statement must hold for each of them.

The `core` and `extraction` images are multi-stage: `uv`, the build and model downloads stay in the first stage, and the runtime image contains only the virtual environment (and models), without `pip`. The runtime stage runs `apt-get upgrade` to pick up Debian security fixes not yet in the base image. Buildx caches this layer until the base image changes; to apply newer fixes locally, rebuild with `podman image build --pull=always --no-cache`.

### Manually maintained images

Integration tests pull a public pgvector copy from GHCR to avoid Docker Hub's unauthenticated pull limit. When upgrading, publish the new tag and update `POSTGRES_IMAGE_VERSION` in `apps/core/tests/integration/conftest.py`:

```bash
podman manifest create --all localhost/pgvector-mirror:0.8.7-pg18-trixie docker://docker.io/pgvector/pgvector:0.8.7-pg18-trixie
podman manifest push --all localhost/pgvector-mirror:0.8.7-pg18-trixie docker://ghcr.io/erykmikolajewicz/pgvector:0.8.7-pg18-trixie
```

The mirror preserves all upstream architectures. Keep `deploy/base/postgres.yaml`,
`apps/core/scripts/dev.py` and the integration test image on the same pgvector version;
GCP inherits the base image without a separate version override.

The `0.8.7-pg18-trixie` update stays on PostgreSQL 18. Deploy the new database image before
running migrations: migration `d9e2f7a1b6c4` updates the installed `vector` extension to `0.8.7`
in existing databases. Its downgrade leaves the extension at `0.8.7`, since pgvector provides
no downgrade scripts. Reverting application migrations does not make an older database image
safe to restore; keep the updated image when rolling back application code.

For `just dev`, an existing `postgres_db_prawobiorca` container keeps its original image.
Stop the development processes and recreate that container with the new image before running
migrations, preserving the named `pg-data` volume. The kind and GCP deployments replace the
PostgreSQL pod when its image changes and keep the existing data volume.

E2E uses a public `embedding` image. Rebuild and publish it whenever `apps/embedding/Containerfile` changes:

```bash
just build-embedding
podman login ghcr.io -u ErykMikolajewicz
podman tag localhost/prawobiorca/embedding:latest ghcr.io/erykmikolajewicz/prawobiorca/embedding:latest
podman push --digestfile embedding.digest ghcr.io/erykmikolajewicz/prawobiorca/embedding:latest
```

Then set `EMBEDDING_IMAGE` in `e2e.yml` and `dast.yml` to the digest saved in `embedding.digest`.
