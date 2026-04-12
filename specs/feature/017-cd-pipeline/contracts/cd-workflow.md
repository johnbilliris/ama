# Contract: CD Workflow (`.github/workflows/cd.yml`)

**Feature**: 017-cd-pipeline
**Date**: 2025-07-14
**Type**: GitHub Actions Workflow

---

## Trigger

```yaml
on:
  workflow_run:
    workflows: ["ci"]        # Must match ci.yml name exactly
    types: [completed]
    branches: [main]
```

**Precondition**: Only executes when CI workflow completes with conclusion `success` on the `main` branch.

---

## Permissions

```yaml
permissions:
  id-token: write     # OIDC token for Azure login
  contents: read      # Checkout repository
  issues: write       # Create issues for critical failures
  actions: read       # Read workflow run status
```

---

## Environment Variables (Repository Level)

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `AZURE_CLIENT_ID` | `vars` | GitHub repo variable | Entra ID app client ID |
| `AZURE_TENANT_ID` | `vars` | GitHub repo variable | Entra ID tenant ID |
| `AZURE_SUBSCRIPTION_ID` | `vars` | GitHub repo variable | Azure subscription ID |

---

## Jobs

### Job 1: `deploy-staging`

**Runs on**: `ubuntu-latest`
**Environment**: `staging`
**Concurrency**: `{ group: deploy-staging, cancel-in-progress: false }`
**Condition**: `if: ${{ github.event.workflow_run.conclusion == 'success' }}`

**Steps**:
1. **Checkout** — `actions/checkout@v4`
2. **Azure Login** — `azure/login@v2` with OIDC
3. **Install azd** — `Azure/setup-azd@v2`
4. **Create Resource Group** — `az group create --name rg-drh-staging --location australiaeast`
5. **Configure azd Environment** — Set `AZURE_ENV_NAME=drh-staging`, `AZURE_LOCATION=australiaeast`
6. **Provision Infrastructure** — `azd provision --no-prompt`
7. **Deploy Services** — `azd deploy --no-prompt`
8. **Health Checks** — Run parallel health checks for all 4 services (30s timeout, 3 retries, 10s intervals)
9. **Record Known-Good Revision** — On health check success, save revision IDs as deployment output
10. **Rollback on Failure** — On health check failure, execute `scripts/rollback.sh --environment staging`
11. **Critical Failure Alert** — If rollback also fails, create GitHub Issue with critical severity

**Outputs**:
- `deployment-status`: `success` | `rolled-back` | `critical-failure`
- `revision-api`: Container Apps revision name
- `revision-agents`: Container Apps revision name
- `revision-ingestion`: Container Apps revision name
- `revision-web`: App Service deployment ID

---

### Job 2: `deployment-gates`

**Runs on**: `ubuntu-latest`
**Needs**: `deploy-staging`
**Condition**: `if: needs.deploy-staging.outputs.deployment-status == 'success'`

**Steps**:
1. **Checkout** — `actions/checkout@v4`
2. **Setup Python** — `actions/setup-python@v5` with Python 3.12
3. **Security Scan — Lint** — `ruff check apps tests packages`
4. **Security Scan — Dependencies** — `pip install pip-audit && pip-audit`
5. **Gate Summary** — Report gate results as job summary

**Outputs**:
- `gates-passed`: `true` | `false`
- `gate-failures`: JSON array of failed gate details

---

### Job 3: `deploy-production`

**Runs on**: `ubuntu-latest`
**Environment**: `production` (with required reviewers configured in GitHub Settings)
**Needs**: `deployment-gates`
**Condition**: `if: needs.deployment-gates.outputs.gates-passed == 'true'`
**Concurrency**: `{ group: deploy-production, cancel-in-progress: false }`

**Steps**:
1. **Checkout** — `actions/checkout@v4`
2. **Azure Login** — `azure/login@v2` with OIDC
3. **Install azd** — `Azure/setup-azd@v2`
4. **Create Resource Group** — `az group create --name rg-drh-production --location australiaeast`
5. **Configure azd Environment** — Set `AZURE_ENV_NAME=drh-production`, `AZURE_LOCATION=australiaeast`
6. **Provision Infrastructure** — `azd provision --no-prompt`
7. **Deploy Services** — `azd deploy --no-prompt`
8. **Health Checks** — Same pattern as staging
9. **Record Known-Good Revision** — Save revision IDs

**Note**: The `environment: production` declaration triggers GitHub's environment protection rules (required reviewers). The pipeline pauses at this job until an authorized reviewer approves.

---

## Concurrency Model

```yaml
# Per-environment concurrency groups
# Staging and production can deploy independently
# Within each environment, one deployment at a time (queue, don't cancel)
concurrency:
  group: deploy-${{ matrix.environment || 'staging' }}
  cancel-in-progress: false
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| CI did not pass | Job does not run (`if` condition filters) |
| Azure login failure | Job fails immediately; no partial deployment |
| `azd provision` failure | Job fails before service deployment; no rollback needed |
| `azd deploy` failure | Rollback triggered via `scripts/rollback.sh` |
| Health check failure | Rollback triggered; all services reverted |
| Rollback failure | Critical failure: GitHub Issue created, pipeline halts |
| Gate failure | `deploy-production` job skipped |
| Manual approval timeout | Job cancelled after environment wait timer expires |

---

## Timeout Budget

| Phase | Budget | Source |
|-------|--------|--------|
| Infrastructure provisioning | ~5 min | `azd provision` |
| Service deployment | ~5 min | `azd deploy` for 4 services |
| Health checks | ≤2 min | FR-010: parallel checks, 30s timeout × 3 retries |
| Gates | ~3 min | ruff + pip-audit |
| **Total (staging)** | **≤15 min** | SC-001 target |
