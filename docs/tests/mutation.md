# Mutation tests

Mutation tests change application code and check whether tests detect the change.
Use them to find weak assertions and missing cases. Surviving mutations need review: some expose a gap,
while others preserve the relevant behavior, such as a changed log message.

Mutation tests are optional locally and run separately from the default CI checks.
Survivors do not fail the command; setup, execution and report-generation errors do.

## Backend

The backend uses mutmut. Its dependencies are installed by the mutation command.
Run from the repository root, with source paths relative to `apps/core`:

```bash
just test-mutation src/core_service/domain/services/case_access.py
just test-mutation src/core_service/domain/services/regulation_access.py --tests 'tests/unit/domain/services -k access'
just test-mutation src/core_service --max-children 4 --fresh
```

The default test selection is `tests/unit`; `--tests` accepts pytest paths, node IDs and selection options.
Code covered only by integration tests can therefore be reported as `no tests`.
Runs reuse cached results when inputs have not changed; use `--fresh` to discard previous results.
Linux or macOS is required; use WSL on Windows.

Inspect the latest selection with:

```bash
just mutation-results
just mutation-results --all
just mutation-show <mutant-id>
just mutation-browse
just mutation-report
```

`just mutation-report` writes a summary, detailed results and surviving diffs to `.cache/mutation/core/report`.
Use `--output <directory>` to choose another destination. Generate reports before switching revisions
so the recorded commit matches the code under review.

## Frontend

The frontend uses StrykerJS with Vitest. Install dependencies with `pnpm install` in `apps/web`,
then run from the repository root:

```bash
just test-mutation-frontend
just test-mutation-frontend --mutate 'src/utils/error.ts'
just test-mutation-frontend --mutate 'src/utils/error.ts' --testFiles 'src/utils/__tests__/error.spec.ts'
just test-mutation-frontend --force
just mutation-report-frontend
```

Arguments are forwarded to Stryker. Quote globs and select application sources only:
`--mutate` replaces the default selection, including its exclusions. `--testFiles` can restrict the tests
used to assess a module. Adjust the worker count with `--concurrency` when needed.

The default scope covers TypeScript and Vue component scripts, excluding generated API code, tests
and type declarations. Vue templates and styles are outside its scope.
See the [Stryker configuration](https://github.com/WMS-DEV/prawobiorca/blob/main/apps/web/stryker.config.json)
for exact selection and framework-specific exclusions.

Repeated runs reuse incremental results. Use `--force` after dependency, configuration or shared setup changes.
Incremental reports can retain previously selected files; remove `.cache/mutation/web/incremental.json`
to discard that history entirely.

Open `.cache/mutation/web/report/mutation.html` for the interactive report.
`just mutation-report-frontend` generates `summary.md` with the current commit;
generate it before switching revisions. Detailed test and mutation results are in `mutation.json`.

## Interpreting results

- **Killed:** a test detected the mutation.
- **Survived:** selected tests passed; inspect the change before deciding whether a test is missing.
- **No tests / NoCoverage:** the selected tests did not exercise the mutation. Check the test selection first.
- **Timeout:** investigate the mutated behavior and execution conditions.
- **Ignored:** excluded from mutation analysis; this does not establish test coverage.

Keep measurements and mutation counts in reports. Review results against the recorded commit and add
tests for meaningful behavior gaps rather than internal calls that merely raise the mutation score.

## Weekly report

The `Mutation tests` workflow runs both suites from scratch in the source repository every Saturday
at 04:00 Europe/Warsaw, and through **Actions → Mutation tests → Run workflow**.
Summaries are displayed on the workflow run page. Download the `core-mutation-<run-id>-<attempt>`
and `frontend-mutation-<run-id>-<attempt>` artifacts within 30 days for detailed results and logs.

Backend artifacts include surviving diffs; frontend artifacts include the interactive HTML report.
Execution logs help diagnose runs that fail before complete results are produced.
Reports identify the tested commit and do not compare automatically with previous runs.
