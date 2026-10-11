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
* **md-editor-v3** for editing the AI instructions and **docx-preview** for previewing DOCX files of application templates.
* **Material Symbols** icons (`@iconify-vue/material-symbols`) and the **Inter** font (`@fontsource-variable/inter`).
* **Vitest** for unit tests, **Playwright** for E2E tests, **oxlint** + **ESLint** for linting, **stylelint** for CSS and **oxfmt** for formatting.

Required toolchain versions are declared in `prawobiorca-frontend/package.json`: Node `^24.15.0` (`engines`) and pnpm `11.24.0` (`packageManager`, enabled through Corepack).

---

## 3. Project Structure

All application code lives in `prawobiorca-frontend/src`:

* **`api/`** — the shared axios instance and the API client generated from the `core-service` contract: `generated/endpoints/` holds one function per endpoint, grouped by tag, and `generated/model/` the request/response types. The only hand-written helpers fetch a presigned URL and trigger the browser download: `cases.ts` for a generated application, `applicationTemplates.ts` for an application template.
* **`pages/`** — route-level views (`MainPage`, `FeaturesPage`, `SearchPage`, `CasePage`, `LoginPage`, `RegisterPage`, and for the administrator `ApplicationTemplatesPage`, `ApplicationTemplatePage`, `OrganizationsPage`).
* **`components/`** — reusable components organised by **Atomic Design**: `atoms/` (badges, buttons, template field inputs), `molecules/` (cards, dialogs, selectors), `organisms/` (sidebar, footer, forms, lists) and `templates/` (`AppLayout`, the sidebar–content–footer page layout).
* **`composables/`** — reusable stateful logic (dark mode, sidebar collapse state, regulation lists, regulation search, regulation upload flow, regulation details editing, application template upload flow, application template editing, published application templates, case documents, case applications, status polling of regulations and generated applications).
* **`domain/`** — framework-free domain constants and helpers shared across components (regulation types, preparation statuses, public/user scope, application generation statuses, application template statuses and field types, application template form mapping).
* **`stores/`** — Pinia stores: `auth`, holding the session state, `cases`, holding the user's cases shown in the sidebar, and `organizations`, holding the organization and suborganization context (kept in `localStorage`; a logged user gets the first organization by default, a guest none).
* **`router/`** — route definitions. Pages are lazy-loaded, unknown paths redirect to the main page, and the auth guard passes the requested path to the login page, which returns there after logging in. Routes marked `requiresAdmin` redirect a non-administrator to the main page. Routes indexed by search engines (`MainPage`, `FeaturesPage`, listed in `public/sitemap.xml`) set their own `title` and `description` in route `meta`; other routes fall back to the ones from `index.html`.
* **`utils/`**, **`assets/`** — error helpers, object storage helpers (presigned upload, dev URL rewrite), page title and description helper and global styles.
* **`__tests__/`** — unit tests, placed in a `__tests__` directory next to the code they cover.

E2E tests live outside `src`, in `prawobiorca-frontend/e2e/`.

`src/main.ts` is the entry point: it wires Pinia, the router and Element Plus, registers the session-expiry handler and resolves the current session before mounting the app.

---

## 4. Organization Context

The organization and suborganization selected in the `organizations` store form the context in which the user works:

* It is chosen in the sidebar (`SidebarContextMenu`) and in the filter of the regulations list (`RegulationOrganizationFilter`); both write to the same store.
* Public regulations (`useRegulations`) and published application templates (`usePublishedTemplates`) are fetched for the selected context and reloaded when it changes. User regulations are not filtered by it.
* The administrator assigns public regulations and application templates to an organization and optionally a suborganization with `OrganizationScopeSelect`; an empty organization means a general one.

---

## 5. API Integration

* The shared axios instance (`src/api/axios.ts`) has no `baseURL` — the paths in the contract already carry the `/api` prefix, under which the API is served on the same origin in every environment (the Vite dev server proxies it to `core-service`).
* `withCredentials` is enabled — access and refresh tokens are carried in cookies, never stored by the application itself.
* A response interceptor retries a request once after refreshing the tokens when `core-service` answers `401`. Concurrent refreshes share a single in-flight request, and the auth endpoints themselves are excluded from this path.
* When the refresh fails, the session-expiry handler resets the auth store and redirects to the login page, and the request is rejected with `SessionExpiredError`, which `showApiError` ignores so the user sees a single message.
* The API client is generated with `just api-types` (run from the repository root): it exports `core-service/openapi.json` and generates `src/api/generated/` from it with **Orval** (`orval.config.ts`). Generated functions send requests through `prawobiorcaRequest`, so they share the axios instance and its interceptor. Components, composables and stores call them directly; logic around the calls lives in composables and utils. The generated files are committed, and CI fails when they are out of date.
* In development, presigned storage URLs pointing at `VITE_DEV_STORAGE_ORIGIN` (set in the committed `.env.development`) are rewritten to `/storage`, which the Vite dev server proxies to object storage. The variable is not set in production builds, so URLs are used as returned by `core-service`.

