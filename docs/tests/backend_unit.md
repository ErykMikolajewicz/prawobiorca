# Backend unit tests

Unit tests verify behavior without running external services. Run them with `just test` from the repository root.

## Choosing the scope

- **Domain entities, value objects and services:** test business rules through their public API, using real objects.
  Access policies, validation and domain status transitions belong here and do not need mocks.
- **Use cases:** test their own orchestration decisions, reactions to failures and limits of task deliveries.
  Move business rules into the domain when appropriate. Simple delegation is covered by integration tests.
- **Infrastructure adapters:** test meaningful transformations and error handling. Replace the network at the
  transport boundary when testing HTTP clients, so the client itself still runs. Database repositories are
  covered against a real database by integration tests.
- **Input validation:** test custom validation rules directly when they need cases beyond the endpoint contract tests.

## Writing tests

Arrange only the state relevant to the scenario. Use shared factories and fixtures for ordinary valid data;
a test overrides the values it exercises. Build DTOs and value objects from real classes so changes to their
fields remain visible to the tests.

Replace external services at their boundaries. In use case tests, replace ports as needed to isolate
orchestration. Assert observable outcomes: returned values, exceptions, saved statuses and scheduled work.
Avoid assertions about incidental reads, session passing or the order of internal calls.

Use parametrization for tables of inputs and expected outcomes. Test dependency failures when the tested
code handles them; repeating that an unhandled exception propagates adds little value.

## Examples and shared setup

Start from [regulation use case tests](https://github.com/WMS-DEV/prawobiorca/blob/main/apps/core/tests/unit/use_cases/test_regulations_uc.py).
Read the [shared fixtures and factories](https://github.com/WMS-DEV/prawobiorca/tree/main/apps/core/tests/fixtures)
and [mock helpers](https://github.com/WMS-DEV/prawobiorca/blob/main/apps/core/tests/mocks.py) for their current interfaces.
