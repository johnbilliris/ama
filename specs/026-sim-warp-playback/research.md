# Research: Simulation Time Warp & Playback

**Feature**: `026-sim-warp-playback`  
**Date**: 2026-04-22

## R1: Signal Scheduling Mechanism for Warp Speed

**Decision**: Durable cursor + canonical server clock with a dedicated worker process.

**Rationale**: The existing `replay_realtime()` uses sequential `asyncio.sleep(offset/time_multiplier)` in the API process. This approach fails under warp because: (a) an in-process asyncio task is lost on restart/redeploy, (b) multi-instance deployments would double-deliver signals, and (c) recalculating all pending entries on every speed change is O(n) and error-prone. A durable cursor model stores the next-signal index and canonical clock state, computing only the next delivery delay on each tick. A dedicated worker (or durable background task) owns signal delivery for a given tenant.

**Alternatives considered**:
- In-process asyncio priority queue: simple but not durable, lost on restart, no multi-instance safety.
- External job queue (Celery/Azure Functions timer): overkill for per-tenant signal delivery; adds infrastructure complexity.
- Pre-compute all real-time offsets on start: breaks on speed change; requires full recalculation.

## R2: Simulated Time Ownership — Server vs Client

**Decision**: Server owns canonical simulated time. Client displays it but does not compute it.

**Rationale**: The current architecture has the browser own `elapsed_seconds` and POST it back on pause/resume/archive. This creates drift/race risk even at 1×; at warp speed with mid-run changes, it becomes untenable. Multiple browser tabs, network delays, or a client crash would corrupt the authoritative time. The server must persist: `accumulated_sim_seconds`, `last_resumed_at`, `current_warp_speed`, and `clock_paused` flag. The computed current simulated time is: `accumulated_sim_seconds + (now - last_resumed_at).seconds × current_warp_speed` (when running).

**Alternatives considered**:
- Keep UI-owned time: breaks with warp speed changes, multi-tab, network delays.
- Hybrid (server validates UI-submitted time): adds complexity without solving the root cause.

## R3: Event Recording Strategy for Playback

**Decision**: Append-first recording of coarse decision-significant events to a dedicated Cosmos container, with monotonic per-tenant sequence numbers.

**Rationale**: The existing audit writer (blob storage, one file per event) is optimised for compliance logging, not ordered retrieval. Playback requires efficient ordered reads by tenant. A dedicated Cosmos container `sim-events` partitioned by `tenant_id` allows efficient range queries. Events are recorded at coarse granularity (completed chat turns, signal deliveries, state changes — not SSE token deltas) to keep volume manageable. A monotonic `event_seq` per tenant ensures deterministic ordering even when multiple events share the same simulated time offset. Recording uses write-boundary interception (wrapping `create_signal`, chat append, state-change service) rather than sprinkling recorder calls across every feature service.

**Alternatives considered**:
- Extend existing blob audit writer: poor for ordered reads, expensive to query by range.
- Record raw SSE chat deltas: explodes event volume, makes scrub expensive.
- Event Grid / Service Bus: adds infrastructure; unnecessary for append-only per-tenant writes.

## R4: Playback Architecture — Client-Side vs Server-Side

**Decision**: Client-side playback with server-provided paginated events and periodic snapshots.

**Rationale**: For typical simulations (hundreds to low thousands of coarse events), loading events into the browser is responsive and eliminates server-side SSE complexity. For longer simulations, the server provides periodic state snapshots (every N events or every M simulated minutes). The client loads the nearest snapshot before the scrub target, then applies remaining events forward. The API uses cursor-based pagination for initial load.

**Alternatives considered**:
- Full server-side playback via SSE: adds server load, complex session state, latency on scrub.
- Unbounded single GET for all events: degrades on long simulations.

## R5: Clock State Ownership — Tenant vs Run

**Decision**: Canonical clock state lives on SimulationTenant (tenant-scoped).

**Rationale**: The existing API routes, dashboard, and frontend are all tenant-scoped. `elapsed_seconds` is already on `SimulationTenant`. `time_compression_ratio` on `SimulationRun` is stored but barely used. Consolidating clock state on the tenant avoids fragmented ownership. The `SimulationRun` retains `time_compression_ratio` as the initial/default value; the tenant's `current_warp_speed` is the runtime authoritative source.

**Alternatives considered**:
- Run-scoped clock: requires changing all API routes and frontend to reference run ID; higher migration cost.
- Separate clock entity: over-engineered for current scope.

## R6: Throttle Behaviour Under Backpressure

**Decision**: Preserve order, accept delayed delivery, surface backlog status to controller. Warn when delivery lag exceeds 10 seconds (configurable).

**Rationale**: Throttling must not reorder or drop signals, as scenario fidelity depends on correct sequencing. When signal density exceeds the configurable burst rate (default 100 signals/sec), the scheduler queues excess signals and delivers them in order as capacity allows. A `delivery_lag` metric (difference between intended and actual delivery time) is exposed to the controller. If lag exceeds 10 seconds of wall-clock time (configurable per deployment), a warning is displayed. This preserves scenario correctness while giving controllers visibility into fidelity.

**Alternatives considered**:
- Drop non-critical signals: breaks scenario completeness.
- Batch/coalesce signals: loses individual signal identity.
- Stretch sim time under backpressure: changes scenario timing semantics.

## R7: Playback Access and Annotation Storage

**Decision**: Annotations stored in the same `sim-events` container as playback events, with `event_type = "annotation"`.

**Rationale**: Annotations are logically events in the simulation timeline (anchored to a simulated time offset). Storing them alongside playback events simplifies the query model — a single ordered query returns both recorded events and annotations. Author-only edit/delete is enforced server-side by comparing the requesting user's OID against the annotation's `author_id`. The `event_seq` for annotations is assigned at creation time from the same shared monotonic counter, interleaving naturally with other events in the timeline ordering.

**Alternatives considered**:
- Separate `sim-annotations` container: adds a second query per playback load; more complex.
- Embed annotations in simulation tenant document: doesn't scale, concurrent edit issues.
