# Test Writing Instructions

## Scope of Tests

Within the project, we maintain the following types of tests:

- **Unit tests**
- **Integration tests**
- **Integration tests of the AI services** (`extraction`) — the service keeps them in its own
`tests/` directory and they are run with `just test-extraction` (the service image must be built first).
- **Frontend unit tests** — the frontend lives in `apps/web/` in this repository and keeps its tests in `__tests__/` directories next to the tested code. They are run with `pnpm test:unit` (Vitest), see [Frontend Unit Tests](#frontend-unit-tests).
- **Manual E2E / UAT tests** — see [Manual E2E Test Case](manual_e2e_test.md) for step-by-step verification of full user flows (login, case creation, article search, and DOCX generation).
- **E2E tests** — kept in `apps/web/e2e/`, written with Playwright, see [E2E Tests](#e2e-tests).

## Technology Stack

The following technologies are used in the project:

- Standard `unittest` library (mainly for patching)
- `pytest` for test management
- `pytest-asyncio` for asynchronous test support
- `testcontainers` for integration tests

Currently, there are **no plans to use plugins** for test parallelization or data generation libraries such as `faker`. Adding new testing libraries requires prior agreement with the team.

## Configuration Files

- The main project configuration is stored in **`pyproject.toml`**.
- Each test directory level contains a **`conftest.py`** file with commonly used fixtures.

### Key files include:
- `../../apps/core/tests/conftest.py`
- `../../apps/core/tests/integration/conftest.py`
- `../../apps/extraction/tests/conftest.py`

Detailed documentation for these files can be found on separate documentation pages.  
Other `conftest.py` files are documented with docstrings inside the files themselves.

### Test Data File

- The `../../apps/core/tests/consts.py` file contains example test data, for example,
STRONG_PASSWORD = "StrongPassword12;"

- Place recurring, valid data used for success scenarios there.

- The `../../apps/core/tests/data` directory holds larger input fixtures — currently the real
`extraction` output used to test the legal structure parser against unmodified Docling results.

## Unit Tests

Unit tests are created by the developer responsible for implementing a given functionality (e.g., based on a Jira story).

Unit tests check behavior, not implementation: a refactoring that keeps the behavior should not require changes in tests.

In unit tests, you should only test:
- Domain services and entities/value objects (provided they exhibit internal behaviors or logic). Business rules – access
  policies, status transitions, validation – belong here and are tested through their public API, with real objects and
  without mocks. Prefer moving a rule from a use case to the domain over testing it through the use case.
- Use cases within the application layer – only their own orchestration logic: branches depending on the state (e.g. which
  preparation status allows an operation), reactions to errors (e.g. marking a regulation as failed) and limits of task
  deliveries. A use case that only passes data between an endpoint and a repository is covered by integration tests only.
- Repositories/Ports - only in special cases (sophisticated mapping logic that does not need a database). A repository
  that writes to or reads from the database is tested by integration tests against the real database, not with
  a mocked session. Clients of HTTP services (embeddings, extraction, LLM) are tested with `httpx2.MockTransport`,
  which replaces the network, not the client.
- Endpoints - only when verifying custom Pydantic validation logic.

All external services should be mocked in unit tests, as well as other application parts as needed.

### One Place for Each Rule

- Access policies (`domain/services/*_access.py`) are tested by domain unit tests. Integration tests check only that an
  endpoint applies the policy (`401`, `403`, `404`), and use case unit tests do not repeat these checks.
- Status transitions and error handling of a use case are tested by use case unit tests. Integration tests check the
  success scenario and the mapping of errors to HTTP status codes, not every combination of states.

### Writing Use Case Tests

- Create the use case in a fixture, so that a new dependency changes a single place.
- Set the default state (e.g. the stored regulation) in a fixture; a test overrides only what it checks.
- Build DTOs and value objects from real classes, with helper functions with default values (e.g. `create_regulation()`),
  not with `MagicMock()` – a mock accepts any attribute, so a renamed field does not fail the test.
- Assert the outcome: the returned value, the raised exception, the statuses saved by a repository, the scheduled task.
  Do not assert calls that are only implementation details (e.g. that the use case read the regulation, or which session
  it passed to a repository).
- Read arguments of awaited calls by parameter name, with `get_awaited_argument()` and `get_awaited_arguments()` from
  `../../apps/core/tests/mocks.py`, not by position (`call.args[-1]`), so that passing an argument by keyword
  does not break the test.
- Use `pytest.mark.parametrize` for tables such as "status → exception", instead of copying a test.
- Do not test that an exception of a dependency is propagated, unless the use case reacts to it.

`../../apps/core/tests/unit/use_cases/test_regulations_uc.py` is the reference example.

## Coverage

Coverage of `core` is measured on unit and integration tests run together (`just cov`), for the whole
`core_service` package, so code tested only by integration tests (endpoints, repositories, simple use cases) also counts.
The threshold (90%) is set in `../../apps/core/coverage.toml` and checked by the CI `integration` job.
`core_service` and its subpackages have no `__init__.py` files (namespace packages), so `include_namespace_packages`
is enabled and `just cov` passes the source directory (`--cov=src/core_service`) rather than the package name – otherwise
files never imported by the tests (e.g. worker tasks) would be missing from the report instead of counting as not covered.
`just test` runs only the unit tests, without coverage, for fast feedback.

## Frontend Unit Tests

Frontend tests check what the user can observe: the rendered content, the request sent to `core`, the displayed message
and the page opened by the router. A refactoring that keeps the behavior should not require changes in tests.

### What Is Replaced

- Only the edges of the application are mocked: the generated API client
  (`vi.mock('@/api/generated/endpoints/cases/cases')` without a factory, so every function of the module is mocked and
  a renamed one fails the type-check), the object storage helpers (`@/utils/storage`) and browser APIs missing in jsdom
  (`matchMedia`, `window.open`, link clicks).
- Stores, composables, the router and Element Plus stay real. Element Plus components are not replaced with hand-written
  stubs: a stub accepts any prop and event, so a broken binding does not fail the test. Only tests of composables and
  utils, which render nothing, replace `ElMessage` (`vi.mock('element-plus', ...)`) to read the shown messages.
- `element-plus` is inlined in `vitest.config.ts` (`server.deps.inline`). Without it Node loads the CommonJS build of
  `async-validator` and every form validation passes silently.
- Own child components are stubbed only in a test of a container that just passes data and events
  (e.g. `RegulationsList.spec.ts`), and when a child needs a heavy dependency (`MdEditorV3`,
  `ApplicationTemplatePreviewDialog`).

### Test Levels

- **Pages** (`pages/__tests__`) — tested with their real child components and composables; only `AppLayout` is replaced.
  They cover the main flows of a page and its reactions to errors, so composables used by a single page
  (e.g. `useCaseApplications`) need no separate tests.
- **Components** — tested separately when they have their own logic (validation, states depending on a status,
  emitted events), e.g. `GeneratePdfForm.spec.ts`.
- **Composables, stores, `domain/`, `utils/`** — tested directly, especially what is hard to reach from a page:
  outdated responses, polling limits, mapping of values.
- **Router** — the guards are tested against the real router (`router/__tests__/index.spec.ts`).
- **Application start** — `src/__tests__/main.spec.ts` starts the whole application: restoring the session and the
  reaction to its expiry.

### Shared Helpers

Helpers live in `apps/web/src/__tests__/`:

- `setup.ts` — runs after each test: unmounts components, empties `document.body` and `localStorage`.
- `app.ts` — `createTestApp(path)` returns the `global` mounting options with Element Plus, a fresh Pinia and a memory
  router. The router is built from the real route table with empty pages, so a wrong route name fails the test.
- `dom.ts` — access to elements teleported outside the mounted component (dialogs, select options, confirmations,
  messages): `page()`, `findButton()`, `findOption()`, `confirmPopconfirm()`, `shownMessages()`, `mockLinkClicks()`.
  Mount with `attachTo: document.body` to use them.
- `factories.ts` — API objects with default values (`createRegulation()`, `createApplicationTemplate()`,
  `createHttpError()`); a test overrides only the fields it checks.

### Writing Tests

- Act like the user: fill inputs, submit forms, click buttons and options. Emit an event of a child component directly
  only when the user cannot trigger it (e.g. a defensive check).
- Assert the outcome: the arguments of the API call, the text on the page, `shownMessages('error')`,
  `router.currentRoute`. Assert the exact message, not only that some message was shown.
- Cover the failure of each request the tested code reacts to, not only the success scenario.
- Use `vi.waitFor()` for effects delayed by Element Plus (validation messages, popovers), and fake timers limited to
  `setInterval` and `Date` for polling.

`apps/web/src/pages/__tests__/CasePage.spec.ts` is the reference example.

### Coverage

Coverage is measured for the whole `src` except the generated API client; the thresholds (90%) are set in
`apps/web/vitest.config.ts` and checked by `just check-frontend`. Coverage shows only which lines were executed, so
a new test should fail when the tested behavior is broken — check it by breaking the code for a moment.

## Integration Tests

Integration tests are prepared by developers, with help from other team members if needed. 

### Review Checklist

- Are success scenarios tested?
- Are potentially dangerous situations tested (e.g., connection errors that could lead to data inconsistency)?
- Is the full functional scope covered without duplication?
- Are fixtures used appropriately without duplication/misuse?

Please note that during these tests, storage and external services are running in containers, but the application itself runs locally to allow for the mocking of its specific components.

### Integration Test Scope

- The entire path is tested: from endpoint call to response.
- Do not mock services that can be recreated locally (PostgreSQL, text-transformator) — use `testcontainers`.
- Other services (e.g., cloud storage, LLM conversations) should be mocked.
- All integration tests should use shared container instances (due to their initialization time).
- Each test prepares its own data. The database is emptied before each test, so a test does not clean up after itself.
- Insert test data with shared helpers (e.g. `insert_regulation` from
  `../../apps/core/tests/integration/fixtures/regulations.py`), so that a change of the database schema affects
  a single place.
- Tests must be fully independent of each other.
- Call endpoints with `client`, `user_client` or `admin_client`. Authentication is not mocked.
- Assert the outcome visible outside the application: the response, the database state, the scheduled tasks
  (`get_scheduled_task_names()`), and calls of external services, which are not checked by unit tests.
  Do not repeat assertions of use case unit tests (e.g. that a scheduler was not called after an error).
- Check the full shape of a response once per resource (it is the contract with the frontend). Other tests check only
  the fields they are about, so that a new field in a response changes a single test.
- **Before creating integration tests, carefully review the [fixture documentation](integration_fixtures.md).**

When writing tests, use existing examples from the repository as a reference.

## E2E Tests

E2E tests cover only the most basic functionality of the application — searching a legal act. Keep their number minimal; everything else belongs to unit and integration tests.

There is a single scenario (`apps/web/e2e/search.spec.ts`): register and log in, create a case, search a legal act and add the result to the case.

In CI they run only in the release repository, on every push to `main` and before every deployment, not on PRs in `WMS-DEV/prawobiorca` (see [E2E](../workflow.md#62-e2e-e2eyml)).

### Environment

- The tests run against the built `core` and `web` images, deployed like the local environment (`podman kube play` with `deploy/local/`), through the nginx ingress at `http://localhost:8080`.
- `extraction`, `llm` and the Taskiq worker are not deployed. `embedding` is required, because every search embeds the query.
- Before the application starts, `just init-e2e-regulation` prepares a public legal act from the stored `extraction` output (`apps/core/tests/data/ustawa-nauka_slice_30-31.json`), using the current parsing and chunking code and the real `embedding`. It also creates the object storage bucket. It is skipped when the act already exists.
- Each run registers a new user with a unique name, so the tests need no cleanup.

### Running Locally

From the repository root:

```bash
just build-core
just build-web
just run-e2e-env
cd apps/web && pnpm test:e2e
just run-locally-down
```

The environment uses the same volumes as `just run-locally`, so the prepared act stays in the local database.
