# Contract: `ci.yml` workflow

## Purpose

Validate every commit on `main`, `dev`, `staging`, `production`, and every pull request targeting `main`, by running quality gates (unit/integration tests, lint, type-check, web build, perf benchmark). `ci` does NOT touch Azure and does NOT deploy.

## Trigger

```yaml
on:
  push:
    branches:
      - main
      - dev
      - staging
      - production
  pull_request:
    branches:
      - main
```

**Notes**:
- The pre-existing branch entries (`001-disaster-response-hub`, `003-rubric-gap-closure`, `015-performance-benchmarks`) are **removed** as part of this change.
- PR triggers are scoped to `main` only.

## Permissions

```yaml
permissions:
  contents: read
```

No other permissions required (no Azure access, no issues).

## Jobs

### Job: `quality`

Same job as today. Steps (in order):

1. `actions/checkout@v5`
2. `actions/setup-python@v6` (3.12)
3. `pnpm/action-setup@v5` (10.6.3)
4. `actions/setup-node@v5` (24)
5. Validate workspace structure (existence checks for `pyproject.toml`, etc.)
6. Install Python tooling (`pip install pytest ruff pytest-benchmark pytest-asyncio`; `pip install -e apps/api apps/agents`)
7. `pnpm install --frozen-lockfile`
8. `pytest tests/contract tests/integration`
9. `ruff check apps tests packages`
10. `pnpm --filter ./apps/web exec tsc --noEmit`
11. `pnpm --filter ./apps/web build`
12. `pytest tests/benchmark/ --benchmark-json=.benchmarks/current.json -q` (continue-on-error, 2-min timeout)
13. Upload `.benchmarks/current.json` as artefact (always)

## Outputs

The job's success/failure is the *only* signal `cd.yml` consumes via `workflow_run`. No explicit `outputs:` are needed for that wiring.

## Behavioural contract

| When | Expected |
|---|---|
| Push to `main` | `ci` runs to completion; CD does not run. |
| Push to `dev`/`staging`/`production` | `ci` runs to completion; CD picks up via `workflow_run`. |
| PR to `main` | `ci` runs; CD does NOT run (gated by `workflow_run.event == 'push'` in `cd.yml`). |
| Push to any other branch | `ci` does NOT run. |
| Push to `dev` while a previous `ci` for `dev` is still running | The newer run starts; both run to completion (no `cancel-in-progress` on `ci`). |

## Acceptance tests

- **AT-CI-001**: A `git commit --allow-empty -m "test ci on dev" && git push origin dev` causes one and only one `ci` run for `dev`.
- **AT-CI-002**: A PR opened against `main` from any feature branch causes one `ci` run; merging it (push to `main`) causes another `ci` run; CD runs for neither (only the merged-into-`main` run runs CD if and only if `main` were a deploy branch — it is not, so no CD).
- **AT-CI-003**: A `git push` to a feature branch (e.g., `031-simplify-cicd-pipeline`) does NOT trigger `ci`.
