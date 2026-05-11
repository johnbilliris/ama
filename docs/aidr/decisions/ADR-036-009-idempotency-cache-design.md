# ADR-036-009: Idempotency-Cache Design (Cosmos + RFC 8785 Body Hashing)

**Status**: Accepted
**Deciders**: API Architect, Solution Architect, Security Engineer, Compliance Auditor
**Date**: 2026-05-08
**Spec**: 036-sim-agent-extend
**FR coverage**: FR-066 (Step 8 Amendment S), FR-051 (RBAC ordering), FR-048 (interaction with sequence allocator fail-closed)
**Constitution**: I (Primacy of Life — replay safety), IV (Transparency and Auditability)
**Related ADRs**: ADR-036-007 (503 caching of sequence-uncertainty), ADR-036-002 (direct REST lifecycle endpoints)

## Context

Step 8 Amendment S added FR-066 to require **direct REST lifecycle
endpoints** (`pause`, `resume`, `abort`, `inject-telemetry`) to honour
the `Idempotency-Key` HTTP header and return the **original cached
response without re-executing side effects** for replays within a
24-hour window. Step 8 amendment pass 1 Q3 + amendment pass 2 Q7
further specified:

- Uniqueness scope is the tuple `(simulation_id, verb, route)` — same
  key on different verbs is a different namespace and both succeed
  independently.
- Body-hash conflict detection: same key + same verb + same `sim_id`
  + DIFFERENT canonical-body sha256 ⇒ HTTP 422 with RFC 9457
  `type: "idempotency-key-conflict"`.
- 503 caching: ADR-036-007's sequence-uncertainty fail-closed responses
  MUST be cached for the full 24 h replay window so that retried
  requests do not double-attempt the underlying Cosmos operation.
- State-machine consumption: `pause→resume→pause` round-trip with
  the same key on the second pause MUST be refused with HTTP 409
  RFC-9457 `lifecycle-state-conflict`.
- RBAC ordering (per Step 8 amendment pass 1 strengthening of
  FR-051): JWT/role/tenant validation precedes idempotency-cache
  consultation; an idempotent replay does NOT bypass RBAC.

## Decision

Implement the FR-066 idempotency cache on **Cosmos DB** with **RFC 8785
JSON Canonicalisation Scheme (JCS)** body hashing.

### Container layout

- **Container**: `simulation_idempotency_cache` (NEW Cosmos
  container).
- **Partition key**: `/simulation_id` (ensures all entries for one
  simulation co-locate; cleanup-on-end is a single partition scan).
- **Document id**: composite — `{sim_id}/{verb}/{route}/{idempotency_key}`.
- **Consistency**: Session (so the same writer that just inserted the
  cache entry observes it on the immediate replay).
- **TTL**: **86400 seconds (24 hours)** anchored on `created_at`
  (not on `expires_at`) — this is the Cosmos native TTL field;
  Cosmos increments expiry from the document's `_ts`.
- **RU/s**: autoscale 400–4000 (read-mostly; expected ratio
  ~95 % reads / 5 % writes at MVP load).

### Document schema

```json
{
  "id": "{sim_id}/{verb}/{route}/{idempotency_key}",
  "_partitionKey": "{simulation_id}",
  "sim_id": "uuid",
  "idempotency_key": "string (client-supplied)",
  "verb": "POST",
  "route": "/api/simulations/{simId}/pause",
  "body_hash": "sha256-hex (over RFC-8785-canonicalised request body)",
  "response_status": 200,
  "response_body": { "...": "..." },
  "response_headers_subset": {
    "content-type": "application/json",
    "x-idempotency-replay": "false"
  },
  "request_correlation_id": "uuid",
  "rbac_subject_id": "Entra OID — used to detect cross-user replay attempts",
  "created_at": "2026-05-08T10:23:14Z",
  "ttl": 86400
}
```

### Algorithm

Pseudocode for FR-066 enforcement at every direct-REST lifecycle
endpoint:

```python
async def enforce_idempotency(
    sim_id: UUID, verb: str, route: str,
    idempotency_key: str | None,
    request_body: dict,
    rbac_subject_id: str,
) -> CacheLookupResult:
    if idempotency_key is None:
        return CacheLookupResult(MISS, None)

    # 1. RBAC has already passed (precedes this call) — FR-051 ordering
    body_hash = canonical_sha256(request_body)  # RFC 8785 JCS
    doc_id = f"{sim_id}/{verb}/{route}/{idempotency_key}"
    cached = await cache_repo.read(doc_id, partition=sim_id)

    if cached is None:
        return CacheLookupResult(MISS, body_hash)

    # 2. Body-hash conflict → HTTP 422 RFC-9457 `idempotency-key-conflict`
    if cached.body_hash != body_hash:
        return CacheLookupResult(BODY_CONFLICT, body_hash, cached)

    # 3. State-machine consumption (lifecycle verbs only) — RFC-9457
    #    `lifecycle-state-conflict`. See ADR appendix below.
    if verb in {"POST"} and route in PAUSE_RESUME_ABORT_ROUTES:
        if not is_state_consistent_with_cached(sim_id, cached):
            return CacheLookupResult(STATE_CONFLICT, body_hash, cached)

    # 4. RBAC subject mismatch is a SEV-2 audit-only event but the replay
    #    proceeds (the original response already reflected the side effects)
    if cached.rbac_subject_id != rbac_subject_id:
        await audit_writer.write(IdempotencyReplayCrossUser(...))

    return CacheLookupResult(HIT, body_hash, cached)


async def write_cache_on_response(...):
    # Write AFTER the side effect commits, before returning to client.
    # 503 fail-closed responses (ADR-036-007) are cached EXACTLY ONCE per
    # original request so that replays return the cached 503 without
    # re-attempting the Cosmos operation.
    ...
```

