# Data Model: CD Pipeline with Staging Environment

**Feature**: 017-cd-pipeline
**Date**: 2025-07-14

---

## Entities

### Environment

An isolated Azure deployment target with its own resource group, configuration, and secrets.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| name | string | enum: `staging`, `production` | Environment identifier |
| azure_env_name | string | max 64 chars, alphanumeric + hyphens | `azd` environment name (e.g., `drh-staging`) |
| location | string | enum: `australiaeast`, `australiasoutheast` | Primary Azure region |
| resource_group | string | derived from azure_env_name | `rg-{azure_env_name}` |
| subscription_id | string | UUID format | Azure subscription |
| client_id | string | UUID format | Entra ID app registration for OIDC |
| tenant_id | string | UUID format | Entra ID tenant |
| parameter_file | string | file path | `infra/main.parameters.{name}.json` |
| requires_approval | boolean | | `false` for staging, `true` for production |
| concurrency_group | string | derived | `deploy-{name}` |

**Relationships**:
- Environment 1:N Deployment Revision
- Environment 1:1 Parameter File
- Environment 1:N Health Check Result

**Validation Rules**:
- `location` MUST be an Australian Azure region
- `name` MUST be unique across all environments
- `parameter_file` MUST exist at the specified path
- `requires_approval` MUST be `true` for production

---

### Deployment Revision

A versioned snapshot of all deployed services at a point in time.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | auto-generated | Unique revision identifier |
| environment | string | FK → Environment.name | Target environment |
| git_sha | string | 40-char hex | Source commit SHA |
| workflow_run_id | integer | positive | GitHub Actions run ID |
| timestamp | datetime | ISO 8601 UTC | Deployment completion time |
| status | string | enum: `deploying`, `healthy`, `unhealthy`, `rolled-back` | Current state |
| is_known_good | boolean | | `true` if all health checks passed post-deployment |
| services | object[] | array of ServiceRevision | Per-service revision details |

**Relationships**:
- Deployment Revision N:1 Environment
- Deployment Revision 1:N Health Check Result
- Deployment Revision 1:N Service Revision

**State Transitions**:
```
deploying → healthy       (all health checks pass → mark as known-good)
deploying → unhealthy     (any health check fails → trigger rollback)
unhealthy → rolled-back   (rollback executed → services reverted)
rolled-back → [terminal]  (rollback succeeded, previous revision restored)
unhealthy → CRITICAL       (rollback also fails → manual intervention required)
```

**Validation Rules**:
- Only one revision per environment can have `is_known_good = true` at a time
- `status` transitions are one-directional (no going back to `deploying`)

---

### Service Revision

Per-service deployment details within a Deployment Revision.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| service_name | string | enum: `api`, `agents`, `ingestion`, `web` | Service from `azure.yaml` |
| host_type | string | enum: `containerapp`, `appservice` | Azure hosting type |
| revision_name | string | | Container Apps revision name or App Service deployment ID |
| image | string | nullable | Container image reference (null for App Service) |
| health_endpoint | string | | Health check URL path |
| health_port | integer | nullable | Port for health check (null for App Service) |

**Fixed Values** (from codebase):

| Service | Host | Health Endpoint | Port |
|---------|------|-----------------|------|
| api | containerapp | `/api/health` | 8000 |
| agents | containerapp | `/health` | 8080 |
| ingestion | containerapp | `/health` | 8081 |
| web | appservice | `/` | N/A |

---

### Deployment Gate

An automated or manual check that must pass before promotion.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| name | string | unique per pipeline run | Gate identifier |
| type | string | enum: `ci-verification`, `security-scan`, `health-check`, `manual-approval` | Gate category |
| status | string | enum: `pending`, `running`, `passed`, `failed`, `skipped` | Current state |
| started_at | datetime | ISO 8601 UTC | Gate execution start |
| completed_at | datetime | nullable, ISO 8601 UTC | Gate execution end |
| failure_details | string | nullable | Reason for failure (null if passed) |
| required | boolean | | Whether gate failure blocks promotion |

**Gate Execution Order** (FR-002):
1. `ci-verification` — Verified by `workflow_run` trigger (always passes if pipeline reached this point)
2. `security-scan` — `ruff check` + `pip-audit`
3. `health-check` — All 4 service health endpoints
4. `manual-approval` — GitHub Environment protection rule (production only)

**Validation Rules**:
- Gates MUST execute in order; a gate failure stops subsequent gates
- `manual-approval` gate auto-rejects after 72 hours (FR-003)

---

### Drift Report

Comparison of actual Azure infrastructure state against IaC definitions.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | string | auto-generated | Report identifier |
| environment | string | FK → Environment.name | Checked environment |
| timestamp | datetime | ISO 8601 UTC | Detection time |
| workflow_run_id | integer | positive | GitHub Actions run ID |
| has_drift | boolean | | Whether any drift was detected |
| drifted_resources | object[] | array of DriftedResource | List of changed resources |
| github_issue_number | integer | nullable | Created issue number (null if no drift) |

---

### Drifted Resource

A single resource that has drifted from IaC definitions.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| resource_id | string | Azure resource ID | Full ARM resource ID |
| resource_type | string | | ARM resource type (e.g., `Microsoft.App/containerApps`) |
| change_type | string | enum: `Create`, `Delete`, `Modify`, `NoChange` | Type of drift |
| property_changes | object[] | array of PropertyChange | Property-level diffs |

---

### Property Change

A single property-level difference within a drifted resource.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| path | string | JSON path notation | Property path (e.g., `properties.configuration.maxReplicas`) |
| expected | string | nullable | Value defined in IaC |
| actual | string | nullable | Value in live Azure |

---

### Health Check Result

Outcome of a health endpoint probe.

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| service_name | string | FK → ServiceRevision.service_name | Checked service |
| endpoint | string | URL | Full health check URL |
| attempt | integer | 1-3 | Retry attempt number |
| status_code | integer | nullable | HTTP response status |
| response_time_ms | integer | nullable | Response time in milliseconds |
| passed | boolean | | Whether the check passed |
| error | string | nullable | Error message if failed |
| timeout | boolean | | Whether the check timed out (30s per FR-010) |
