# ADR-036-005: ETag Optimistic Concurrency for Cascade Thread-Cap Enforcement

**Status**: Accepted
**Deciders**: Data Architect, Backend Engineer
**Date**: 2026-05-08
**Spec**: 036-sim-agent-extend
**FR coverage**: FR-052, FR-057
**Constitution**: Audit-and-Provenance

## Context

The simulation realm enforces a hard cap of **5 active hazard threads**
per simulation (FR-052 / Assumption A10). Cascade fan-outs (FR-057) can
race when multiple synthetic signals trigger thread proposals
concurrently. The cap MUST be:

- **Atomically respected** — never exceed 5, even under 50-way
  contention.
- **Affinity-aware** — when the cap is reached, the cascade
  orchestrator MUST consult the deterministic 5-step affinity ladder
  (`cascade_affinity_ladder.py`) and degrade the new proposal to an
  annotation on the most-related existing thread.

A pessimistic lock against `simulation_threads/{simulationId}` would
serialise every cascade and cripple p95 latency.

## Decision

Use **Cosmos ETag optimistic concurrency** for all `simulation_threads`
mutations. The pattern:

1. Read `simulation_threads/{simulationId}` with its `_etag`.
2. Compute the new `active_threads` set in memory (add or remove).
3. Issue `replace_item` with `if_match=_etag`.
4. On `412 Precondition Failed`, retry up to **5 times** with **50 ms
   exponential back-off + 50 % jitter**, capped at **400 ms** total.
5. After exhaustion, raise the conflict — the orchestrator falls back
   to "no slot available" and routes the cascade to the affinity
   ladder.

The retry budget is bounded by the FR-059 abort budget (1 s) so a
stalled mutation never holds an abort.

The cap value is mirrored in three places (intentionally — change-
detection):

- `apps/api/app/services/simulation/thread_cap_service.py:THREAD_CAP = 5`
- `data-model.md` `simulation_threads.active_threads.maxItems = 5`
- `audit-envelope.md §3.10` `current_thread_count.const = 5`

A schema test verifies the three values stay byte-equal.

## Consequences

- The hypothesis property test
  (`tests/integration/test_thread_cap_service.py::
  test_concurrent_adds_never_exceed_cap`) drives 50 concurrent
  attempts; the in-memory fallback (`asyncio.Lock`) preserves the
  invariant for unit testing.
- Cosmos RU consumption per cascade fan-out: 1 read + 1 conditional
  replace + (≤4 retries on contention) ≤ 25 RU p95.
- The ladder result (`affinity_step` 1–5) is recorded on the
  `cascade.degraded_to_annotation` audit envelope so replays can
  reconstruct the ladder choice.

## Alternatives considered

- **Cosmos stored procedure** — rejected: Cosmos JS engine adds 50–
  100 ms latency, doesn't compose with the AI-controller's
  `asyncio.Task` model, and the procedure code lives outside the Python
  type system (no Pydantic validation).
- **Pessimistic Redis lock** — rejected: introduces a dependency
  outside the simulation realm and is itself a SPOF.
- **Eventual-consistency `IncrementCounter`** — rejected: would let the
  cap exceed 5 transiently.

## Linked artefacts

- `apps/api/app/services/simulation/thread_cap_service.py`
- `apps/api/app/services/simulation/cascade_affinity_ladder.py`
- `apps/api/app/services/simulation/cascade_orchestrator.py`
- `infra/bicep/modules/cosmos-simulation-containers.bicep`
