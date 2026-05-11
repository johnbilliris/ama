# ADR-036-007: Distributed Gap-Free Audit Sequence Allocator

**Status**: Accepted
**Deciders**: Solution Architect, Data Engineer, Compliance Auditor, Principal Engineer
**Date**: 2026-05-08
**Spec**: 036-sim-agent-extend
**FR coverage**: FR-048 (Step 8 Amendment D), FR-066 (idempotency cache anchoring of fail-closed responses)
**Constitution**: IV (Transparency and Auditability), I (Primacy of Life — fail-closed)
**Supersedes**: nothing (extends ADR-036-005 ETag-pattern reuse to a different per-sim counter document)

## Context

The audit pipeline (`apps/api/app/services/simulation/audit_writer.py`)
allocates `sequence_number` from a **process-local** Python dict
(`_sequence_counters: dict[str, int] = {}` at module scope) — verified
in the Step 8 cross-cohort review at lines 44–47 and 75–81. With more
than one `apps/api` Container App replica handling traffic for the
same simulation, two replicas can independently allocate the same
`sequence_number`, producing **duplicates and gaps** that violate
FR-048's append-only, gap-free invariant and corrupt the FR-049
machine-export and FR-054 lessons-capture single-walk reconstruction.

The Step 8 Amendment D restated FR-048 as REQUIRING that the
allocator be **safe across multiple API replicas** with an explicit
choice between (A) Cosmos ETag conditional replace, (B) Cosmos
stored procedure, or (C) documented single-writer constraint with
replica-affinity routing. The `apps/api` Container App is configured
with `minReplicas: 1, maxReplicas: 3` (per `infra/bicep/modules/container-apps-scaling.bicep`),
so the production posture is multi-replica.

## Decision

Adopt **Option (A)** — **Cosmos ETag conditional replace on a
per-simulation sequence-counter document** — for the FR-048 audit
sequence allocator. Reuses the proven pattern from ADR-036-005
(`simulation_threads`/cap enforcement) so the team has one allocator
shape to operate.

**Counter document**:

- **Container**: `simulation_audit_sequence_counters` (NEW Cosmos
  container).
- **Partition key**: `/simulation_id`.
- **Document id**: `simulation_audit_sequence_counter/{simulation_id}`.
- **Consistency**: account-default (Consistent-Prefix is sufficient
  because the ETag conditional replace is the atomic guarantee, not
  the read consistency).
- **TTL**: none (counter persists for the full simulation lifetime;
  cleanup at FR-054 lessons-capture archive time).
- **RU/s**: fixed 400 (one document per sim, replace-only access
  pattern).
- **Schema**:

```json
{
  "id": "simulation_audit_sequence_counter/{simulation_id}",
  "_partitionKey": "{simulation_id}",
  "simulation_id": "uuid",
  "current_sequence": 42,
  "last_writer_replica_id": "ca-api-rev-12345-replica-2",
  "updated_at": "2026-05-08T10:23:14Z",
  "_etag": "<server-managed>"
}
```

**Allocation algorithm** (replaces `audit_writer.py:_sequence_counters`):

```python
async def allocate_sequence_number(sim_id: UUID) -> int:
    for attempt in range(5):
        doc, etag = await counter_repo.read_with_etag(sim_id)
        proposed = doc.current_sequence + 1
        try:
            await counter_repo.replace_item(
                doc_id=f"simulation_audit_sequence_counter/{sim_id}",
                doc={**doc.dict(),
                     "current_sequence": proposed,
                     "last_writer_replica_id": REPLICA_ID,
                     "updated_at": utcnow()},
                if_match=etag,
            )
            return proposed
        except CosmosAccessConditionFailedError:
            await asyncio.sleep(0.05 * (2 ** attempt) + jitter())
    raise SequenceAllocatorExhausted(sim_id)
```

**Retry budget**: 5 attempts × 50 ms exponential back-off + jitter
(matches ADR-036-005). Worst-case ≈ 1.55 s; bounded so it does NOT
exceed FR-009's 5 s parse-to-pipeline budget.

