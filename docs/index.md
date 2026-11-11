# Prawobiorca documentation

Welcome to the Prawobiorca developer documentation.

## What is Prawobiorca?
Prawobiorca is a web application for semantic search of legal acts, case management and AI-assisted drafting of student applications in DOCX format.
Users can search descriptions to find a relevant act, search provisions within a selected document, and find published application templates by name or with AI-assisted search.
Both the backend services and the Vue frontend are kept in a single repository.

---

## What will you find in this documentation?

* **[Application logic explanation](app_logic.md)**: What is the purpose of the app and how should it behave.
* **[AI / LLM Service](ai.md)**: AI module architecture, supported models, application templates and DOCX application generation.
* **[Workflow](workflow.md)**: Team workflow, branches and commit conventions.
* **[CI/CD](ci_cd.md)**: Automated checks, releases, deployment and pipeline maintenance.
* **[Application architecture](architecture/architecture.md)**: System overview, repository layout and deployment environments.
* **[Backend](architecture/backend.md)**: Services, background processing, API conventions and Clean Architecture.
* **[Frontend](architecture/frontend.md)**: Stack, structure and development commands of the Vue application.
* **[Tests](tests/tests.md)**: Information about testing conventions and [Manual E2E Test Case](tests/manual_e2e_test.md).

---

## Working on documentation

Documentation lives in `docs/`, and its navigation is configured in `zensical.toml`.
Write explanations in English; keep Polish UI labels, legal text examples and code identifiers as they appear in the application.
Add new pages to the navigation and update links when changing headings.

From the repository root, install the documentation tools and start the local preview:

```bash
uv sync --locked
uv run zensical serve --dev-addr 127.0.0.1:8001
```

Open [http://127.0.0.1:8001](http://127.0.0.1:8001). The preview reloads as you edit the documentation.
Port `8001` lets it run alongside the backend on port `8000`. Stop it with `Ctrl+C`.

Before submitting a change, run the same build as CI:

```bash
uv run zensical build --clean --strict
```

The generated site is written to `site/`, which is ignored by Git. The
[Docs workflow](ci_cd.md#documentation-docsyml) checks relevant PRs and publishes the site after a push to `main`.

---

## Need Support?

Have questions not covered in the documentation?

* Please send email to: eryk.mikolajewicz@gmail.com

---
