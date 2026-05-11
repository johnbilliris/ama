# Contract: Idempotency-Cache Wire Shape and Conflict Detection

**Feature**: 036 — Simulation Telemetry-Injection Agent (amendment cycle)
**Spec FRs**: FR-066 (Step 8 Amendment S), FR-051 (Amendment E — RBAC ordering), FR-048 (Amendment D — 503 caching from sequence uncertainty)
**Constitution**: I (Primacy of Life — replay safety), IV (Transparency and Auditability)
**Authoring ADR**: ADR-036-009 (idempotency-cache design); related: ADR-036-007 (503 caching), ADR-036-002 (direct REST lifecycle)
**Cosmos container**: `simulation_idempotency_cache` (NEW; partition `/simulation_id`; TTL 86 400 s anchored on `_ts`; Session consistency; autoscale 400–4000 RU/s)

This contract pins the wire shape, conflict-detection algorithm, and TTL semantics for the FR-066 idempotency cache. It is the binding contract between (a) the four direct-REST lifecycle endpoints (`pause`, `resume`, `abort`, `inject-telemetry`), (b) the Cosmos cache container, and (c) clients that send the `Idempotency-Key` HTTP header.

---

## 1. Wire shape

### 1.1 Request header

```
POST /api/simulations/{simId}/pause HTTP/1.1
Authorization: Bearer <Entra JWT>
Content-Type: application/json
Idempotency-Key: example-idempotency-token

{ "reason": "Coordinator pause for cohort review" }
```

**`Idempotency-Key` header rules**:

- **Length**: 1 ≤ len ≤ 256 bytes; UTF-8.
- **Charset**: clients SHOULD use UUIDv4 (RFC 4122) for collision avoidance; the server treats the value as opaque.
- **Optionality**: the header is **OPTIONAL** on every endpoint. If absent, no replay protection is applied; if present, FR-066 enforcement applies.
- **Scope**: `(sim_id, verb, route, idempotency_key)` is the unique tuple. Cross-verb collisions are NOT possible (per pass 1 Q3).

### 1.2 Cache document

```json
{
  "id": "{sim_id}/{verb}/{route}/{idempotency_key}",
  "_partitionKey": "{simulation_id}",
  "sim_id": "uuid",
  "idempotency_key": "string (1..256 chars; client-supplied)",
  "verb": "POST",
  "route": "/api/simulations/{simId}/pause",
  "body_hash": "sha256-hex (64 chars)",
  "response_status": 200,
  "response_body": { "...": "..." },
  "response_headers_subset": {
    "content-type": "application/json",
    "x-idempotency-replay": "false",
    "x-replica-id": "ca-api-rev-12345-replica-2"
  },
  "request_correlation_id": "uuid",
  "rbac_subject_id": "Entra OID",
  "created_at": "2026-05-08T10:23:14Z",
  "ttl": 86400,
  "_ts": 1747823014,
  "_etag": "<server-managed>"
}
```

**`response_headers_subset` whitelist** (NEVER cached): `Authorization`, `Cookie`, `Set-Cookie`, `WWW-Authenticate`, `Server`, `Date`. The whitelist is the closed set `{content-type, x-idempotency-replay, x-replica-id, retry-after}`.

### 1.3 Replay response headers

A cached replay response sets:

```
HTTP/1.1 200 OK
Content-Type: application/json
X-Idempotency-Replay: true
X-Replay-Original-Created-At: 2026-05-08T10:23:14Z
```

Fresh requests (cache miss + side-effect commit) set `X-Idempotency-Replay: false`.

---

## 2. Conflict-detection algorithm