**Fail-closed protocol** (per Step 8 Amendment Pass 1 Q2):

1. On `SequenceAllocatorExhausted`, the originating endpoint returns
   **HTTP 503 Service Unavailable** with `Retry-After: 5`.
2. A best-effort entry of type `audit.sequence.uncertainty` is
   written to the **fail-safe dead-letter queue** (Cosmos
   `simulation_audit_dlq` container, partition by `simulation_id`),
   with `sequence_number = -1` and an `uncertainty_reason` enum
   drawn from `{etag_exhausted, counter_unreachable, replica_partition}`.
3. The 503 response is cached in the FR-066 idempotency-cache for
   the full 24 h replay window so retried requests do not double-attempt.
4. Downstream readers (FR-054 lessons-capture, FR-049 audit export)
   detect `sequence_number = -1` and surface them as
   **evidence-integrity warnings** (RFC 9457 problem detail
   `type: "evidence-integrity-warning"`).

## Alternatives considered

- **(B) Cosmos stored procedure**: atomic increment in JavaScript
  server-side. Rejected because (1) Cosmos JS sprocs are an
  operational liability (no Python typing, no pytest coverage in
  current toolchain, deploy is out-of-band from app deploy), (2)
  ETag pattern is already proven in ADR-036-005, (3) sproc max
  execution time of 5 s would not be exceeded but adds a separate
  failure mode (sproc timeout vs. ETag conflict).
- **(C) Single-writer with replica-affinity routing**: would require
  Container Apps revision pinning on one replica per simulation,
  which conflicts with KEDA HTTP scaler's even-distribution
  semantics. Rejected.
- **Azure Service Bus session-enabled queue**: adds a queue
  round-trip on every audit write, eroding the FR-009 5 s budget.
  Rejected.
- **Snowflake**-style monotonic ID (timestamp + replica_id +
  sequence): not gap-free across replicas because clock skew and
  replica reassignment break monotonicity guarantees. Rejected.

## Consequences

**Positive**:

- Gap-free `sequence_number` across N replicas with bounded retry
  budget.
- Reuses ADR-036-005 ETag pattern → one allocator concept to
  operate.
- Cosmos-native; no new infrastructure.
- Fail-closed protocol compliant with Constitution I (no silent
  gaps).

**Negative / costs**:

- One additional Cosmos round-trip per audit write (read counter +
  conditional replace) — adds ~5 ms to audit write path.
- Extra ~AU$5/month for the new fixed-400 RU/s container.
- Operational care: the dead-letter queue MUST be monitored; an
  alert fires at ≥ 1 entry per hour per sim.

**Test obligations**:

- Property-based test (`tests/contract/test_audit_sequence_etag_concurrency.py`)
  asserting that 50 concurrent allocations produce 50 distinct
  sequence numbers in `[1..50]` with no gaps.
- Integration test (`tests/integration/test_audit_sequence_dlq.py`)
  asserting that ETag exhaustion writes a DLQ entry with
  `sequence_number = -1` and the originating endpoint returns 503.
- Load test extension (`tests/load/simulation_injection_load.py`)
  measuring P95 audit-write latency under 200 concurrent injections
  (target: P95 ≤ 80 ms including allocator round-trip).

**Operational**:

- New runbook entry: `docs/disaster-response-hub/audit-sequence-dlq-runbook.md`
  (out-of-scope for this ADR but added to the tasks list for the
  amendment cycle).

## References

- Spec FR-048 (Step 8 Amendment D), FR-049, FR-066
- ADR-036-005 (sibling ETag pattern for `simulation_threads`)
- Step 8 cross-cohort synthesis: `step8-synthesis.md` § C2
  ("Audit `sequence_number` not gap-free across replicas")
- Step 8 amendment pass 1 Q2 (fail-closed user-facing protocol)
- Cosmos DB optimistic concurrency: <https://learn.microsoft.com/azure/cosmos-db/nosql/database-transactions-optimistic-concurrency>
