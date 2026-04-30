# Operator REST API — Workflow Runs

**Contract**: `apps/api/app/api/routes/workflow_runs.py`  
**Mounted at**: `/api/workflow_runs` (under the existing `settings.api_prefix = "/api/"`)  
**Authentication**: Existing `auth.py` middleware (Bearer token via Entra ID).  
**Authorisation**: Read-only for all callers in the `EmergencyOperator` Entra group; mutating endpoints (cancel) require the `EmergencyCommander` group.

This contract backs FR-011 (workflows are addressable, listable, inspectable), FR-011b (state-filterable), and the operator-facing pieces of SC-008 (approval-gate metrics) and SC-009 (no dashboard regression).

---

## GET /api/workflow_runs

List workflow runs.

**Query parameters**:

| Param | Type | Notes |
|---|---|---|
| `incident_id` | string | Optional. Filter to a single incident (returns at most 1 active + N terminal runs per FR-011a). |
| `status` | string \| array | Optional. One or more of the 7 canonical states. Repeatable: `?status=Running&status=AwaitingApproval`. |
| `tenant_id` | string | Optional. Defaults to the caller's tenant. |
| `limit` | int | Default 50, max 200. |
| `continuation` | string | Cosmos continuation token; opaque. |

**Response 200**:

```json
{
  "items": [
    { "...workflow-run.schema.json document..." }
  ],
  "continuation": "<opaque token or null>"
}
```

---

## GET /api/workflow_runs/{run_id}

Retrieve a single run.

**Response 200**: a `workflow-run.schema.json` document.  
**Response 404**: `{ "error": "not_found" }`.

---

## GET /api/workflow_runs/{run_id}/checkpoints

List checkpoints for a run, in `sequence` order.

**Response 200**:

```json
{
  "items": [
    { "...checkpoint.schema.json document..." }
  ]
}
```

---

## GET /api/workflow_runs/{run_id}/audit

List audit entries linked to this run, in `started_at` order.

**Query parameters**:

| Param | Type | Notes |
|---|---|---|
| `agent` | string | Optional. Filter to one of the five agent names. |
| `outcome` | string | Optional. One of the audit-entry outcomes. |
| `limit` | int | Default 100, max 500. |

**Response 200**:

```json
{
  "items": [
    { "...audit-entry.schema.json document..." }
  ]
}
```

---

## POST /api/workflow_runs/{run_id}/cancel

Operator-initiated cancel. Requires `EmergencyCommander` group.

**Request body**:

```json
{ "reason": "free-text justification (audited)" }
```

**Response 200**: the updated `workflow-run.schema.json` document with `status = "Cancelled"`, `terminal_at` set.  
**Response 409** if the run is already in a terminal state: `{ "error": "already_terminal", "current_status": "Failed" }`.

---

## GET /api/workflow_runs/metrics/approval-gate

Approval-gate operator metrics (SC-008).

**Query parameters**:

| Param | Type | Notes |
|---|---|---|
| `window` | string | One of `1h`, `24h`, `7d`, `30d`. Default `24h`. |

**Response 200**:

```json
{
  "window": "24h",
  "mtta_seconds": 142,
  "approvals": 87,
  "modifications": 9,
  "rejections": 2,
  "escalations": 5,
  "timeouts": 1
}
```

---

## Behaviours

- All endpoints MUST set `Cache-Control: no-store` (matches existing repo convention for operator data).
- All list endpoints MUST honour the caller's `tenant_id` claim (existing tenancy enforcement).
- All mutating endpoints MUST emit an audit entry (re-uses the same audit middleware as agent invocations) tagged with `event: "operator.workflow_action"`.
- `GET /api/workflow_runs/metrics/approval-gate` reads from the existing Application Insights (Azure Monitor) backend via the existing `appi_query` helper — does NOT introduce a new query backend.

---

## Error model

All endpoints follow the existing AMA API error envelope:

```json
{
  "error": "<machine_readable_code>",
  "message": "<human readable>",
  "correlation_id": "<trace_id>"
}
```

Error codes specific to this contract:

| Code | Status | Meaning |
|---|---|---|
| `not_found` | 404 | Run or checkpoint not found in the caller's tenant. |
| `already_terminal` | 409 | Cancel attempted against a run that has already reached a terminal status. |
| `invalid_state` | 409 | Reserved — for any future state-transition operator actions; unused by this contract. |
| `forbidden` | 403 | Caller lacks the required Entra group membership. |
