# Quickstart — Simplify CI/CD with Branch-Based Deployment

This runbook is for the **operator** who configures the GitHub repository and Azure subscription so the pipeline introduced by spec `031-simplify-cicd-pipeline` works end-to-end. It is also the **smoke test** that the spec's success criteria are met.

Read time: ~10 minutes. Active operator time (one-off setup): ~30 minutes per environment.

## Prerequisites

- Repository admin permissions on `johnbilliris/ama`.
- Azure subscription owner (or Contributor + User Access Administrator) for the subscription that will host `rg-drh-dev`, `rg-drh-staging`, `rg-drh-production`.
- Azure CLI 2.x logged in (`az login`).
- GitHub CLI 2.x logged in (`gh auth status`).

## One-time setup

### 1. Create the three environment branches (admin-only)

```bash
# Repo root
git checkout main
git pull --ff-only
git push origin main:dev
git push origin main:staging
git push origin main:production
```

(Or via the GitHub UI: Branches → New branch → from `main`.)

**Recommended branch protection** (per environment branch — operator's call, out of scope for this PR):
- Require a PR before merging.
- Require at least 1 approving review.
- Require status check `ci / quality` to pass.
- Restrict who can push (`production` should be tightest).

### 2. Create three service principals (one per environment)

For each environment in `dev staging production`:

```bash
ENV=dev   # repeat for staging and production
SUB=$(az account show --query id -o tsv)

az ad sp create-for-rbac \
  --name "sp-drh-${ENV}-cicd" \
  --role "Contributor" \
  --scopes "/subscriptions/${SUB}" \
  --sdk-auth > "azure-credentials-${ENV}.json"
```

Each output is the JSON object documented in `contracts/azure-credentials.schema.json`. **Treat as a secret — do not commit.**

> Note: `--sdk-auth` is deprecated by Microsoft but is still the canonical shape that `azure/login@v3 with: creds:` consumes. The deprecation does not affect functionality; the OIDC migration tracked by ADR-031 will ultimately retire this approach.

### 3. Create the three GitHub Environments

```bash
# Per environment
for ENV in dev staging production; do
  gh api -X PUT "/repos/johnbilliris/ama/environments/${ENV}" -f wait_timer=0
done
```

Then add the secret:

```bash
for ENV in dev staging production; do
  gh secret set AZURE_CREDENTIALS \
    --env "${ENV}" \
    --body "$(cat azure-credentials-${ENV}.json)"
done
```

(After verifying via `gh secret list --env ${ENV}`, **delete the local `azure-credentials-*.json` files**.)

### 4. Bootstrap the dev resource group (first run)

The first push to `dev` will run `azd provision` against an empty subscription scope; this creates `rg-drh-dev` and provisions the Bicep template with `infra/main.parameters.dev.json`. Expect 8–12 minutes.

```bash
git checkout dev
git commit --allow-empty -m "chore: bootstrap dev environment"
git push origin dev
```

Watch the Actions UI:
- `ci` runs → green
- `cd` runs (triggered by `workflow_run`) → deploys to `rg-drh-dev`

Repeat for `staging` and `production` (the latter two should already have resource groups from earlier deployments).

## Daily operations

### Deploy to dev

```bash
git checkout dev
git merge --ff-only main          # bring in latest validated changes from main
git push origin dev
```

`ci` runs (~5 min); on success, `cd` runs (~10 min) and deploys to `rg-drh-dev`. No human intervention.

### Promote dev → staging

```bash
git checkout staging
git merge --ff-only dev
git push origin staging
```

(Or open a PR `dev → staging` if you've enabled the recommended branch protection.)

### Promote staging → production

Same pattern, `staging → production`. Production deploys go through whatever review you've enforced via branch protection.

### Roll back staging or production

The pipeline rolls back automatically on health-check failure for staging/production. Manual rollback:

```bash
scripts/rollback.sh --environment staging --resource-group rg-drh-staging
```

(Dev does not auto-rollback — push a fix commit to `dev` instead.)

### Rotate `AZURE_CREDENTIALS` (every 90 days)

Per environment:

```bash
ENV=dev
CLIENT_ID=$(jq -r '.clientId' azure-credentials-${ENV}.json)   # if you kept it; otherwise from KV

# Issue a new secret, append (does not invalidate the old one immediately)
NEW=$(az ad sp credential reset --id "${CLIENT_ID}" --append --years 1 -o json)

# Build the new sdk-auth shape (clientId/tenantId/subscriptionId stay the same; only clientSecret changes)
NEW_SECRET=$(echo "${NEW}" | jq -r '.password')
NEW_JSON=$(jq --arg s "${NEW_SECRET}" '.clientSecret=$s' azure-credentials-${ENV}.json)

# Push to GitHub
echo "${NEW_JSON}" | gh secret set AZURE_CREDENTIALS --env "${ENV}" --body -

# After verifying a successful deploy, revoke the old credential's keyId
# az ad sp credential delete --id "${CLIENT_ID}" --key-id <old-keyId>
```

## Smoke tests (verify spec success criteria)

| Test | Steps | Pass condition (maps to SC-#) |
|---|---|---|
| `dev` push deploys to dev only | Push empty commit to `dev`; wait. | Single `cd` run; resource changes only in `rg-drh-dev`; no changes in `rg-drh-staging` or `rg-drh-production`. (SC-001) |
| Single secret per env | `gh secret list --env dev` | Output contains `AZURE_CREDENTIALS` and **only** `AZURE_CREDENTIALS` for Azure auth. (SC-002, SC-005) |
| Spec-029 footprint deleted | `ls .github/workflows/` | No file matching `spec029-*` or any of: `change-freeze`, `posture-exception-sweep`, `evidence-pack`, `dev-key-issue`, `emergency-hotfix`, `_reusable/`. `tools/pipeline/` directory does not exist. (SC-003) |
| Drift detection scope | Trigger `drift-detection` via UI dispatch | Exactly two jobs run: `staging`, `production`. (SC-004) |
| New contributor onboarding | Time the steps in §1–4 above | ≤30 minutes per environment. (SC-005) |
| ADR exists | `cat docs/aidr/decisions/adr-031-azure-credentials-mvp.md` | File exists; references this spec; names an owner; names a review trigger. (SC-006) |
| No deploy-time regression | Compare `cd` end-to-end time vs the previous pipeline | New time ≤ old baseline. (SC-007) |
| Three FR-020 recommendations presented | Reviewer message at end of implementation | Three recommendations enumerated, each with proposed change + reason + trade-off; each requires individual operator response. (SC-008) |

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `cd` did not run after `ci` succeeded | Push was on a non-environment branch, or `ci` was triggered by a PR. | Confirm push was to `dev`/`staging`/`production`; PRs to `main` do not trigger `cd` by design. |
| `cd` ran but deployed an old commit | Workflow checked out default branch instead of `head_sha`. | Confirm step 1 of `cd.yml` has `ref: ${{ github.event.workflow_run.head_sha }}`. |
| `azure/login` fails with `Could not parse credentials` | `AZURE_CREDENTIALS` is not valid JSON or missing required fields. | Validate against `contracts/azure-credentials.schema.json`; recreate via `az ad sp create-for-rbac --sdk-auth`. |
| `cd` runs but deploys to the wrong environment | Dynamic `environment:` did not resolve. | Confirm `environment: ${{ github.event.workflow_run.head_branch }}` is at job level, not step level. |
| Drift detection runs against `dev` | Matrix not updated. | Confirm `strategy.matrix.environment: [staging, production]` in `drift-detection.yml`. |
| First push to `production` fails with "resource group not found" | Bootstrap not done. | Allow `azd provision` to run (it creates the RG); subsequent pushes are faster. |
| `cd` for `dev` failed but no critical-issue was opened | Working as designed (FR-015b). | Push a fix commit to `dev`. |

## Rollback to the previous pipeline (escape hatch)

If this simplification needs to be reverted:

```bash
git revert <merge-sha-of-spec-031>
git push origin main
```

The old `cd.yml` (with `workflow_run` for `main` only and OIDC) and the spec-029 footprint will return. The `AZURE_CREDENTIALS` secrets you created remain in the GitHub Environments and can be left in place or deleted.