```python
async def enforce_idempotency(
    sim_id: UUID, verb: str, route: str,
    idempotency_key: str | None,
    request_body: dict,
    rbac_subject_id: str,
    sim_state: SimulationState,
) -> CacheLookupResult:
    if idempotency_key is None:
        return CacheLookupResult(MISS, None)

    # FR-051 ordering: RBAC has already passed before this call.
    body_hash = canonical_sha256(request_body)  # RFC 8785 JCS
    doc_id = f"{sim_id}/{verb}/{route}/{idempotency_key}"
    cached = await cache_repo.read(doc_id, partition=sim_id)

    if cached is None:
        return CacheLookupResult(MISS, body_hash)

    # Body-hash conflict → HTTP 422 RFC-9457 `idempotency-key-conflict`
    if cached.body_hash != body_hash:
        return CacheLookupResult(BODY_CONFLICT, body_hash, cached)

    # Lifecycle state-machine consumption (per pass 2 Q7) → HTTP 409
    # RFC-9457 `lifecycle-state-conflict`. See §3 below.
    if route in PAUSE_RESUME_ABORT_ROUTES:
        if not is_state_consistent_with_cached(sim_state, cached):
            return CacheLookupResult(STATE_CONFLICT, body_hash, cached)

    # RBAC subject mismatch is SEV-2 audit-only event but the replay proceeds
    # (the original response already reflected the side effects).
    if cached.rbac_subject_id != rbac_subject_id:
        await audit_writer.write(IdempotencyReplayCrossUser(
            cached_subject=cached.rbac_subject_id,
            replay_subject=rbac_subject_id,
            cache_doc_id=doc_id,
        ))

    return CacheLookupResult(HIT, body_hash, cached)
```

### 2.1 RFC 8785 canonicalisation

`canonical_sha256(body)` is implemented as:

```python
import canonicaljson  # PyPI, RFC 8785 conformant
import hashlib

def canonical_sha256(body: dict) -> str:
    canon = canonicaljson.encode_canonical_json(body)  # bytes
    return hashlib.sha256(canon).hexdigest()
```

The stdlib `json.dumps(..., sort_keys=True, separators=(",", ":"))` is **not** RFC 8785 conformant for floating-point numbers (per ADR-036-009 § "RFC 8785" rationale) and MUST NOT be used.

---

## 3. Lifecycle state-machine consumption table

| Cached verb | Sim state at replay | Action |
|---|---|---|
| `pause` | `paused` | Replay cached 200 (idempotent re-pause) |
| `pause` | `active` (was resumed) | **HTTP 409** `lifecycle-state-conflict` |
| `pause` | `ended` | **HTTP 409** `lifecycle-state-conflict` |
| `resume` | `active` | Replay cached 200 |
| `resume` | `paused` | **HTTP 409** `lifecycle-state-conflict` (re-paused after resume) |
| `abort` | `ended` | Replay cached 200 (idempotent re-abort) |
| `abort` | `active` or `paused` | **HTTP 409** `lifecycle-state-conflict` (impossible — SEV-2 alert) |
| `inject-telemetry` | `active` | Replay cached response (200 or 4xx) |
| `inject-telemetry` | `paused` | **HTTP 409** `audit.lifecycle.refused_while_paused` (refusal NOT cached per pass 2 Q7) |
| `inject-telemetry` | `ended` | Replay cached response (immutable history; FR-054 lessons-capture readers may still query) |

**Side-effect ordering invariant**: cache write happens **AFTER** the side effect commits, **BEFORE** the response returns to the client. This ensures (a) a successful replay reflects committed state, (b) a server crash between side effect and cache write produces a duplicate side effect at most once on retry — handled by upstream retry-budgeting.

---

## 4. TTL semantics

- **TTL = 86 400 s = 24 hours**, set at insert via Cosmos native `ttl` field.
- **Anchor**: Cosmos `_ts` (set by Cosmos at write time). `_ts` is updated only on writes; **replay reads do NOT extend TTL**.
- **Eviction**: Cosmos auto-evicts when `_ts + ttl < now()`. After eviction, a subsequent request with the same key + body is treated as a fresh request.
- **24 h is exact**: not "approximately 24 hours". Cosmos TTL precision is 1 second.

**Why 24 hours, not longer?**

- Per spec FR-066 / pass 1 Q3: the 24 h window is sufficient to cover client-side retry intervals, browser-tab refreshes, and short-lived network flaps.
- Longer windows (e.g. 7 days) would expose a wider replay-attack surface and accumulate cost without proportional benefit.
- Shorter windows (e.g. 1 hour) would not survive realistic client retry patterns.

**TTL anchoring on `_ts`, NOT on `expires_at`**: the document carries a stored `created_at` for forensic display and a derivative `ttl` for Cosmos eviction. There is no `expires_at` field — Cosmos computes effective expiry as `_ts + ttl`.