---

## 6. Build and Deployment

`prawobiorca-frontend/Containerfile` defines a two-stage build: the first stage installs dependencies with pnpm and runs `pnpm run build`, the second copies the resulting `dist/` into an **nginx:alpine** image listening on port `8000`. The bundled `nginx.conf` falls back to `index.html` for unknown paths, which is what the history-mode router requires.

The image is built as `prawobiorca-frontend` by `just build-frontend` (and as part of `just build-images`).

In both deployment environments the frontend is served at the root path, behind the same entry point as the API:

* **On-Premise**: `deploy/local/prawobiorca-frontend.yaml`, routed by the nginx ingress defined in `deploy/local/nginx-config.yaml` — `/` goes to the frontend, `/api` to `core-service`.
* **Cloud (GCP)**: `deploy/gcp/prawobiorca-frontend.yaml`, routed by `deploy/gcp/ingress.yaml`.

---

## 7. Development Commands

All commands are run from the `prawobiorca-frontend/` directory:

| Command | Purpose |
| --- | --- |
| `pnpm install` | Install dependencies. |
| `pnpm dev` | Vite dev server with hot reload. |
| `pnpm build` | Type-check and build the production bundle. |
| `pnpm type-check` | Type-check with `vue-tsc`. |
| `pnpm test:unit` | Run unit tests with Vitest. |
| `pnpm test:e2e` | Run E2E tests with Playwright against a running environment (see [Tests](../tests/tests.md#e2e-tests)). |
| `pnpm lint` | Run oxlint, ESLint and stylelint with autofix. |
| `pnpm format` | Format `src/` with oxfmt. |
| `pnpm check` | Run oxlint, ESLint, stylelint and oxfmt without fixing; used by the pre-commit hook. |
| `pnpm generate:api-client` | Generate `src/api/generated/` from `core-service/openapi.json` with Orval. |

A JetBrains IDE (PyCharm Professional, free for students under a non-commercial licence) with the Vue plugin is recommended, so that the whole repository — Python services and frontend — is handled by a single IDE. In VS Code, the [Volar](https://marketplace.visualstudio.com/items?itemName=Vue.volar) extension is required to make the TypeScript language service aware of `.vue` types.

---

## 8. Styling

Element Plus provides the base look; the application customises it through CSS variables. Global styles live in `src/assets/styles/`, imported once through `index.css` in `src/main.ts`:

* **`tokens.css`** — the light (`:root`) and dark (`html.dark`) themes: overridden Element Plus variables (`--el-*`) and the application's own (`--app-*`), including the spacing scale `--app-space-xs|sm|md|lg|xl` (0.25, 0.5, 0.75, 1 and 1.5 rem) and `--app-radius-lg`.
* **`overrides.css`** — global overrides of Element Plus components, and styles of elements teleported outside a component (e.g. the drawer header).
* **`base.css`** — `body` and `#app`.
* **`components.css`** — shared classes: `.page-header`, `.page-title`, `.section-title`, `.icon-btn` (with `.is-active`, `.is-primary` and `.is-danger`), `.app-card` (with `.is-interactive` for clickable cards), `.app-card-content`, `.app-card-actions`, `.app-actions`, `.app-collapse`, `.app-badge`, `.app-text-truncate`, `.app-text-secondary`, `.app-list-reset` and `.app-sidebar-item`.

Component styles are written in `<style scoped>` and follow these conventions; stylelint (`stylelint.config.mjs`) enforces the color, font-size, class name and nesting rules:

* Colors only through variables — hex and color functions are allowed only in `tokens.css` and `overrides.css`.
* Spacing (`gap`, `padding`, `margin`) through `--app-space-*`; font sizes in `rem`; border radius through `--el-border-radius-base` or `--app-radius-lg`. Pixels remain for borders, shadows and fixed dimensions.
* Class names in kebab-case; states and variants as `is-*` classes (`.is-active`, `.is-collapsed`); new shared classes get the `app-` prefix.
* No nesting — Element Plus internals are styled with `:deep()` or its component variables.
* No inline styles.
* A single responsive breakpoint: `768px`, matching the Element Plus `xs` breakpoint. Mobile-only rules go into `@media (width <= 768px)`, so the desktop layout stays untouched; in scripts the same breakpoint is read from `isMobile` of the `useBreakpoint` composable.
* Hover-only effects (hiding actions until hover, lifting cards) go into `@media (hover: hover)`, so they do not hide anything on touch screens.
* On mobile the sidebar is rendered as a drawer opened from `AppTopBar`, instead of a column next to the content.
