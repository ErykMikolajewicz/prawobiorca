# Frontend tests

Frontend tests check rendered content, requests, validation, messages and navigation from the user's perspective.
Run `pnpm test:unit` in `apps/web` for watch mode, add `--run` for a single run,
or use `just check-frontend` from the repository root for checks with coverage.

## Choosing the scope

- **Pages:** exercise the main flows with real child components and composables, including request failures.
  Composables used only by that page usually need no separate tests for the same behavior.
- **Components:** test independently when they own validation, status-dependent behavior or emitted events.
- **Composables, stores, domain and utilities:** cover behavior that is difficult to reach through a page,
  such as outdated responses, polling limits and value mapping.
- **Router and application startup:** check navigation guards, session restoration and session expiry.

## Service boundaries

Replace the API client, object storage access and browser APIs unavailable in the test environment.
Keep stores, the router and UI components real so broken bindings and form validation remain observable.
Tests that render nothing may replace the message service to inspect feedback.

Stub an own child component when testing a container whose responsibility is passing data and events,
or when the child requires a heavy dependency. Keep such replacements narrow so they do not hide
the behavior the test is meant to verify.

## Writing tests

Interact through inputs, buttons, options and forms. Emit child events directly only for defensive paths
that cannot be triggered through normal interaction.

Assert the outcome: request data, page content, exact feedback messages and the destination route.
Cover each request failure the tested code handles. Wait for visible asynchronous effects;
use controlled timers for polling rather than arbitrary delays.

Use shared application setup and data factories so each test starts with isolated state and only specifies
what matters to its scenario. Framework configuration and cleanup details belong in the shared setup.

## Examples and shared setup

See [case page tests](https://github.com/WMS-DEV/prawobiorca/blob/main/apps/web/src/pages/__tests__/CasePage.spec.ts)
for a representative page flow, and the [shared test helpers](https://github.com/WMS-DEV/prawobiorca/tree/main/apps/web/src/__tests__)
for application setup, DOM interaction and data factories.
The [Vitest configuration](https://github.com/WMS-DEV/prawobiorca/blob/main/apps/web/vitest.config.ts)
defines environment and coverage settings.
