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

In unit tests, you should only test:
- Use cases within the application layer.
- Domain services and entities/value objects (provided they exhibit internal behaviors or logic)
- Repositories/Ports - only in special cases (sophisticated mapping logic).
- Endpoints - only when verifying custom Pydantic validation logic.

All external services should be mocked in unit tests, as well as other application parts as needed.

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
- Each test should prepare its own test environment (e.g., insert data into the database) and clean up after itself.
- Tests must be fully independent of each other.
- It’s recommended to use a try block with cleanup in `finally` to ensure container state consistency even on test failure.
- **Before creating integration tests, carefully review the fixture documentation in `../../core-service/tests/integration/conftest.py`.**

When writing tests, use existing examples from the repository as a reference.

## E2E Tests

E2E tests cover only the most basic functionality of the application — searching a legal act. Keep their number minimal; everything else belongs to unit and integration tests.

There is a single scenario (`prawobiorca-frontend/e2e/search.spec.ts`): register and log in, create a case, search a legal act and add the result to the case.

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
