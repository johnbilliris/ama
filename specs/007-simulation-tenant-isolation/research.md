# Research: Simulation-as-Tenant

**Feature**: 007-simulation-tenant-isolation | **Date**: 2026-04-09

## R1: Extending TenantContext for Simulation Tenants

**Decision**: Extend the existing `TenantContext` dataclass (in `apps/api/app/core/tenant_context.py`) to include a `tenant_id: str` field that distinguishes `live` from `sim-{scenarioRunId}`.

**Rationale**: The codebase already has a `TenantContext` with `agency_id`, `jurisdiction_ids`, and `persona_id`. Adding `tenant_id` is a minimal extension. The existing `scope_key` property can incorporate `tenant_id` as the outermost prefix, ensuring all downstream partition keys, cache keys, and audit prefixes inherit tenant isolation automatically.

**Alternatives Considered**:
- Separate `SimulationContext` class — rejected because it would require bifurcating every service method signature. A single `TenantContext` with a `tenant_id` field is simpler and ensures the live path uses the same code.
- Ambient thread-local context — rejected because FastAPI uses async/await with `contextvars`; the existing dependency injection pattern (via `rbac.py`) is idiomatic and testable.

## R2: Cosmos DB Partition Strategy for Simulation Isolation

**Decision**: Use the existing multi-hash partition key pattern in `cosmos_scope.py`. The `signals` container already uses `['/scope', '/jurisdictionId', '/dataSourceId']`. The `scope` field will be set to `live` for real signals and `sim-{scenarioRunId}` for simulation signals. The `simulation` container (already provisioned with hash partition on `/scenario_id`) will store `SimulationTenant` and `ScenarioTemplate` documents.

**Rationale**: Cosmos DB enforces partition isolation at the query level — a query scoped to `scope=live` cannot return documents with `scope=sim-xyz`. This is a structural guarantee, not an application-layer convention. The partition key is already on every signal document; no schema migration needed.

**Alternatives Considered**:
- Separate Cosmos DB database per simulation — rejected due to provisioning latency (~minutes vs <30s target) and management overhead.
- Separate container per simulation — rejected; Cosmos DB has a 25-container-per-database soft limit and container creation is slow.

## R3: Redis Namespace Isolation

**Decision**: Prefix all Redis keys with the `tenant_id`. Pattern: `{tenant_id}:{resource_type}:{resource_id}`. For example: `live:dedup:bom-warnings:abc123` vs `sim-run42:dedup:signal:xyz789`. The existing Redis client in the ingestion pipeline uses key prefixes for deduplication; extend this pattern to all cache operations.

**Rationale**: Redis does not have native namespace isolation, but key prefixing is the standard approach. Combined with the `TenantContext` propagation, every cache read/write will include the tenant prefix. The `FLUSHDB` operation is never used; cleanup iterates keys by prefix pattern (`SCAN` with `MATCH`).

**Alternatives Considered**:
- Separate Redis databases (SELECT 0, 1, 2...) — rejected; Azure Cache for Redis Basic SKU supports only 1 database. Would require Standard SKU upgrade for multi-DB.
- Separate Redis instances per simulation — rejected; cost and provisioning time prohibitive.

## R4: Blob Storage Prefix Strategy

**Decision**: Use container/prefix hierarchy for tenant isolation. Pattern:
- `audit/{tenant_id}/...` — audit trail events
- `raw-payloads/{tenant_id}/...` — raw signal payloads (live uses `raw-payloads/live/bom-warnings/...`)
- `simulation/{tenant_id}/...` — simulation-specific artefacts (exercise reports, scenario packs)

The existing `raw-payloads` container already uses path prefixes (`bom-warnings/YYYY/MM/DD/...`). Adding a tenant prefix before the data-source prefix is backward-compatible.

**Rationale**: Azure Blob Storage virtual directories via path prefixes are free, require no provisioning, and deletion is a single `delete_blobs` call with prefix filter. The `simulation` container already exists in Bicep.

**Alternatives Considered**:
- Separate storage account per simulation — rejected; overkill, slow provisioning, RBAC duplication.
- Separate containers per simulation — rejected; container creation requires management-plane calls, slower than 30s target.

## R5: Entra ID Integration and Participant Membership

**Decision**: Use a single Entra ID app role (`SimulationUser`) to gate access to simulation features. Per-simulation membership is stored in the `SimulationTenant.participants` list in Cosmos DB. The API middleware:
1. Validates the Entra ID token (authn)
2. Checks for `SimulationUser` role (base authz)
3. Looks up the user's `oid` in the requested simulation's participant list (tenant authz)
4. Sets `TenantContext.tenant_id` accordingly

**Rationale**: Simulations are short-lived (hours to days). Creating/deleting Entra ID groups for each simulation would introduce management-plane latency and Graph API dependencies. The internal participant list is immediate (Cosmos DB point-read) and cleaned up automatically when the simulation is archived.

