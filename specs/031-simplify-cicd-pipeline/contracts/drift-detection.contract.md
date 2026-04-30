# Contract: `drift-detection.yml` workflow

## Purpose

Detect drift between deployed Azure infrastructure and the Bicep templates for the `staging` and `production` environments. Open a GitHub issue per environment when drift is detected.

## Trigger

```yaml
on:
  schedule:
    - cron: "0 16 * * 6"   # Saturday 16:00 UTC = Sunday 02:00 AEST
  workflow_dispatch:
```

No new triggers added. The schedule is preserved.

## Permissions

```yaml
permissions:
  contents: read   # checkout Bicep files
  issues: write    # create drift issues
```

**Removed**: `id-token: write` (no longer needed under `AZURE_CREDENTIALS`).

## Matrix scope

```yaml
jobs:
  detect-drift:
    strategy:
      matrix:
        environment: [staging, production]
      fail-fast: false
    environment: ${{ matrix.environment }}
```

Per FR-011 / FR-012: `dev` is **excluded**. `fail-fast: false` keeps both environments evaluated even if one fails.

## Authentication

```yaml
- uses: azure/login@v3
  with:
    creds: ${{ secrets.AZURE_CREDENTIALS }}
```

Resolved per matrix entry from the staging or production GitHub Environment.

## Step order

Unchanged from current `drift-detection.yml`:

1. Checkout repository.
2. `azure/login` (now with `creds:` JSON).
3. `az deployment group what-if` against `rg-drh-${matrix.environment}` using `infra/main.bicep` + `infra/main.parameters.${matrix.environment}.json`.
4. Parse drift output (filter false-positive properties: `provisioningState`, `etag`, timestamps, etc.).
5. Generate Markdown drift report.
6. Create GitHub Issue labelled `infrastructure-drift` (one per environment) when drift is detected; otherwise write a clean-state summary.

## Behavioural contract

| Scenario | Expected outcome |
|---|---|
| Scheduled run, no drift in either env | No issues created; both summaries say "No drift". |
| Scheduled run, drift in staging only | One `infrastructure-drift` issue against staging; production summary says "No drift". |
| `workflow_dispatch` triggered by operator | Same matrix runs (staging + production); same outputs. |
| Resource group `rg-drh-staging` does not exist yet | Step 3 emits a warning; staging job exits 0 with `drift-detected=false`; no issue created. |
| `AZURE_CREDENTIALS` missing for an environment | The matrix job for that env fails at the `azure/login` step. The other env's job continues (because of `fail-fast: false`). |
| Operator dispatches against `dev` (e.g., via UI form) | Not possible — the matrix is hard-coded to `[staging, production]`. |

## Acceptance tests

- **AT-DD-001**: Trigger the workflow via `workflow_dispatch`. Confirm exactly two matrix jobs run, named `staging` and `production`.
- **AT-DD-002**: Confirm zero matrix jobs are created for `dev` (Actions UI shows only the two).
- **AT-DD-003**: Introduce a deliberate drift in staging (e.g., manually scale a container app). Re-run the workflow. Confirm an `infrastructure-drift` issue is opened for staging only.
- **AT-DD-004**: Confirm no `permissions: id-token: write` line remains in the workflow file.
