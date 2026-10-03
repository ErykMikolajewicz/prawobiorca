# Frontend

## 1. Introduction

The frontend is the user-facing layer of Prawobiorca. It is a single-page application (SPA) written in **Vue 3**, living in the `prawobiorca-frontend/` directory of this repository, next to the Python services described in [General information](architecture.md).

It talks to `core-service` exclusively over the HTTP REST API — it has no direct access to the database, the object storage, or any of the compute services.

---

## 2. Technology Stack

* **Vue 3** with the Composition API and `<script setup>` single-file components.
* **TypeScript**, type-checked with `vue-tsc` (the `tsc` CLI cannot resolve `.vue` imports).
* **Vite** as the dev server and production bundler.
* **Vue Router** for client-side routing, in HTML5 history mode.
* **Pinia** for shared application state.
* **Element Plus** as the component library, including its dark theme variables.
* **axios** as the HTTP client, with the API client generated from the OpenAPI contract by **Orval**.
* **Vitest** for unit tests, **oxlint** + **ESLint** for linting and **oxfmt** for formatting.

Required toolchain versions are declared in `prawobiorca-frontend/package.json`: Node `^24.15.0` (`engines`) and pnpm `11.24.0` (`packageManager`, enabled through Corepack).

---

## 3. Project Structure

All application code lives in `prawobiorca-frontend/src`:

* **`api/`** — the shared axios instance and the API client generated from the `core-service` contract: `generated/endpoints/` holds one function per endpoint, grouped by tag, and `generated/model/` the request/response types. `cases.ts` holds the only hand-written call, to an endpoint missing from the contract.
* **`pages/`** — route-level views (`MainPage`, `SearchPage`, `CasePage`, `LoginPage`, `RegisterPage`).
* **`components/`** — reusable components organised by **Atomic Design**: `atoms/` (badges, buttons), `molecules/` (cards, dialogs, selectors), `organisms/` (navbar, footer, forms, lists) and `templates/` (`AppLayout`, the navbar–content–footer page layout).
* **`composables/`** — reusable stateful logic (dark mode, regulation lists, regulation search, regulation upload flow, preparation status polling).
* **`domain/`** — framework-free domain constants and helpers shared across components (regulation types, preparation statuses, public/user scope).
* **`stores/`** — Pinia stores; currently `auth`, holding the session state.
* **`router/`** — route definitions. Pages are lazy-loaded, unknown paths redirect to the main page, and the auth guard passes the requested path to the login page, which returns there after logging in.
* **`utils/`**, **`assets/`** — error helpers, object storage helpers (presigned upload, dev URL rewrite) and global styles.
* **`__tests__/`** — unit tests, placed in a `__tests__` directory next to the code they cover.

`src/main.ts` is the entry point: it wires Pinia, the router and Element Plus, registers the session-expiry handler and resolves the current session before mounting the app.

---

## 4. API Integration

* The shared axios instance (`src/api/axios.ts`) has no `baseURL` — the paths in the contract already carry the `/api` prefix, under which the API is served on the same origin in every environment (the Vite dev server proxies it to `core-service`).
* `withCredentials` is enabled — access and refresh tokens are carried in cookies, never stored by the application itself.
* A response interceptor retries a request once after refreshing the tokens when `core-service` answers `401`. Concurrent refreshes share a single in-flight request, and the auth endpoints themselves are excluded from this path.
* When the refresh fails, the session-expiry handler resets the auth store and redirects to the login page, and the request is rejected with `SessionExpiredError`, which `showApiError` ignores so the user sees a single message.
* The API client is generated with `just api-types` (run from the repository root): it exports `core-service/openapi.json` and generates `src/api/generated/` from it with **Orval** (`orval.config.ts`). Generated functions send requests through `prawobiorcaRequest`, so they share the axios instance and its interceptor. Components, composables and stores call them directly; logic around the calls lives in composables and utils. The generated files are committed, and CI fails when they are out of date.
* In development, presigned storage URLs pointing at `VITE_DEV_STORAGE_ORIGIN` (set in the committed `.env.development`) are rewritten to `/storage`, which the Vite dev server proxies to object storage. The variable is not set in production builds, so URLs are used as returned by `core-service`.

---

## 5. Build and Deployment

`prawobiorca-frontend/Containerfile` defines a two-stage build: the first stage installs dependencies with pnpm and runs `pnpm run build`, the second copies the resulting `dist/` into an **nginx:alpine** image listening on port `8000`. The bundled `nginx.conf` falls back to `index.html` for unknown paths, which is what the history-mode router requires.

The image is built as `prawobiorca-frontend` by `just build-frontend` (and as part of `just build-images`).

In both deployment environments the frontend is served at the root path, behind the same entry point as the API:

* **On-Premise**: `deploy/local/prawobiorca-frontend.yaml`, routed by the nginx ingress defined in `deploy/local/nginx-config.yaml` — `/` goes to the frontend, `/api` to `core-service`.
* **Cloud (GCP)**: `deploy/gcp/prawobiorca-frontend.yaml`, routed by `deploy/gcp/ingress.yaml`.

---

## 6. Development Commands

All commands are run from the `prawobiorca-frontend/` directory:

| Command | Purpose |
| --- | --- |
| `pnpm install` | Install dependencies. |
| `pnpm dev` | Vite dev server with hot reload. |
| `pnpm build` | Type-check and build the production bundle. |
| `pnpm type-check` | Type-check with `vue-tsc`. |
| `pnpm test:unit` | Run unit tests with Vitest. |
| `pnpm test:e2e` | Run E2E tests with Playwright against a running environment (see [Tests](../tests/tests.md#e2e-tests)). |
| `pnpm lint` | Run oxlint and ESLint with autofix. |
| `pnpm format` | Format `src/` with oxfmt. |
| `pnpm check` | Run oxlint, ESLint and oxfmt without fixing; used by the pre-commit hook. |
| `pnpm generate:api-client` | Generate `src/api/generated/` from `core-service/openapi.json` with Orval. |

A JetBrains IDE (PyCharm Professional, free for students under a non-commercial licence) with the Vue plugin is recommended, so that the whole repository — Python services and frontend — is handled by a single IDE. In VS Code, the [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) extension is required to make the TypeScript language service aware of `.vue` types.
