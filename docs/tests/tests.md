# Testing strategy

Tests check observable behavior. Refactoring that preserves behavior should not require rewriting tests.
Developers add tests alongside functionality and fixes, choosing the smallest test scope that can verify the behavior.

## Test levels

| Level | Responsibility | Guide |
| --- | --- | --- |
| Backend unit | Business rules and application orchestration | [Backend unit tests](backend_unit.md) |
| Integration | API contracts, persistence and background processing; extraction service behavior | [Integration tests](integration.md) |
| Frontend | User interactions, validation, navigation and error handling | [Frontend tests](frontend.md) |
| E2E | A small smoke test of the deployed application | [E2E tests](e2e.md) |
| Manual E2E / UAT | Full user flows including AI processing and DOCX generation | [Manual scenario](manual_e2e_test.md) |
| Mutation | Whether existing tests detect changes in behavior | [Mutation tests](mutation.md) |

## One place for each rule

Business rules, such as access policies and status transitions of domain objects, belong in domain unit tests.
Use case tests cover orchestration: decisions about scheduling work, reactions to failures and delivery limits.
Integration tests verify that these parts work together and expose the expected API contract.

For example, test the combinations of users and resource visibility in the access policy tests.
An integration test then checks that the endpoint enforces that policy and returns the correct HTTP status.
It does not need to repeat the entire policy matrix. A use case that only passes data between an endpoint
and a repository can be covered by integration tests alone.

Frontend tests cover the behavior visible to the user. Keep E2E scenarios few: detailed rules and error cases
belong in the faster backend and frontend suites.

## Running tests

Run `just` commands from the repository root. Frontend commands require dependencies installed with
`pnpm install` in `apps/web`. Container requirements are described in the integration and E2E guides.

| Command | Purpose |
| --- | --- |
| `just test` | Fast backend unit tests |
| `just test-integration` | Backend integration tests |
| `just cov` | Backend unit and integration tests with coverage |
| `just build-extraction` then `just test-extraction` | Extraction integration tests against its image |
| `cd apps/web && pnpm test:unit` | Frontend tests in watch mode; add `--run` for a single run |
| `just check-frontend` | Frontend checks, types and tests with coverage |

The test stack uses pytest for Python, Vitest for the frontend and Playwright for E2E.
Agree on additional testing libraries with the team before adding them.
See [CI/CD](../ci_cd.md) for the checks required in each repository.

## Coverage and review

Backend coverage combines unit and integration tests, so code covered through the API counts too.
Frontend coverage excludes the generated API client. Both suites enforce a 90% threshold in CI;
the precise settings live in their configuration files.

Coverage shows execution, not the strength of assertions. Review whether a test would fail if the behavior
were broken. [Mutation tests](mutation.md) help investigate this without treating their score as proof of correctness.

## Maintaining test documentation

Keep these pages focused on test scope, conventions, commands and reasons for decisions.
Document isolation guarantees and boundaries of mocked services because they affect what a test proves.

Keep fixture dependencies, helper parameters, mock configuration and framework workarounds next to their code.
Link to shared setup and representative tests instead of maintaining a separate API reference.
Store test counts, timings and mutation results in reports rather than this guide.
