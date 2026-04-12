# Contract: Rollback Script (`scripts/rollback.sh`)

**Feature**: 017-cd-pipeline
**Date**: 2025-07-14
**Type**: Bash Script (GitHub Actions `ubuntu-latest` compatible)

---

## Interface

```bash
scripts/rollback.sh \
  --environment <staging|production> \
  --resource-group <resource-group-name> \
  [--revision-api <revision-name>] \
  [--revision-agents <revision-name>] \
  [--revision-ingestion <revision-name>] \
  [--revision-web <deployment-id>] \
  [--dry-run]
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--environment` | Yes | — | Target environment name (`staging` or `production`) |
| `--resource-group` | Yes | — | Azure resource group name |
| `--revision-api` | No | — | Previous known-good Container Apps revision for `api` |
| `--revision-agents` | No | — | Previous known-good Container Apps revision for `agents` |
| `--revision-ingestion` | No | — | Previous known-good Container Apps revision for `ingestion` |
| `--revision-web` | No | — | Previous known-good App Service deployment ID for `web` |
| `--dry-run` | No | `false` | Print rollback actions without executing |

**Note**: If individual revision parameters are not provided, the script discovers the previous revision from Azure (second-most-recent active revision for Container Apps, previous deployment for App Service).

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Rollback completed successfully; all services restored to known-good state |
| 1 | Rollback failed: one or more services could not be restored |
| 2 | Invalid arguments or missing required parameters |
| 3 | Azure CLI not available or authentication failure |
| 4 | Health check after rollback failed (critical failure — manual intervention required) |

---

## Execution Flow

```
1. Validate inputs
   ├── Check Azure CLI is available
   ├── Validate --environment is staging or production
   └── Validate --resource-group is non-empty

2. Discover current and target revisions (if not provided)
   ├── For Container Apps (api, agents, ingestion):
   │   └── az containerapp revision list → find previous active revision
   └── For App Service (web):
       └── az webapp deployment list → find previous deployment

3. Execute rollback
   ├── For Container Apps:
   │   ├── az containerapp revision activate --revision <previous>
   │   └── az containerapp revision deactivate --revision <current>
   └── For App Service:
       └── az webapp deployment source config-zip (redeploy previous)

4. Verify rollback (health checks)
   ├── Check api at /api/health (30s timeout, 3 retries)
   ├── Check agents at /health (30s timeout, 3 retries)
   ├── Check ingestion at /health (30s timeout, 3 retries)
   └── Check web at / (30s timeout, 3 retries)

5. Report result
   ├── Exit 0: All health checks pass → rollback successful
   └── Exit 4: Any health check fails → CRITICAL FAILURE
```

---

## Output Format

**stdout** (structured for pipeline consumption):

```
[ROLLBACK] Environment: staging
[ROLLBACK] Resource Group: rg-drh-staging
[ROLLBACK] Rolling back api: rev-current → rev-previous
[ROLLBACK] Rolling back agents: rev-current → rev-previous
[ROLLBACK] Rolling back ingestion: rev-current → rev-previous
[ROLLBACK] Rolling back web: deploy-current → deploy-previous
[ROLLBACK] Verifying health checks...
[ROLLBACK] api: HEALTHY (200, 45ms)
[ROLLBACK] agents: HEALTHY (200, 32ms)
[ROLLBACK] ingestion: HEALTHY (200, 28ms)
[ROLLBACK] web: HEALTHY (200, 120ms)
[ROLLBACK] ✅ Rollback completed successfully
```

**stderr** (error reporting):

```
[ROLLBACK] ❌ ERROR: Health check failed for api after rollback
[ROLLBACK] ❌ CRITICAL: Rollback failed — manual intervention required
```

---

## Security Requirements (per CHK067)

- **Input validation**: All parameters are validated before use; no shell injection via parameter values.
- **No secret handling**: Script does not read or write secrets. Azure authentication is pre-established by the pipeline (`azure/login@v2`).
- **No privilege escalation**: Script runs with the same permissions as the GitHub Actions runner. No `sudo` or elevated commands.
- **Idempotent**: Running the script multiple times with the same parameters produces the same result (activating an already-active revision is a no-op).

---

## Dependencies

- `az` CLI (pre-installed on `ubuntu-latest`)
- `curl` (pre-installed on `ubuntu-latest`)
- `jq` (pre-installed on `ubuntu-latest`)
- Active Azure session (via `azure/login@v2` in the calling workflow)

---

## Rollback Time Budget

| Phase | Budget | Notes |
|-------|--------|-------|
| Revision discovery | ~10s | Azure API calls |
| Container Apps rollback (3 services) | ~60s | Revision activation/deactivation |
| App Service rollback (1 service) | ~30s | Redeployment |
| Health checks | ≤2 min | FR-010 compliant |
| **Total** | **≤5 min** | SC-003 target |
