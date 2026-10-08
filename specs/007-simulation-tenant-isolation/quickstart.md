# Quickstart: Simulation Tenant Isolation

**Feature**: 007-simulation-tenant-isolation | **Contract version**: 2 | **Date**: 2026-09-16

This quickstart documents the request/response shapes the API implements today. Lifecycle values are
Title-Case and case-sensitive (`Provisioning`, `Active`, `Paused`, `Archiving`, `Archived`, `Deleted`) per
[contract-resolution.v2.json](contracts/contract-resolution.v2.json). Version 1 lowercase examples are superseded.

Commands below are authored guidance, not a captured run log. The executed evidence for this feature is the
`spec007_isolation` marker selection described in section 5.

## Prerequisites

- Python 3.12+, Node.js 20+
- Azure CLI logged in (`az login`)
- Docker running (for local Cosmos DB emulator or Azure connection)
- `.env` configured with Cosmos DB, Redis, and Azure OpenAI credentials

## 1. Create a Simulation Tenant

```bash
# POST to the simulation management endpoint
curl -X POST http://localhost:8000/api/simulations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_type": "Cyclone",
    "jurisdictions": ["qld"],
    "scenario_template_id": "qld-cyclone-multi-agency",
    "participants": ["<your-entra-oid>"],
    "warp_speed": 1.0,
    "resource_limits": {
      "max_signals": 10000,
      "max_recommendations": 500,
      "max_duration_hours": 48
    }
  }'
```

`201 Created` returns `tenant_id` (format `sim-{uuid}`), `scenario_run_id`, a Title-Case `status`, and the clock
fields `current_warp_speed`, `accumulated_sim_seconds`, `clock_paused`, `playback_status`. The caller's OID is
added to `participants` automatically when it is absent from the request.

## 2. Seed Scenario Data

### From a template

```bash
curl -X POST http://localhost:8000/api/simulations/sim-abc123/seed \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "qld-cyclone-multi-agency"
  }'
```

`202 Accepted`. The body carries `status: "accepted"` plus the seeding counters
(`signals_injected`, `signals_scheduled`, `organisations_seeded`). Seeding only *schedules* signals: the warp
scheduler delivers them on the server-owned clock, so `signals_injected` is `0` for scheduled runs. The tenant must
be `Active`, otherwise the route returns `409`.

### From historical data

```bash
curl -X POST http://localhost:8000/api/simulations/sim-abc123/seed/replay \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc-xyz-...",
    "start": "2026-03-15T06:00:00Z",
    "end": "2026-03-16T18:00:00Z",
    "time_compression": 10
  }'
```

The field names are `start`, `end` and `time_compression`; the version 1 `start_from` / `end_at` / `replay_mode`
fields are not accepted. A source incident outside the caller's jurisdictions returns `403`; an unknown incident
returns `404`.

## 3. Add Participants

```bash
curl -X POST http://localhost:8000/api/simulations/sim-abc123/participants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "participants": [
      {
        "oid": "<entra-oid-1>",
        "persona": "qfd",
        "organisation_id": "org-qfd",
        "jurisdiction_id": "qld",
        "role": "coordinator"
      },
      {
        "oid": "<entra-oid-2>",
        "persona": "qps",
        "organisation_id": "org-qps",
        "jurisdiction_id": "qld",
        "role": "participant"
      }
    ]
  }'
```

Participants are objects, not bare OID strings, and there is no separate `persona_assignments` array. The caller
must be the creator or hold a coordinator/admin role (`403` otherwise). Duplicate OIDs in one request return `422`,
as does a persona that is unknown or whose organisation/jurisdiction contradicts the persona catalogue or the
tenant's jurisdictions.

## 4. Verify Tenant Isolation

### Check that simulation signals are partitioned

```bash
# Query signals in the simulation tenant
curl http://localhost:8000/api/signals?limit=10 \
  -H "Authorization: Bearer $SIM_USER_TOKEN"
# Should return ONLY signals scoped to sim-abc123

# Query signals as a live user
curl http://localhost:8000/api/signals?limit=10 \
  -H "Authorization: Bearer $LIVE_USER_TOKEN"
# Should return ONLY live signals, no simulation data
```

### Check Redis key isolation

```bash
redis-cli KEYS "sim-abc123:*"   # Simulation cache keys
redis-cli KEYS "live:*"          # Live cache keys — no overlap
```

### Check Blob Storage isolation

