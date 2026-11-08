# Test Writing Instructions

## Scope of Tests

Within the project, we maintain the following types of tests:

- **Unit tests**
- **Integration tests**
- **Integration tests of the AI services** (`extraction-service`) — the service keeps them in its own
`tests/` directory and they are run with `just test-extraction` (the service image must be built first).
- **Frontend unit tests** — the frontend lives in `prawobiorca-frontend/` in this repository and keeps its tests in `__tests__/` directories next to the tested code. They are run with `pnpm test:unit` (Vitest).
- **Manual E2E / UAT tests** — see [Manual E2E Test Case](manual_e2e_test.md) for step-by-step verification of full user flows (login, case creation, article search, and DOCX generation).
- **E2E tests** — kept in `prawobiorca-frontend/e2e/`, written with Playwright, see [E2E Tests](#e2e-tests).

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
- `../../core-service/tests/conftest.py`
- `../../core-service/tests/integration/conftest.py`
- `../../extraction-service/tests/conftest.py`

Detailed documentation for these files can be found on separate documentation pages.  
Other `conftest.py` files are documented with docstrings inside the files themselves.

### Test Data File

- The `../../core-service/tests/consts.py` file contains example test data, for example,
STRONG_PASSWORD = "StrongPassword12;"

- Place recurring, valid data used for success scenarios there.

- The `../../core-service/tests/data` directory holds larger input fixtures — currently the real
`extraction-service` output used to test the legal structure parser against unmodified Docling results.

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
  `../../core-service/tests/mocks.py`, not by position (`call.args[-1]`), so that passing an argument by keyword
  does not break the test.
- Use `pytest.mark.parametrize` for tables such as "status → exception", instead of copying a test.
- Do not test that an exception of a dependency is propagated, unless the use case reacts to it.

`../../core-service/tests/unit/use_cases/test_regulations_uc.py` is the reference example.

## Coverage

Coverage of `core-service` is measured on unit and integration tests run together (`just cov`), for the whole `src`
directory, so code tested only by integration tests (endpoints, repositories, simple use cases) also counts.
The threshold (90%) is set in `../../core-service/coverage.toml` and checked by the CI `integration` job.
`src` has no `__init__.py` files, so `include_namespace_packages` is enabled – otherwise files never imported by
the tests (e.g. worker tasks) would be missing from the report instead of counting as not covered.
`just test` runs only the unit tests, without coverage, for fast feedback.

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
  `../../core-service/tests/integration/fixtures/regulations.py`), so that a change of the database schema affects
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

There is a single scenario (`prawobiorca-frontend/e2e/search.spec.ts`): register and log in, create a case, search a legal act and add the result to the case.

In CI they run only in the release repository, on every push to `main` and before every deployment, not on PRs in `WMS-DEV/prawobiorca` (see [E2E](../workflow.md#62-e2e-e2eyml)).

### Environment

- The tests run against the built `prawobiorca-backend` and `prawobiorca-frontend` images, deployed like the local environment (`podman kube play` with `deploy/local/`), through the nginx ingress at `http://localhost:8080`.
- `extraction-service`, `llm-service` and the Taskiq worker are not deployed. `embedding-service` is required, because every search embeds the query.
- Before the application starts, `just init-e2e-regulation` prepares a public legal act from the stored `extraction-service` output (`core-service/tests/data/ustawa-nauka_slice_30-31.json`), using the current parsing and chunking code and the real `embedding-service`. It also creates the object storage bucket. It is skipped when the act already exists.
- Each run registers a new user with a unique name, so the tests need no cleanup.

### Running Locally

From the repository root:

```bash
just build-app
just build-frontend
just run-e2e-env
cd prawobiorca-frontend && pnpm test:e2e
just run-locally-down
```

The environment uses the same volumes as `just run-locally`, so the prepared act stays in the local database.
