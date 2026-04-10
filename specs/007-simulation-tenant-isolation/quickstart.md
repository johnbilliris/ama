# Quickstart: Simulation Tenant Isolation

**Feature**: 007-simulation-tenant-isolation | **Date**: 2026-04-09

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
    "scenario_type": "cyclone",
    "jurisdictions": ["qld-fnq", "qld-nq"],
    "scenario_template_id": "qld-cyclone-multi-agency",
    "participants": ["<your-entra-oid>"],
    "resource_limits": {
      "max_signals": 10000,
      "max_recommendations": 500,
      "max_duration_hours": 48
    }
  }'
```

Response includes `tenant_id` (format: `sim-{uuid}`).

## 2. Seed Scenario Data

### From a template

```bash
curl -X POST http://localhost:8000/api/simulations/sim-abc123/seed \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "cyclone-cat3-coastal",
    "replay_mode": "real-time"
  }'
```

### From historical data

```bash
curl -X POST http://localhost:8000/api/simulations/sim-abc123/seed/replay \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "incident_id": "inc-xyz-...",
    "start_from": "2024-12-01T00:00:00Z",
    "end_at": "2024-12-03T00:00:00Z",
    "replay_mode": "real-time"
  }'
```

## 3. Add Participants

```bash
curl -X POST http://localhost:8000/api/simulations/sim-abc123/participants \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "participants": ["<entra-oid-1>", "<entra-oid-2>"],
    "persona_assignments": [
      {"participant_oid": "<entra-oid-1>", "persona_id": "exercise-coordinator", "org_id": "qfes"},
      {"participant_oid": "<entra-oid-2>", "persona_id": "field-responder", "org_id": "qps"}
    ]
  }'
```

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

```bash
az storage blob list --container-name reports \
  --prefix "sim-abc123/" --account-name stamazo6bb5
```

## 5. Run Cross-Tenant Leakage Tests

```bash
# From the repo root
pytest tests/integration/test_tenant_isolation.py -v

# Key test cases:
# - test_simulation_signals_invisible_to_live_users
# - test_live_signals_invisible_to_simulation_users
# - test_simulation_user_cannot_access_other_simulation
# - test_simulation_agent_chain_stays_in_tenant
# - test_cosmos_partition_key_enforces_scope
# - test_redis_keys_prefixed_by_tenant
```

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
# Pause simulation (agents stop, signals queue)
curl -X POST http://localhost:8000/api/simulations/sim-abc123/pause \
  -H "Authorization: Bearer $TOKEN"

# Resume
curl -X POST http://localhost:8000/api/simulations/sim-abc123/resume \
  -H "Authorization: Bearer $TOKEN"

# Archive (generates exercise report, moves to cold storage)
curl -X POST http://localhost:8000/api/simulations/sim-abc123/archive \
  -H "Authorization: Bearer $TOKEN"

# Delete (permanent, requires archived status)
curl -X DELETE http://localhost:8000/api/simulations/sim-abc123 \
  -H "Authorization: Bearer $TOKEN"
```

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| 403 on simulation endpoints | User lacks `SimulationUser` app role | Assign role in Entra ID or add to participant list |
| Simulation signals appear in live dashboard | Partition key not prefixed with `sim-` | Check `cosmos_scope.py` scoped_partition_key() uses tenant_id |
| Agent chain not processing simulation signals | Handoff event missing `tenant_id` | Verify `create_handoff_event()` includes tenant context |
| Auto-throttle activating unexpectedly | Live incident detected during simulation | Expected behaviour — simulation throttles to 20% quota during active live incidents |