Exercise reports and archive manifests are written to the `simulation` container under
`simulation/{tenant_id}/…`, not to a `reports` container:

```bash
az storage blob list --container-name simulation \
  --prefix "sim-abc123/" --account-name "$AZURE_STORAGE_ACCOUNT"
```

## 5. Run Cross-Tenant Leakage Tests

```bash
# From the repo root
pytest tests/integration/test_tenant_isolation.py -v

# Key test cases:
# - test_simulation_signals_invisible_to_live
# - test_live_signals_invisible_to_simulation
# - test_cross_simulation_isolation
# - test_partition_key_enforces_scope
# - test_request_context_rejects_caller_supplied_foreign_scope
# - test_constructor_binding_rejects_foreign_scope
# - test_cosmos_point_read_propagates_service_failure
```

The required release gate is the `spec007_isolation` marker selection wired into the
`simulation-tenant-isolation` CI job. Run the same selection locally with:

```bash
pytest -m spec007_isolation --strict-markers -q
```

`tools/lint/check_spec007_isolation_selector.py` fails if a marked module is missing from that CI job or if the
job stops asserting a nonzero collection.

## 6. Monitor Simulation Activity

### Application Insights KQL

```kql
// All traces for a specific simulation tenant
traces
| where customDimensions.tenant_id == "sim-abc123"
| order by timestamp desc
| take 50

// Compare agent latency: simulation vs live
requests
| where name startswith "POST /api/"
| extend tenant = tostring(customDimensions.tenant_id)
| summarize avg(duration), percentile(duration, 95) by tenant, name
| order by name asc
```

## 7. Lifecycle Operations

```bash
# Pause simulation (clock stops, scheduler delivery loop is cancelled)
curl -X POST http://localhost:8000/api/simulations/sim-abc123/pause \
  -H "Authorization: Bearer $TOKEN"

# Resume (clock restarts, scheduler delivery loop restarts)
curl -X POST http://localhost:8000/api/simulations/sim-abc123/resume \
  -H "Authorization: Bearer $TOKEN"

# Change warp speed (creator only; value must be in /api/simulations/meta/warp-speeds)
curl -X POST http://localhost:8000/api/simulations/sim-abc123/warp-speed \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"warp_speed": 10}'

# Archive — 202 Accepted with status "Archiving"; the job persists the report first
curl -X POST http://localhost:8000/api/simulations/sim-abc123/archive \
  -H "Authorization: Bearer $TOKEN"

# Poll until the tenant reports "Archived"
curl http://localhost:8000/api/simulations/sim-abc123 \
  -H "Authorization: Bearer $TOKEN"

# Delete (permanent; requires Archived status, an elapsed retention deadline, and an admin role)
curl -X DELETE http://localhost:8000/api/simulations/sim-abc123 \
  -H "Authorization: Bearer $TOKEN"
```

## 8. Read the Exercise Report

```bash
# Tenant-scoped read: 409 while the simulation is Active, 404 when no report exists yet
curl http://localhost:8000/api/simulations/sim-abc123/report \
  -H "Authorization: Bearer $TOKEN"

# Stable report-ID read: resolves the owning tenant, then checks membership
curl http://localhost:8000/api/simulations/reports/rpt-abc123 \
  -H "Authorization: Bearer $TOKEN"
```

Neither read generates a report. Reports are produced by the archive job only (`SIM-REPORT-MISSING`).

## Common Issues

| Symptom | Cause | Fix |
| ------- | ----- | --- |
| 403 on simulation endpoints | User lacks `SimulationUser` app role | Assign role in Entra ID or add to participant list |
| 409 on an operational route | Caller has more than one active simulation membership | Use an explicit `/api/simulations/{tenantId}/...` path |
| 404 on `GET /report` | The archive job has not persisted a report yet | Poll tenant detail until `status` is `Archived` |
| 503 during tenant resolution | Tenant store unreachable | Fail-closed by design — the middleware never falls back to `live` |
| Simulation signals appear in live dashboard | Partition key not prefixed with `sim-` | Check `cosmos_scope.py` scoped_partition_key() uses tenant_id |
| Agent chain not processing simulation signals | Handoff event missing `tenant_id` | Verify `create_handoff_event()` includes tenant context |
| Auto-throttle activating unexpectedly | Live incident detected during simulation | Expected behaviour — simulation throttles to 20% quota during active live incidents |
