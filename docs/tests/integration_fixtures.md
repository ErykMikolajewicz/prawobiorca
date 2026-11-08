# Fixtures used in integration tests

The fixtures are defined in `core-service/tests/integration/conftest.py`, and the shared ones in
`core-service/tests/fixtures/` and `core-service/tests/integration/fixtures/`.

## Database connection

A single PostgreSQL container and a single engine (`session_maker` fixture) are shared by the tests and the application.

`asyncpg` connections are bound to the event loop in which they were created. This is not a problem here, because:

- `pytest.ini` runs all tests and fixtures in one, session-scoped event loop,
- the test client calls the application through `ASGITransport`, in the same event loop as the test.

The test inserts its data with `session_maker`, calls an endpoint, and then reads the database with `session_maker` again
to check the result.

## Database cleanup

The `clean_database` fixture empties all tables (`TRUNCATE ... CASCADE`, except `alembic_version`) before each test.
Therefore:

- a test does not clean up after itself and does not need `try` / `finally` blocks,
- each test starts with an empty database, also without the data inserted by migrations (e.g. the default organization),
- tests cannot depend on each other.

Transaction rollback is not used, because the application commits its own transactions, and a task is visible to
the worker only after `NOTIFY` is committed.

## Application dependencies

The `override_dependencies` fixture is applied to every test. It connects the application to the test database
and replaces external services:

- object storage – `mock_regulations_storage`, `mock_applications_storage`, `mock_application_templates_storage`,
- embedding service – `mock_texts_embedder`, which returns `QUERY_VECTOR` for queries and `DESCRIPTION_VECTOR` for texts
  (`tests/integration/fixtures/ai_services.py`),
- task broker – a real, not started `PostgresBroker`, so scheduled tasks are written to the `task_messages` table.

A test configures or inspects a mock by requesting its fixture. Scheduled tasks are read with `get_scheduled_task_names()`
or `get_scheduled_tasks()` from `tests/integration/fixtures/tasks.py`.

## Clients and users

Authentication is not mocked – the clients send a real access token, signed with the application key:

- `client` – an anonymous caller,
- `user_client` – a logged user (`USER_ID`); requests the `user` fixture, which stores the user in the database,
- `admin_client` – a logged administrator (`ADMIN_ID`); requests the `admin` fixture.

The `user` and `admin` fixtures can also be requested alone, when the test needs data of another user.

## Test data

Insert data with the helpers from `tests/integration/fixtures/` (`insert_regulation`, `insert_section`, `insert_case`,
`insert_application`, `insert_application_template`, `insert_organization`, ...). They take an open session, so several
rows can be inserted in one transaction:

```python
async with session_maker.begin() as session:
    organization_id = await insert_organization(session)
    regulation_id = await insert_regulation(session, None, organization_id=organization_id)
```
