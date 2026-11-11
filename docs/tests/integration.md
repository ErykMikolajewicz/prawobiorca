# Integration tests

Integration tests verify boundaries that unit tests cannot: API contracts, persistence, dependency wiring
and background processing. Run `just test-integration`, or `just cov` to include backend unit tests and coverage.

## Core scope and service boundaries

Tests exercise the application from an HTTP request through to its response and stored effects.
PostgreSQL with pgvector runs in a container; the API runs in the test process. A working Docker-compatible
container runtime is required.

Authentication and database operations stay real. Object storage and AI services are replaced,
so these tests verify how `core` uses those services, rather than the behavior of the services themselves.
Background processing tests schedule work through the application and execute the stored task to check
that the API and worker agree on the task contract.

Cover successful flows, HTTP error mapping and failures that could leave inconsistent data.
Check the response, persisted state, scheduled work and interactions with external services where relevant.
Keep exhaustive business-rule matrices in [unit tests](backend_unit.md).

Check the complete response shape once per resource to protect the frontend contract.
Other tests should assert the fields relevant to their scenario.

## Isolation and database lifecycle

Each test starts with an empty database and creates its own data, including any records normally inserted
by migrations. Tests must not depend on execution order and do not clean up after themselves.
Reuse shared data builders to avoid spreading schema details across scenarios.

The database is cleared before each test instead of using a transaction rollback: the application commits
its own transactions, and background task notifications must be committed to become visible.
The container is shared to keep setup time down.

Tests and application code share an event loop because asynchronous database connections belong to the loop
that created them. For the current setup, see the [pytest configuration](https://github.com/WMS-DEV/prawobiorca/blob/main/apps/core/pytest.ini)
and [integration setup](https://github.com/WMS-DEV/prawobiorca/blob/main/apps/core/tests/integration/conftest.py).

## Examples and shared setup

Use existing [integration tests](https://github.com/WMS-DEV/prawobiorca/tree/main/apps/core/tests/integration)
as examples. Shared [integration helpers](https://github.com/WMS-DEV/prawobiorca/tree/main/apps/core/tests/integration/fixtures)
and [fixtures](https://github.com/WMS-DEV/prawobiorca/tree/main/apps/core/tests/fixtures)
define data creation, authenticated clients, service replacements and task execution.
Read their code for current names, dependencies and parameters.

## Extraction service

The extraction service has its own integration suite against its built container image.
From the repository root, run:

```bash
just build-extraction
just test-extraction
```

These tests check the service's document-processing behavior, which is replaced in `core` tests.
See the [extraction tests](https://github.com/WMS-DEV/prawobiorca/tree/main/apps/extraction/tests)
for the scenarios and setup. The suite also runs in the `extraction` CI job.
