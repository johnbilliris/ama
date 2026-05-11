# ADR-036-003: Cosmos DB Session Consistency for Simulation Realm

**Status**: Accepted
**Deciders**: Data Architect, Backend Engineer, SRE
**Date**: 2026-05-08
**Spec**: 036-sim-agent-extend
**FR coverage**: FR-046, FR-048, FR-052, FR-057, FR-060

## Context

The simulation realm performs heavily-concurrent reads and writes
against multiple Cosmos containers — `simulation_threads`,
`simulation_synthetic_signals`, `simulation_audit_logs`,
`simulation_state`, `routing_decisions`, and `exercise_outcome_index`
— with strict invariants:

- **Gap-free `sequence_number` per simulation** (FR-048).
- **Thread cap of 5** active threads per simulation (FR-052), enforced
  via ETag optimistic concurrency.
- **Byte-deterministic cascade affinity ladder** (FR-057) — a replay
  must produce identical fan-out ordering.

Strong consistency for the simulation realm would have crossed cost
and latency thresholds (~3× RU charges, ~50 ms p95 lift); Eventual
consistency would have broken the gap-free sequence invariant under
multi-replica cascades. Bounded-staleness was a contender but ties
us to a global staleness window we cannot fine-tune per workload.

## Decision

Use **Cosmos `Session` consistency** for every simulation-realm
container. The data architect's cohort canvass (`cohort-tech-arch-ai.md
§4.1`) captures the rationale:

- Session consistency guarantees **monotonic read** + **read-own-write**
  + **monotonic writes** *within a session token*. The audit writer
  threads its session token through the optimistic-concurrency retries
  (`AuditWriter._next_sequence_number`) so the gap-free invariant holds
  per replica.
- Cross-replica reads via the change feed are eventually consistent —
  acceptable because `map_overlay_publisher` (T-D11) treats the change
  feed as the *source of truth for visualisation* and emits
  `map.overlay.stale` events when its observed-at timestamp exceeds the
  per-category freshness window (`apps/api/app/config/
  signal_freshness.py`).
- ETag conflicts on `simulation_threads` updates retry 5 times with
  50 ms exponential back-off + jitter (capped at 400 ms) — see
  `thread_cap_service.py`. The retry budget never exceeds the FR-059
  abort budget (1 s).

## Consequences

- **Reads MUST pin the session token** for any operation that follows
  a write within the same controller turn. This is enforced by
  threading the session token through the audit-writer DI wiring; the
  pattern is documented in `tests/integration/test_audit_writer.py`.
- Cross-region replication (AU East primary, AU Central secondary) is
  asynchronous; the disaster-recovery RPO is "best-effort 5 min". The
  spec accepts this because all simulation data is reproducible from
  the audit log.
- `exercise_outcome_index` reads in `lessons_capture.generate()` use
  the same session token so a re-run sees its prior write (FR-055
  idempotency).

## Alternatives considered

- **Strong consistency** — rejected: 3× RU charges; latency lift would
  break the FR-003 (≤ 1 s soft-ack) budget.
- **Bounded-staleness (5 s, 100 K ops)** — rejected: the global window
  cannot be tuned per container; the audit writer's gap-free invariant
  would be fragile under burst workloads.
- **Eventual** — rejected: breaks gap-free `sequence_number`.

## Linked artefacts

- `apps/api/app/services/simulation/audit_writer.py`
- `apps/api/app/services/simulation/thread_cap_service.py`
- `apps/api/app/services/simulation/map_overlay_publisher.py`
- `infra/bicep/modules/cosmos-simulation-containers.bicep`
