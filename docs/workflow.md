# Project Workflow

For automated checks, releases and deployment, see [CI/CD](ci_cd.md).

## 1. Team Collaboration

When additional team members join the project:

- **Jira** is introduced for task and story management.
- **Definition of Done:**
    - A story is considered complete when its status is changed in Jira by project manager, 
    - or after passing code review and integration tests (for backend-only features).

## 2. Branching Model (Git)

The repository maintains the following branches:

- `main` – The only long-lived branch. Developers merge their changes directly into it, and it must always be ready to release.
- `<jira number>` – Per task/subtask branches for implementing individual functionalities.

## 3. Workflow

- **Task Creation in Jira**  
    Project Manager creates a new story (feature/task) in Jira.

- **Working on the Task**  
    A branch `<jira number>` is created e.g. 55, 78.  
    The developer implements the feature and prepares unit tests.

- **Integration Testing**  
    A designated developer prepares integration tests for new or modified components.

- **Merging to main**  
    After development and testing, the feature branch is merged (PR) into `main` in `WMS-DEV/prawobiorca`.

- **E2E/Manual Testing**  
    E2E tests run automatically on `main` in the release repository after the merge. Manual testing is done as needed.

- **Production Release**  
    A release from `main` is deployed to the production environment according to business needs (e.g., new features, critical fixes), see [CD](ci_cd.md#cd-cdyml).

### 3.1 Exceptions

- Dedicated test branches may be used for urgent fixes observed in production; however, all changes must undergo full testing and code review before merging.
- Optionally, Test Driven Development (TDD) can be applied—writing tests before code—though not required for every task.

## 4. Additional Guidelines

- Every change must undergo code review (including test quality).
- Unit and integration tests run on every PR to `main` and every push to `main`.
- Branch protection is not available in `WMS-DEV/prawobiorca` on the current GitHub plan, so nothing blocks a direct push to `main`. Use PRs anyway and never force-push `main`.
- Commit messages follow the **Conventional Commits** specification.
- Every feature branch is named according to the Jira task number and description.
- Documentation is updated as needed, at the latest in the sprint following feature implementation.

## 5. Commit Standard: Conventional Commits

**Format:**

`<type>: <description>`


**Common commit types:**

- `feature` – New functionality
- `bugfix` – Bug fix
- `chore` – Technical changes (e.g., dependency upgrades)
- `docs` – Documentation changes
- `refactor` – Code refactoring, including performance improvements
- `test` – Add or improve tests
- `style` – Changes that don’t affect logic (e.g., formatting, whitespace)

**Versioning and Commits:**

- `bugfix`, `docs`, `test`, `style` – Increment the patch version (X.Y.Z)
- `feature`, `refactor`, `chore` – Increment the minor version (X.Y.Z)
- **Breaking changes:** Increment the major version (X.Y.Z). Breaking changes should be prepared over several commits on a dedicated branch.
