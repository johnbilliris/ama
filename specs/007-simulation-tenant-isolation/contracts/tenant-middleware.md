# Contract: Tenant Middleware

**Feature**: 007-simulation-tenant-isolation | **Contract version**: 2 | **Date**: 2026-09-16

Lifecycle values use the canonical Title-Case strings defined in [contract-resolution.v2.json](contract-resolution.v2.json): `Provisioning`, `Active`, `Paused`, `Archiving`, `Archived`, `Deleted`. Version 1 lowercase examples are superseded; comparisons are case-sensitive.

## Purpose

`TenantMiddleware` (`apps/api/app/middleware/tenant_middleware.py`, registered through `add_tenant_middleware`) resolves a `TenantContext` for every request that already carries validated claims, so downstream services, repositories, agents and audit writers are tenant-scoped without passing the tenant explicitly.

## Request Flow

```text
Request → Auth middleware (request.state.claims) → Tenant middleware → Route → Service → Repository (tenant-scoped)
```

### Middleware Behaviour

1. **Skip unauthenticated paths.** Requests whose path starts with `/api/health`, `/api/docs` or `/api/openapi.json` are forwarded with no tenant context.
2. **Skip unauthenticated requests.** When `request.state.claims` is absent the request is forwarded unchanged. This middleware never issues `401`; authentication is owned by the auth middleware and route dependencies.
3. **Extract the principal** with `extract_principal_from_claims()`.
4. **Resolve `tenant_id`** using the rules in *Routing Rules* below.
5. **Build `TenantContext`** with `tenant_id`, `agency_id`, `jurisdiction_ids`, `persona_id` and publish it on a `contextvars.ContextVar` for the request lifetime, resetting the token in a `finally` block.
6. **Annotate telemetry** through `annotate_current_span(ctx)` so the resolved tenant reaches the current span.
7. **Echo the resolution** as the `X-Tenant-Id` response header.
8. **Record idle activity.** Per `SIM-TTL-IDLE`, a successful (`< 400`) `POST`/`PUT`/`PATCH` on a `sim-` tenant calls `simulation_repository.touch_activity(tenant_id)`. Archive paths are excluded so archiving cannot keep extending its own TTL.

### Routing Rules

| Request Path | Tenant Resolution |
| ------------ | ----------------- |
| `/api/health`, `/api/docs`, `/api/openapi.json` | No tenant context |
| `/api/simulations/sim-{uuid}/...` | `sim-{uuid}` from the path, membership-checked against the stored tenant |
| `/api/simulations` and every other `/api/simulations/...` path (create, list, `meta/*`, `reports/{reportId}`) | `live` |
| `/api/signals`, `/api/dashboard`, other operational routes | Inferred from active membership, else `live` |

Ambient inference for operational routes uses `simulation_repository.get_by_participant(subject)`:

- exactly one active membership → that `tenant_id`
- more than one active membership → `409 Conflict`, an explicit `/api/simulations/{tenantId}/...` path is required
- no active membership → `live`

### Lifecycle Status and Management Access

The middleware does **not** gate on lifecycle status. `Paused`, `Archiving` and `Archived` tenants stay addressable so archive, report and retention management keep working after a simulation stops running. Version 1 specified `409` for any tenant outside `active`/`paused`; that rule is superseded because it would have blocked the `SIM-ARCHIVE-ASYNC` polling flow and the `SIM-REPORT-MISSING` report reads. Route handlers, not the middleware, enforce per-operation status preconditions.

### Ingestion Pipeline (Special Case)

The ingestion pipeline (`apps/ingestion/`) does not run the tenant middleware. It authenticates with a system managed identity (`DefaultAzureCredential`) and writes under `PipelineConfig.scope`, which defaults to `live`. Simulation signals are produced by the simulation scheduler and seeding services inside the API, never by the live ingestion polling path.

### Error Handling

| Condition | Response |
| --------- | -------- |
| Request has no validated claims | Forwarded without tenant context; the auth layer owns `401` |
| Caller lacks the `SimulationUser` role | `403 Forbidden` (route dependency, not this middleware) |
| Caller is neither `created_by` nor in `participants` | `403 Forbidden` |
| Simulation tenant absent, or its status is `Deleted` | `404 Not Found` |
| Tenant store raises during resolution | `503 Service Unavailable` — fail-closed, never falls back to `live` |
| Multiple active memberships on a non-simulation path | `409 Conflict` |

### Context Propagation

`TenantContext` is propagated through Python `contextvars`. Repositories read the current context to build partition keys, cache-key prefixes and blob paths. Storage calls are offloaded with `app.core.async_io.run_blocking`, which copies the context into the worker thread, so tenant scoping survives the offload boundary.

```python
_tenant_context_var: ContextVar[TenantContext] = ContextVar("tenant_context")


def get_current_tenant() -> TenantContext:
    return _tenant_context_var.get()


def set_current_tenant(ctx: TenantContext) -> Token[TenantContext]:
    return _tenant_context_var.set(ctx)


def reset_current_tenant(token: Token[TenantContext]) -> None:
    _tenant_context_var.reset(token)
```

### Agent Handoff Propagation

When the API creates an `AgentHandoffEvent`, it includes `tenant_id` in the payload. The agents service receives the handoff and sets the tenant context before processing. Agent HTTP calls back to the API include the tenant context via the standard Entra ID token flow.
