"""
Pytest configuration file for the FastAPI project.

Registers the modules with common fixtures, such as the FastAPI test clients (`tests/fixtures/clients.py`):
`client` for an anonymous caller, `user_client` and `admin_client` for a logged user and administrator
(the last two are for integration tests only, as they store the user in the database).
Recurring test data (e.g. ids) is kept as constants in `tests/consts.py`.
"""

pytest_plugins = [
    "tests.fixtures.clients",
    "tests.fixtures.dependencies",
    "tests.integration.fixtures.ai_services",
    "tests.integration.fixtures.tasks",
    "tests.integration.fixtures.users",
]