**Alternatives Considered**:
- Dynamic Entra ID security groups — rejected; Graph API calls for group creation take seconds, group membership propagation can take minutes, and cleanup is error-prone.
- Entra ID app roles per simulation — rejected; app role changes require app registration updates, which are slow and have a maximum role limit.

## R6: Auto-Throttle Mechanism for Live Priority

**Decision**: Implement a `ResourceGovernor` service that monitors shared resource utilisation (Cosmos DB RU consumption, Redis memory, LLM token usage). When utilisation exceeds the configurable threshold (default: 70%), simulation writes are rate-limited via a token bucket. When a live incident is declared, simulations are throttled to 20% of shared throughput via an explicit throttle mode.

**Rationale**: Token bucket rate limiting is well-understood, stateless per-request, and allows simulation operations to continue (slowly) rather than failing. The 70% threshold for organic throttling and 20% cap during live incidents provides two distinct protection levels.

**Alternatives Considered**:
- Cosmos DB Request Rate Too Large (429) retry — rejected as the only mechanism; 429s indicate the live tenant is already impacted. Proactive throttling prevents 429s.
- Queue-based backpressure — rejected for initial implementation; adds infrastructure complexity (Event Hubs / Service Bus). Can be added later if needed.

## R7: Agent Chain Tenant Propagation

**Decision**: Extend `AgentHandoffEvent` (in `apps/agents/common/handoffs.py`) to include `tenant_id`. When the monitoring agent builds a handoff, it inherits `tenant_id` from the signal's scope. Downstream agents receive the tenant context in the handoff payload and propagate it to all state writes. The API endpoints called by agents will enforce tenant context via the standard middleware.

**Rationale**: Agents already communicate via HTTP calls to the API. The API middleware will enforce tenant context on these calls. Adding `tenant_id` to the handoff payload is a single-field extension. The agent chain processes simulation signals identically to live signals — the tenant context is the only discriminator.

**Alternatives Considered**:
- Separate agent instances per simulation — rejected; would require N×5 Container App replicas, defeating the shared-compute model.
- Agent-level tenant filtering — rejected; agents should be tenant-unaware. Isolation is enforced at the storage layer, not the business logic layer.

## R8: Alert Publication Safety Gate

**Decision**: Add a `TenantAwareAlertGate` check in the alert publication service. Before any alert is delivered to a real channel (SMS, broadcast, social media), the gate checks `TenantContext.tenant_id`. If the tenant is not `live`, the alert is recorded as `published (simulation)` in the simulation audit trail and delivery is blocked. This is a hard gate, not a feature flag.

**Rationale**: This is a life-safety requirement (Constitution I). The gate must be structural — a single `if tenant_id != "live": block_delivery()` check — not configurable or bypassable. The check is at the publication service layer, which is the last point before external delivery.

**Alternatives Considered**:
- Channel-level filtering — rejected; would require every delivery channel (SMS gateway, broadcast API, social media API) to understand tenant context. Centralising the gate is safer.
- Feature flag — rejected; a flag can be misconfigured. A code-level gate with no bypass mechanism is appropriate for a safety-critical check.

## R9: Frontend Simulation Dashboard Approach

**Decision**: The simulation dashboard reuses all existing dashboard components. The URL pattern is `/simulations/{tenantId}` which sets a client-side context that is included in all API calls. The persistent SIMULATION banner is a fixed-position component rendered when the route starts with `/simulations/`. The live dashboard at `/incidents` has no simulation-related UI elements.

**Rationale**: Reusing dashboard components ensures simulation fidelity (FR-020) and reduces development effort. Route-based separation (not a toggle) ensures live operators never accidentally see simulation data.

**Alternatives Considered**:
- Simulation toggle on the live dashboard — rejected per FR-022; live dashboard must not contain simulation UI elements.
- Separate deployed frontend for simulation — rejected; doubles deployment complexity for identical UI.

## R10: Exercise Report Generation

**Decision**: The `ExerciseReportService` queries the simulation tenant's Cosmos DB partition for all signals, recommendations, approvals, alerts, and timeline events. It aggregates metrics (time-to-first-recommendation, time-to-alert-publication, coordination coverage) and compares against benchmark targets stored in the `ScenarioTemplate`. The report is rendered as a JSON document stored in the `simulation` blob container and viewable via the web frontend.

**Rationale**: All exercise data is tenant-scoped in Cosmos DB, making aggregation queries straightforward (partition-scoped cross-partition queries are not needed). Benchmark targets are part of the scenario template, making comparison deterministic.

**Alternatives Considered**:
- Real-time metrics via Application Insights queries — rejected as the primary mechanism; App Insights has 5-10 minute ingestion delay and KQL queries are complex. Direct Cosmos DB aggregation is faster and more reliable for post-exercise reports.
