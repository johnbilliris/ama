# Contract: Drift Detection Workflow (`.github/workflows/drift-detection.yml`)

**Feature**: 017-cd-pipeline
**Date**: 2025-07-14
**Type**: GitHub Actions Workflow

---

## Trigger

```yaml
on:
  schedule:
    - cron: "0 16 * * 6"    # Saturday 16:00 UTC = Sunday 02:00 AEST
  workflow_dispatch:          # Manual trigger for on-demand checks
```

**Note**: Cron uses UTC. During AEDT (daylight saving), this runs at Sunday 03:00 local time, which is acceptable per research R-006.

---

## Permissions

```yaml
permissions:
  id-token: write     # OIDC token for Azure login
  contents: read      # Checkout repository (Bicep files)
  issues: write       # Create issues for drift findings
```

---

## Environment Variables (Repository Level)

Same as CD workflow:

| Variable | Type | Source | Description |
|----------|------|--------|-------------|
| `AZURE_CLIENT_ID` | `vars` | GitHub repo variable | Entra ID app client ID |
| `AZURE_TENANT_ID` | `vars` | GitHub repo variable | Entra ID tenant ID |
| `AZURE_SUBSCRIPTION_ID` | `vars` | GitHub repo variable | Azure subscription ID |

---

## Jobs

### Job: `detect-drift`

**Runs on**: `ubuntu-latest`
**Strategy**: Matrix over environments `[staging, production]`

**Steps**:

1. **Checkout** — `actions/checkout@v4`
2. **Azure Login** — `azure/login@v2` with OIDC
3. **Run What-If** — Execute `az deployment group what-if`:
   ```bash
   az deployment group what-if \
     --resource-group "rg-drh-${ENVIRONMENT}" \
     --template-file infra/main.bicep \
     --parameters "@infra/main.parameters.${ENVIRONMENT}.json" \
     --result-format FullResourcePayloads \
     --no-pretty-print \
     -o json > what-if-output.json
   ```
4. **Parse Results** — Filter out false-positive fields and extract meaningful drift:
   - Ignore: `provisioningState`, `etag`, `identity.principalId`, timestamps, `uniqueId`
   - Keep: Any `Modify`, `Create`, or `Delete` change types on declarative properties
5. **Generate Report** — Format drift findings into markdown
6. **Create GitHub Issue** (if drift detected):
   ```bash
   gh issue create \
     --title "Infrastructure drift detected: ${ENVIRONMENT} ($(date +%Y-%m-%d))" \
     --body "${DRIFT_REPORT}" \
     --label "infrastructure-drift"
   ```
7. **Report Clean State** — If no drift, log "No drift detected" in job summary

---

## Output: GitHub Issue Format

**Title**: `Infrastructure drift detected: {environment} (YYYY-MM-DD)`

**Labels**: `infrastructure-drift`

**Body**:
```markdown
## Infrastructure Drift Report

**Environment**: {environment}
**Resource Group**: rg-drh-{environment}
**Detected**: YYYY-MM-DD HH:MM UTC
**Workflow Run**: {link to workflow run}

### Summary

| Metric | Count |
|--------|-------|
| Resources with drift | {count} |
| Properties modified | {count} |
| Resources to create | {count} |
| Resources to delete | {count} |

### Drifted Resources

| Resource | Type | Change | Property | Expected | Actual |
|----------|------|--------|----------|----------|--------|
| {name} | {type} | Modify | {path} | {expected} | {actual} |
| ... | ... | ... | ... | ... | ... |

### Filtered (Likely False Positives)

The following system-managed properties were excluded from this report:
- `provisioningState`, `etag`, `identity.principalId`, timestamps

### Next Steps

1. Review each drifted resource to determine if the change was intentional
2. If unintentional: run `azd provision` to restore IaC-defined state
3. If intentional: update the Bicep templates to match the desired state
4. Close this issue when drift is resolved
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Azure login failure | Job fails with authentication error; no false "clean" report |
| Resource group doesn't exist | `what-if` fails; job reports error (environment not provisioned) |
| `what-if` command failure | Job fails; error surfaced in workflow summary |
| GitHub Issue creation failure (API rate limit) | Job fails; drift findings available in workflow logs |
| No drift detected | No issue created; clean status logged in job summary |

---

## False Positive Mitigation

Properties to ignore in drift analysis (runtime/system-managed):

```json
[
  "provisioningState",
  "etag",
  "identity.principalId",
  "identity.tenantId",
  "properties.createdAt",
  "properties.lastModifiedAt",
  "properties.uniqueId",
  "systemData",
  "properties.hostNames",
  "properties.defaultHostName",
  "properties.outboundIpAddresses",
  "properties.possibleOutboundIpAddresses"
]
```