### Body-hash canonicalisation: RFC 8785 (JCS)

Body hashing uses **RFC 8785 JSON Canonicalisation Scheme (JCS)** to
produce a deterministic byte-stream regardless of input
serialisation. JCS is a published IETF standard, has reference
implementations in multiple languages, and is the same canonicaliser
used by JWS + JOSE specs. Implementation choice:

- **Library**: `canonicaljson` (PyPI) — pure-Python, RFC 8785
  conformance test suite passes.
- **Test vectors**: `tests/contract/test_rfc8785_canonical_json.py`
  (NEW) verifies all RFC 8785 § 3.2 test vectors — empty object,
  trailing zeros in numbers, nested arrays, unicode escapes.
- **Fallback**: Python stdlib
  `json.dumps(obj, sort_keys=True, separators=(",", ":"),
  ensure_ascii=False)` is NOT RFC-8785-conformant for floating-point
  numbers and is REJECTED for FR-066 use; reuse the same decision
  for the FR-060 `prompt_hash` canonicalisation.

### Lifecycle state-machine consumption

The 4 routes participate in this state machine:

| Cached verb | Sim state at replay | Action |
|---|---|---|
| `pause` | paused | replay cached 200 (idempotent re-pause) |
| `pause` | active (was resumed) | **HTTP 409** `lifecycle-state-conflict` |
| `pause` | ended | **HTTP 409** `lifecycle-state-conflict` |
| `resume` | active | replay cached 200 |
| `resume` | paused | **HTTP 409** `lifecycle-state-conflict` (already resumed once and re-paused) |
| `abort` | ended | replay cached 200 |
| `abort` | active or paused | **HTTP 409** `lifecycle-state-conflict` (cached abort exists but state was rolled forward — should be impossible; SEV-2 alert) |
| `inject-telemetry` | active | replay cached response (200 or 4xx) |
| `inject-telemetry` | paused | **HTTP 409** `audit.lifecycle.refused_while_paused` (refusal NOT cached per pass 2 Q7) |
| `inject-telemetry` | ended | replay cached response (immutable history) |

### TTL anchoring

- TTL = 86400 s = 24 h, anchored on Cosmos `_ts` (set at insert).
- Cosmos increments `_ts` only on writes; replay reads do NOT
  extend the TTL.
- After 24 h the entry is auto-evicted; a subsequent request with
  the same key + body is treated as a fresh request (idempotency is
  not infinite — the spec allows the cache window to be 24 h).

## Alternatives considered

- **Redis** (`SETEX` + Lua-scripted body-hash compare): rejected
  because a separate replication-failover model and a second source
  of truth (Redis ↔ Cosmos divergence on partition events). Cosmos
  is already the audit/data-plane store.
- **In-process LRU**: rejected — does not survive across multiple
  `apps/api` Container App replicas; would re-introduce the FR-048
  multi-replica failure mode.
- **HTTP caching headers (`Cache-Control: max-age`) at APIM**: too
  coarse; cannot do body-hash conflict detection.
- **Hash via `stable_json` (Python stable-encoder)**: rejected because
  `stable_json` does not conform to RFC 8785 number canonicalisation
  (NaN/Infinity handling, trailing-zero removal).
- **Per-`sim_id` namespace (no verb/route subdivision)**: rejected
  per pass 1 Q3 — would cause `pause` and `abort` with the same
  client-supplied key to collide.

## Consequences

**Positive**:

- Single source of truth (Cosmos) for replay receipts.
- TTL handled by Cosmos native field — no cleanup worker needed.
- RFC-8785 hashing is interoperable with non-Python consumers (e.g.
  audit-export clients verifying replay integrity).
- 503 caching from ADR-036-007 has a designated home.

**Negative**:

- ~AU$15/month additional Cosmos cost (autoscale 400–4000).
- Body-hash compute on every lifecycle write (~0.1 ms per request).
- One additional Cosmos round-trip per lifecycle write (cache read +
  side effect + cache write).

**Test obligations**:

- Contract: `tests/contract/test_rfc8785_canonical_json.py` (test
  vectors).
- Contract: `tests/contract/test_idempotency_cache_conflict.py`
  (422 on body-hash mismatch).
- Integration: `tests/integration/test_idempotency_round_trip.py`
  (`pause→resume→pause` returns 409 `lifecycle-state-conflict`).
- Integration: `tests/integration/test_idempotency_503_cache.py`
  (the ADR-036-007 503 is cached and replayed without
  re-attempting).
- Integration: `tests/integration/test_idempotency_rbac_ordering.py`
  (RBAC denial precedes cache read).

## References

- Spec FR-066 (Step 8 Amendment S), FR-051, FR-048
- Step 8 cross-cohort synthesis: `step8-synthesis.md` § "Amendment S"
- Step 8 amendment pass 1 Q2/Q3, amendment pass 2 Q7
- ADR-036-007 (503 caching)
- ADR-036-002 (direct REST lifecycle)
- RFC 8785 — JSON Canonicalisation Scheme (JCS): <https://www.rfc-editor.org/rfc/rfc8785>
- RFC 9457 — Problem Details for HTTP APIs: <https://www.rfc-editor.org/rfc/rfc9457>
