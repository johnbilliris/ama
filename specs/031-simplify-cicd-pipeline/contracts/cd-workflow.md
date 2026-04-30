# Contract: `cd.yml` workflow

## Purpose

Deploy to **exactly one** Azure environment per run, after `ci` succeeds for a `push` event on one of `dev`, `staging`, `production`. Branch identity drives target environment 1:1.

## Trigger

```yaml
on:
  workflow_run:
    workflows: ["ci"]
    types: [completed]
    branches:
      - dev
      - staging
      - production
```

**Critical preconditions** (gated by job-level `if:`):

```yaml
jobs:
  deploy:
    if: >-
      github.event.workflow_run.conclusion == 'success' &&
      github.event.workflow_run.event == 'push'
```

- `conclusion == 'success'` — only deploy when CI passed (FR-003).
- `event == 'push'` — never deploy off a PR-triggered CI run (FR-006).
- Branch filter `[dev, staging, production]` — `main` is excluded; FR-003 / FR-004.

## Permissions

```yaml
permissions:
  contents: read     # checkout the head_sha
  issues: write      # critical-failure issue creation (staging/prod only)
  actions: read      # read upstream workflow_run metadata
```

**Removed**: `id-token: write` (no longer needed once OIDC is dropped).

## Environment binding

The job uses a **dynamic** `environment:` key:

```yaml
environment: ${{ github.event.workflow_run.head_branch }}
```

This resolves to `dev` / `staging` / `production` and pulls `secrets.AZURE_CREDENTIALS` from the matching GitHub Environment.

## Concurrency

```yaml
concurrency:
  group: deploy-${{ github.event.workflow_run.head_branch }}
  cancel-in-progress: false
```

One in-flight deploy per environment; queue (do not cancel) subsequent runs.

## Job: `deploy`

### Step order

1. **Checkout the validated commit** (NOT default branch):
   ```yaml
   - uses: actions/checkout@v5
     with:
       ref: ${{ github.event.workflow_run.head_sha }}
   ```
2. **Set TARGET_ENV** as a job-level env from `head_branch`:
   ```yaml
   - run: echo "TARGET_ENV=${{ github.event.workflow_run.head_branch }}" >> "$GITHUB_ENV"
   ```
3. **Azure login** with the JSON secret:
   ```yaml
   - uses: azure/login@v3
     with:
       creds: ${{ secrets.AZURE_CREDENTIALS }}
   ```
4. **Install azd**: `Azure/setup-azd@v2`.
5. **Create resource group** (`rg-drh-${TARGET_ENV}`, `--location australiaeast`). Idempotent.
6. **Configure azd environment** (`azd env new drh-${TARGET_ENV} --no-prompt || true`; set `AZURE_ENV_NAME`, `AZURE_LOCATION`, `AZURE_SUBSCRIPTION_ID`).
7. **Provision** (`azd provision --no-prompt`).
8. **Deploy** (`azd deploy --no-prompt`).
9. **Health checks** (parallel) — same as today; check `api`, `agents`, `ingestion` (containerapp), `web` (appservice).
10. **Record known-good revisions** (always, on success of step 9).
11. **Rollback on health failure** — `if: failure() && steps.health-check.outcome == 'failure' && env.TARGET_ENV != 'dev'`. Invokes `scripts/rollback.sh --environment ${TARGET_ENV} --resource-group rg-drh-${TARGET_ENV}`.
12. **Critical-failure issue creation** — `if: failure() && steps.rollback.outcome == 'failure' && env.TARGET_ENV != 'dev'`. Same `gh issue create` body as today, parameterised on `TARGET_ENV`.
13. **Set deployment status** (`success` / `rolled-back` / `critical-failure` / `failed-no-rollback`).
14. **Deployment summary** writes to `$GITHUB_STEP_SUMMARY`.

### Removed jobs

The current `deployment-gates` and `deploy-production` jobs are **removed**. Gate logic that ran between staging and production (lint, pip-audit) was already enforced by `ci.yml`; duplicating it in CD added complexity without value. Production deployment is now triggered directly by a push to the `production` branch (with whatever branch-protection rules the operator configures).

## Behavioural contract

| Scenario | Expected outcome |
|---|---|
| `ci` succeeds on `push` to `dev` | One `cd` run; deploys to `rg-drh-dev`; on health failure, no rollback, no issue. |
| `ci` succeeds on `push` to `staging` | One `cd` run; deploys to `rg-drh-staging`; on health failure, runs rollback; on rollback failure, opens critical issue. |
| `ci` succeeds on `push` to `production` | Same as staging but against `rg-drh-production`. |
| `ci` succeeds on `push` to `main` | `cd` does **not** run (excluded by `branches:` filter). |
| `ci` succeeds on a `pull_request` to `main` | `cd` does **not** run (excluded by the `event == 'push'` gate). |
| `ci` fails on any branch | `cd` does **not** run (excluded by the `conclusion == 'success'` gate). |
| Two pushes to `staging` 30 seconds apart, both pass `ci` | Two `cd` runs; second queues behind first; both eventually complete. |
| `AZURE_CREDENTIALS` missing in target env | `cd` fails fast at step 3 (`azure/login`) with a clear message. |
| `head_sha` no longer exists (force-pushed) | Step 1 fails with a checkout error (acceptable; force-pushing in flight is a known operator hazard). |

## Acceptance tests

- **AT-CD-001**: Push a no-op commit to `dev`. After `ci` succeeds, exactly one `cd` run starts; it deploys to `rg-drh-dev`; the workflow summary shows env=`dev`. No issue is created if the deploy fails.
- **AT-CD-002**: Push a no-op commit to `staging`. CD runs; if induced to fail health checks, `scripts/rollback.sh` is invoked with `--environment staging`.
- **AT-CD-003**: Push to `main`. `ci` runs; `cd` does NOT run. Confirm via the Actions UI that no `cd` workflow run is created.
- **AT-CD-004**: Open a PR to `main`. `ci` runs (PR-driven). Confirm `cd` does NOT run even when `ci` passes.
- **AT-CD-005**: Trigger two pushes to `production` 10 seconds apart. Confirm via the Actions UI that the second `cd` is `queued` while the first is `in_progress`, and that they execute serially in commit order.

## Outputs

| Output | Source | Used by |
|---|---|---|
| `target_env` | `head_branch` | step summary, rollback script invocation |
| `revision-{api,agents,ingestion}` | `az containerapp show` | (informational; not consumed downstream in this PR) |
| `revision-web` | `az webapp show` | (informational) |
| `deployment-status` | computed at end | step summary |