---

## 5. 503 caching from sequence-uncertainty

Per ADR-036-007, when the audit sequence allocator exhausts its retry budget the originating endpoint returns **HTTP 503** + `Retry-After: 5`. This response IS cached for the full 24 h replay window so that retried requests do not double-attempt the underlying Cosmos operation. Cache document for a cached 503:

```json
{
  "id": "{sim_id}/POST/{route}/{idempotency_key}",
  "_partitionKey": "{simulation_id}",
  "sim_id": "uuid",
  "idempotency_key": "client-supplied",
  "verb": "POST",
  "route": "/api/simulations/{simId}/inject-telemetry",
  "body_hash": "sha256-hex",
  "response_status": 503,
  "response_body": {
    "type": "https://api.platform.example.gov.au/problems/sequence-uncertainty",
    "title": "Audit sequence allocator exhausted",
    "status": 503,
    "detail": "The audit sequence allocator could not allocate a gap-free sequence number within the retry budget.",
    "instance": "<request_correlation_id>",
    "uncertainty_reason": "etag_exhausted",
    "dlq_entry_id": "<uuid>"
  },
  "response_headers_subset": {
    "content-type": "application/problem+json",
    "retry-after": "5"
  },
  "request_correlation_id": "uuid",
  "rbac_subject_id": "Entra OID",
  "created_at": "2026-05-08T10:23:14Z",
  "ttl": 86400
}
```

The dead-letter queue entry referenced by `dlq_entry_id` is the source of truth for the underlying uncertainty event (per § 8.5 of `data-model.md`).

---

## 6. Cross-user replay handling

If `cached.rbac_subject_id != current_request.rbac_subject_id`, the replay **proceeds** (the original response already committed the side effect) BUT a SEV-2 audit-only event `audit.idempotency.replay_cross_user` is written. Operations team alerts (`ag-sim-sre-prod`) fire on aggregated occurrences (≥ 5 cross-user replays in 24 h per simulation).

**Why not refuse?** Refusing would surface the existence of the cached entry to the wrong user (information disclosure). Accepting is safer; the audit trail is the forensic mechanism.

---

## 7. Eviction and cleanup

- Cosmos handles automatic eviction via TTL. No background worker required.
- **Simulation end (`abort` or `end_reason: ended`)**: cache entries are NOT explicitly purged; they continue to serve replays for the remaining TTL. This preserves replay receipts even after the simulation is archived.
- **Lessons-capture (FR-054)**: lessons-capture readers MAY query cache entries to enrich the timeline (e.g. distinguishing cached replays from fresh requests). The cache is read-only for them.

---

## 8. Testing

| Test | File | Purpose |
|---|---|---|
| Contract — RFC 8785 canonicalisation | `tests/contract/test_rfc8785_canonical_json.py` | All RFC 8785 § 3.2 test vectors pass |
| Contract — wire shape | `tests/contract/test_idempotency_cache_wire_shape.py` | Cache document validates against the JSON Schema in `data-model.md` § 8.2 |
| Integration — body-hash conflict | `tests/integration/test_idempotency_body_hash_mismatch.py` | Same key + different body returns 422 `idempotency-key-conflict` |
| Integration — lifecycle round-trip | `tests/integration/test_idempotency_round_trip.py` | `pause→resume→pause` (replay) returns 409 `lifecycle-state-conflict` |
| Integration — 503 caching | `tests/integration/test_idempotency_503_cache.py` | Sequence-uncertainty 503 is cached and replayed without re-attempting |
| Integration — RBAC ordering | `tests/integration/test_idempotency_rbac_ordering.py` | RBAC denial precedes cache read |
| Integration — TTL anchoring | `tests/integration/test_idempotency_ttl.py` | Eviction occurs at `_ts + ttl`; replays do not extend TTL |
| Load — idempotency overhead | `tests/load/simulation_injection_load.py` | Cache lookup adds ≤ 5 ms P95 to lifecycle endpoints |

---

*Contract authored 2026-05-08 in the Step 8 amendment cycle; aligned with ADR-036-009.*
