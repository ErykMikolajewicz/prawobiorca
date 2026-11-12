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
| `extraction` | `just type-check-extraction`, `just test-extraction` | ty and integration tests against the service image, built with Buildx and cached in Actions. Uses the runner's Docker socket. |
| `frontend` | `just check-frontend` | `pnpm check`, type checking, Vitest with coverage thresholds from `vitest.config.ts`. |
| `api-types` | `just api-types` | Regenerated OpenAPI schema and frontend client must match committed files. |
| `workflows` | `just check-workflows` | zizmor security audit and actionlint. |
| `containers` | `just check-containers` | hadolint for all `Containerfile` files. |
| `deployment` | `just check-deployment` | checkov for `deploy/gcp/`, using the separate `deployment` dependency group. Local manifests are not checked; keep their security settings aligned. |

When the API changes, commit the output of `just api-types`: `apps/core/openapi.json` and `apps/web/src/api/generated/`. The commit hook regenerates these for changes in `apps/core/src/`.

## Documentation (`docs.yml`)

Runs on PRs targeting `main` and pushes to `main` when `docs/`, `zensical.toml`, the root `pyproject.toml`,
`uv.lock` or the documentation workflow changes. It builds the site with `uv run zensical build --clean --strict`;
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
It builds `core` and `web`, starts a disposable `just run-e2e-env` on the runner, then runs
`just dast`. No production credentials or external scan targets are used.

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
  excluded because E2E does not run extraction, LLM or workers. These paths are removed before
  OpenAPI import as well as excluded from the scan context.
- The scan covers API traffic through the local nginx ingress. It does not crawl the Vue UI,
  check production TLS/GCP configuration, or exercise administrator-only functionality.
- Generated OpenAPI inputs do not guarantee valid IDs for existing objects. Some object routes
  will return validation or not-found responses. DAST does not replace integration tests for
  cross-user access or business rules.

### Local use

Use a **disposable database and object storage**: active scanning can create, modify and delete
records. The ordinary local E2E environment shares volumes with `just run-locally`, so do not
scan a developer environment containing data you want to keep. Prefer a fresh VM or CI runner.

On that disposable Linux environment, build `core` and `web`, prepare the embedding image as
in E2E, then run:

```bash
just run-e2e-env
just dast
just run-locally-down
```

Reports are written to `.cache/dast/report/`. The temporary credentials file is removed after the
scanner exits and is not uploaded; reports may contain the disposable user's session data.
Update `ZAP_IMAGE` in `scripts/dast/run.py`
and validate the plan when upgrading ZAP.

## E2E (`e2e.yml`)

Runs in the release repository on pushes to `main` and before each deployment. It builds `core` and `web`, starts `just run-e2e-env` and runs Playwright. Failures include backend/nginx logs and a Playwright report artifact. Results are visible in the public repository and are not reported back to the source repository. See [E2E tests](tests/e2e.md).

The `embedding` image is pulled from GHCR; see [Manually maintained images](#manually-maintained-images) when updating it.

## CD (`cd.yml`)

To publish a production release from `main`:

```bash
just release v1.2.3
```

The command requires both repositories' `main` branches to point to the same commit. Publishing the release in the release repository starts CD; pushes and prereleases do not deploy.

1. Run E2E on the released commit.
2. Wait for the repository owner's approval in the `production` environment (only `v*` tags allowed).
3. Build `core` and `web`, then push them to Artifact Registry with commit SHA and `latest` tags.
4. Run database migrations, then roll out `core`, `core-worker` and `web` using the SHA tags.

Production approval is the deployment safeguard: source repository administrators can read `MIRROR_TOKEN` and create releases, but cannot approve deployments. GCP authentication uses Workload Identity Federation restricted to `production`, configured by `scripts/cloud/github_cicd_init.sh`.

Configuration and PostgreSQL are deployed separately with `scripts/cloud/deploy_app.sh`; Cloud Run services (`extraction`, `embedding`, `embedding-batch`) use their own scripts in `scripts/cloud/`.

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
- **checkov** (`.checkov.yaml`): `CKV_K8S_14`/`43` — CD replaces `latest` with SHA tags; `CKV_K8S_15` — default pull policy with immutable tags; `CKV_K8S_21` — `default` namespace; `CKV2_K8S_6` — no network policies. Resource annotations explain worker probe exemptions (no HTTP endpoint) and PostgreSQL UID 999 (owns existing data).
- **Dependency audit**: checkov's `asteval` is overridden to a fixed version in `pyproject.toml`. `ecdsa` (`PYSEC-2026-1325`) is ignored with `--ignore-until-fixed`: it affects signing, while checkov only verifies external-check signatures. The audit reports it again once a fix exists.

### Manually maintained images

Integration tests pull a public pgvector copy from GHCR to avoid Docker Hub's unauthenticated pull limit. When upgrading, publish the new tag and update `POSTGRES_IMAGE_VERSION` in `apps/core/tests/integration/conftest.py`:

```bash
podman pull docker.io/pgvector/pgvector:0.8.4-pg18-trixie
podman tag docker.io/pgvector/pgvector:0.8.4-pg18-trixie ghcr.io/erykmikolajewicz/pgvector:0.8.4-pg18-trixie
podman push ghcr.io/erykmikolajewicz/pgvector:0.8.4-pg18-trixie
```

E2E uses a public `embedding` image. Rebuild and publish it whenever `apps/embedding/Containerfile` changes:

```bash
just build-embedding
podman login ghcr.io -u ErykMikolajewicz
podman tag localhost/prawobiorca/embedding:latest ghcr.io/erykmikolajewicz/prawobiorca/embedding:latest
podman push ghcr.io/erykmikolajewicz/prawobiorca/embedding:latest
```
