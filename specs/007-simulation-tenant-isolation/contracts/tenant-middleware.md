# Contract: Tenant Middleware

**Feature**: 007-simulation-tenant-isolation | **Date**: 2026-04-09

## Purpose

Global FastAPI middleware that resolves `TenantContext` on every authenticated request. Ensures all downstream operations (services, repositories, agents, audit) are tenant-scoped.

## Request Flow

```
Request → Entra ID Token Validation → Tenant Middleware → Route Handler → Service → Repository (tenant-scoped)
```

### Middleware Behaviour

1. **Extract authenticated principal** from the validated Entra ID token (existing `extract_principal_from_claims()`)
2. **Resolve tenant_id**:
   - If the user has an active simulation participation → `tenant_id = sim-{scenarioRunId}`
   - If the user has no active simulation, or the request is to a non-simulation endpoint → `tenant_id = live`
   - Simulation participation is checked via a Cosmos DB point-read on the `simulation` container
3. **Build TenantContext** with `tenant_id`, `agency_id`, `jurisdiction_ids`, `persona_id`
4. **Set context** in `contextvars.ContextVar` for the request lifecycle
5. **Add `tenant_id` to telemetry** — custom dimension on all Application Insights traces/metrics

### Routing Rules

| Request Path | Tenant Resolution |
|-------------|-------------------|
| `/api/simulations/*` (management) | Always `live` (management operations are admin-scoped) |
| `/api/simulations/{tenantId}/*` (data access within simulation) | `tenantId` from path, validated against participant list |
| `/api/signals`, `/api/dashboard`, etc. | Resolved from user's active simulation participation, or `live` |
| `/api/health`, `/api/docs` | No tenant context (unauthenticated) |

### Ingestion Pipeline (Special Case)

The ingestion pipeline (`apps/ingestion/`) does NOT use the tenant middleware. It uses a system-level managed identity and always writes to `tenant_id = live`. This is enforced by:
1. The ingestion pipeline has no user authentication — it uses `DefaultAzureCredential` (managed identity)
2. The signal partition key builder in the ingestion pipeline hardcodes `scope = "live"`
3. No simulation signals are ever routed through the ingestion pipeline

### Error Handling

| Condition | Response |
|-----------|----------|
| Missing/invalid Entra ID token | 401 Unauthorized |
| User lacks `SimulationUser` role for simulation endpoint | 403 Forbidden |
| User not in simulation's participant list | 403 Forbidden |
| Simulation tenant not found | 404 Not Found |
| Simulation tenant not in `active` or `paused` status | 409 Conflict |
| Cosmos DB unreachable during tenant resolution | 503 Service Unavailable (fail-safe: do NOT fall back to live) |

### Context Propagation

The `TenantContext` is propagated to downstream services via Python `contextvars`. All repository methods read the current tenant context to build partition keys, cache key prefixes, and blob storage paths. Services do not need to explicitly pass tenant context — it is ambient.

```python
_tenant_context_var: ContextVar[TenantContext] = ContextVar("tenant_context")

def get_current_tenant() -> TenantContext:
    return _tenant_context_var.get()

def set_current_tenant(ctx: TenantContext) -> None:
    _tenant_context_var.set(ctx)
```

### Agent Handoff Propagation

When the API creates an `AgentHandoffEvent`, it includes `tenant_id` in the payload. The agents service receives the handoff and sets the tenant context before processing. Agent HTTP calls back to the API include the tenant context via the standard Entra ID token flow.
