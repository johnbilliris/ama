# Quickstart: CD Pipeline with Staging Environment

**Feature**: 017-cd-pipeline
**Date**: 2025-07-14

---

## Prerequisites

### Azure Setup

1. **Azure Subscription** with sufficient quota in `australiaeast` region
2. **Entra ID App Registration** with federated credentials for GitHub OIDC:
   - Issuer: `https://token.actions.githubusercontent.com`
   - Subject identifier for `main` branch: `repo:{owner}/{repo}:ref:refs/heads/main`
   - Subject identifier for environments: `repo:{owner}/{repo}:environment:staging` and `repo:{owner}/{repo}:environment:production`
3. **Azure RBAC**: Assign the app registration `Contributor` role on the target subscription (or individual resource groups)

### GitHub Setup

1. **Repository Variables** (Settings → Secrets and variables → Actions → Variables):
   - `AZURE_CLIENT_ID` — Entra ID application (client) ID
   - `AZURE_TENANT_ID` — Entra ID directory (tenant) ID
   - `AZURE_SUBSCRIPTION_ID` — Azure subscription ID

2. **GitHub Environments** (Settings → Environments):
   - Create `staging` environment (no protection rules)
   - Create `production` environment with:
     - Required reviewers: Add authorized team members
     - Wait timer: (optional, for additional delay)

3. **Labels**: Create `infrastructure-drift` label in the repository

---

## Files Created by This Feature

| File | Purpose |
|------|---------|
| `.github/workflows/cd.yml` | CD pipeline: staging deploy → gates → production |
| `.github/workflows/drift-detection.yml` | Weekly infrastructure drift detection |
| `scripts/rollback.sh` | Automated rollback script |
| `infra/main.parameters.staging.json` | Staging environment Bicep parameters |
| `infra/main.parameters.production.json` | Production environment Bicep parameters |

---

## Verifying the Setup

### 1. Verify CD Pipeline Triggers

```bash
# Push a change to main (or merge a PR)
git checkout main
git pull
# Make a minor change (e.g., update a comment)
git add . && git commit -m "test: verify CD pipeline trigger"
git push origin main
```

Then in GitHub Actions:
1. Wait for the `ci` workflow to complete (green check)
2. The `cd` workflow should trigger automatically
3. Check the `deploy-staging` job runs and completes

### 2. Verify Health Checks Locally

```bash
# Test health endpoints (if services are running locally)
curl -f http://localhost:8000/api/health
curl -f http://localhost:8080/health
curl -f http://localhost:8081/health
curl -f http://localhost:3000/
```

### 3. Verify Rollback Script

```bash
# Dry-run rollback (no Azure changes)
chmod +x scripts/rollback.sh
./scripts/rollback.sh \
  --environment staging \
  --resource-group rg-drh-staging \
  --dry-run
```

### 4. Verify Drift Detection

```bash
# Trigger manually from GitHub Actions UI
# Go to Actions → "Drift Detection" → "Run workflow"
```

---

## Pipeline Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   PR Merge   │────▶│   CI (ci.yml) │────▶│ CD: Deploy       │────▶│ CD: Gates        │
│   to main    │     │   quality job │     │ Staging          │     │ security + health│
└─────────────┘     └──────────────┘     └──────────────────┘     └──────────────────┘
                                                                           │
                                                                    Gates Pass?
                                                                    ┌──────┴──────┐
                                                                    │ Yes         │ No
                                                                    ▼             ▼
                                                            ┌──────────────┐  Pipeline
                                                            │ Manual       │  Stops
                                                            │ Approval     │
                                                            │ (production) │
                                                            └──────┬───────┘
                                                                   │ Approved
                                                                   ▼
                                                            ┌──────────────┐
                                                            │ CD: Deploy   │
                                                            │ Production   │
                                                            └──────────────┘
```

---

## Concurrency Behavior

- **One deployment at a time** per environment
- If a deployment is in progress and another commit triggers the pipeline, the new deployment **queues** (does not cancel the running one)
- GitHub Actions enforces a 6-hour timeout on stuck jobs

---

## Rollback Behavior

```
Deployment Completes
        │
        ▼
  Health Checks (parallel, 4 services)
        │
   ┌────┴────┐
   │ All     │ Any
   │ Pass    │ Fail
   ▼         ▼
Mark as    Rollback All Services
Known-Good    │
              ▼
        Re-check Health
              │
         ┌────┴────┐
         │ Pass    │ Fail
         ▼         ▼
    Rollback     CRITICAL FAILURE
    Success      Manual Intervention
                 (GitHub Issue created)
```

---

## Environment Configuration

| Setting | Staging | Production |
|---------|---------|------------|
| `environmentName` | `drh-staging` | `drh-production` |
| `location` | `australiaeast` | `australiaeast` |
| Resource Group | `rg-drh-staging` | `rg-drh-production` |
| Manual Approval | No | Yes (required reviewers) |
| Concurrency Group | `deploy-staging` | `deploy-production` |
| Parameter File | `main.parameters.staging.json` | `main.parameters.production.json` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| CD workflow doesn't trigger | Check CI workflow name matches `"ci"` in `workflow_run` trigger |
| Azure login fails | Verify federated credential configuration in Entra ID; check subject identifier matches branch/environment |
| `azd provision` fails | Check resource group exists; verify RBAC permissions; check Azure quota |
| Health checks fail after deploy | Check service health endpoints are implemented; verify service startup time |
| Rollback fails | Check Azure CLI is authenticated; verify previous revision exists |
| Drift detection reports false positives | Update the false-positive filter list in the workflow |
