# Contract: RFC 9457 Problem Detail Error Responses

**Feature**: 036 — Simulation Telemetry-Injection Agent (amendment cycle)
**Spec FRs**: FR-048 (Step 8 Amendment D), FR-051 (Amendment E), FR-059 (Amendment F), FR-066 (Amendment S), FR-049 + FR-054 (evidence-integrity warnings)
**Constitution**: I (Primacy of Life — fail-closed), IV (Transparency and Auditability)
**Standard**: **RFC 9457** — Problem Details for HTTP APIs (the 2024-published successor to RFC 7807; supersedes RFC 7807 with extension-fields ABNF clarifications)
**Authoring ADRs**: ADR-036-007 (sequence allocator fail-closed), ADR-036-009 (idempotency cache)

This contract enumerates **every RFC 9457 problem-detail type** produced by feature 036 (including those introduced in the Step 8 amendment cycle and Cycle 2 amendments) and pins the schema, status code, type-URI convention, and FastAPI integration pattern for each. **Every error response from spec-036 endpoints (defined by the `SPEC_036_PROBLEM_JSON_ROUTES` allow-list — see § 7 below) is `application/problem+json`, regardless of the client's `Accept` header (per RFC 9457 § 4 — the more-specific media type wins for declared error responses).** Endpoints **outside** the spec-036 allow-list continue to emit the legacy `{correlationId, statusCode, errorCategory, message}` envelope produced by `apps/api/app/middleware/error_handler.py:24-72`; that legacy envelope is preserved unchanged (Cycle 2 Amendment A2-05 narrowing path; refactor explicitly avoided to contain blast radius).

---

## 1. Common envelope

Every problem-detail response conforms to:

```json
{
  "type": "https://api.platform.example.gov.au/problems/<error-name>",
  "title": "Human-readable summary (locale-independent)",
  "status": 409,
  "detail": "Localised human-readable detail (en-AU primary)",
  "instance": "<chat_turn_id | correlation_id | uuid>",
  "<extension-field-1>": "...",
  "<extension-field-2>": "..."
}
```

**Type URI convention**: `https://api.platform.example.gov.au/problems/<error-name>` — stable URIs that resolve (HTTP-fetchable) to the human-readable error catalogue (one Markdown page per `type` under `docs/disaster-response-hub/error-catalogue/`). The URI is the **canonical discriminator** across all clients.

**FastAPI integration**: a single `ProblemDetailException(status_code, type_uri, title, detail, instance, **extensions)` exception class is registered with `app.exception_handler(ProblemDetailException)` to render `application/problem+json` responses. The handler also sets the OpenTelemetry `exception.type` attribute to the URI for trace correlation. RFC-9457-compliant extensions are flat top-level fields per RFC § 3.2.

---

## 2. Defined problem-detail types

### 2.1 `lifecycle-state-conflict`

**Type URI**: `https://api.platform.example.gov.au/problems/lifecycle-state-conflict`
**HTTP status**: **409**
**Raised by**: FR-066 idempotency cache + state-machine consumption mismatch (decision 15 / ADR-036-009)
**Trigger conditions** (see ADR-036-009 § "Lifecycle state-machine consumption"):

- `pause` cached + sim now `active` (was resumed): replay refused.
- `pause` cached + sim now `ended`: replay refused.
- `resume` cached + sim now `paused` (was re-paused): replay refused.
- `abort` cached + sim now `active` or `paused` (impossible — SEV-2 alert): replay refused.

**Body shape**:

```json
{
  "type": "https://api.platform.example.gov.au/problems/lifecycle-state-conflict",
  "title": "Lifecycle state conflict",
  "status": 409,
  "detail": "The cached idempotency entry for verb 'pause' is inconsistent with the current simulation state 'active'. The original pause was already consumed by a subsequent resume.",
  "instance": "<request_correlation_id>",
  "idempotency_key": "<client-supplied>",
  "verb": "pause",
  "route": "/api/simulations/{simId}/pause",
  "current_state": "active",
  "cached_response_status": 200,
  "cache_created_at": "2026-05-08T10:23:14Z"
}
```

**Audit consequence**: NO new audit entry is written for the 409 itself (the original lifecycle audit entry is preserved). The cache is RETAINED for the full 24 h replay window as an immutable receipt; the state machine merely refuses re-execution.

### 2.2 `idempotency-key-conflict`

**Type URI**: `https://api.platform.example.gov.au/problems/idempotency-key-conflict`
**HTTP status**: **422**
**Raised by**: FR-066 idempotency cache + body-hash mismatch (ADR-036-009)
**Trigger condition**: a request arrives with a known `Idempotency-Key` for the same `(sim_id, verb, route)` tuple but a DIFFERENT canonical-body sha256 (per RFC 8785 JCS canonicalisation).

**Body shape**:

```json
{
  "type": "https://api.platform.example.gov.au/problems/idempotency-key-conflict",
  "title": "Idempotency-Key body mismatch",
  "status": 422,
  "detail": "An earlier request used the same Idempotency-Key for this verb and simulation, but with a different request body. Idempotency-Key reuse requires a byte-identical canonical body (RFC 8785).",
  "instance": "<request_correlation_id>",
  "idempotency_key": "<client-supplied>",
  "verb": "POST",
  "route": "/api/simulations/{simId}/inject-telemetry",
  "body_hash_attempted": "<sha256-of-incoming-canonical-body>",
  "body_hash_cached": "<sha256-of-cached-canonical-body>",
  "cache_created_at": "2026-05-08T10:23:14Z"
}
```

**Client guidance**: clients MUST generate a NEW `Idempotency-Key` for every distinct request body. Reusing a key with a different body is a client bug.

### 2.3 `injection-refused`

**Type URI**: `https://api.platform.example.gov.au/problems/injection-refused`
**HTTP status**: **400** (most reasons), **429** (`circuit_open`)
**Raised by**: FR-009 / FR-010 / FR-052 / FR-057 refusals (existing — pre-amendment)
**Reason enum** (`reason` extension field):

- `life_safety_low_confidence` — FR-010 hybrid gate; life-safety category at `low` confidence.
- `missing_provenance` — FR-009; required provenance fields absent.
- `unknown_category` — FR-009; parsed category outside the 9-value closed enum.
- `malformed_input` — pre-LLM regex / Content Safety scrubber rejection.
- `pii_detected` — Content Safety scrubber detected PII.
- `thread_cap_exceeded` — FR-052; would create 6th hazard thread.
- `cascade_depth_exceeded` — FR-043; would create depth-2 cascade.
- `circuit_open` — FR-009 parse-attempt circuit-breaker tripped (HTTP 429 only).

**Body shape**:

```json
{
  "type": "https://api.platform.example.gov.au/problems/injection-refused",
  "title": "Telemetry injection refused",
  "status": 400,
  "detail": "Life-safety category 'fire-behaviour' parsed at 'low' confidence; coordinator clarification required.",
  "instance": "<chat_turn_id>",
  "reason": "life_safety_low_confidence",
  "category": "fire-behaviour",
  "confidence": "low",
  "clarification_question": "What is the current head-fire intensity? Provide a Byram-Index estimate or report \"not visible\"."
}
```

### 2.4 `evidence-integrity-warning`

**Type URI**: `https://api.platform.example.gov.au/problems/evidence-integrity-warning`
**HTTP status**: not an error — emitted as a **`Warning` HTTP response header on 200/2xx responses** AND as a structured marker inside the FR-049 audit-export payload + FR-054 lessons-capture record. The `application/problem+json` body is the structured form; the `Warning` header carries a compact form per RFC 7234 § 5.5 (multiple `warn-codes` permitted).
**Raised by**: ADR-036-007 fail-closed protocol — when a reader (FR-049 export, FR-054 lessons-capture, FR-066 cache replay) detects `sequence_number = -1` entries in the `simulation_audit_dlq` for the simulation in scope.

**Body shape**:

```json
{
  "type": "https://api.platform.example.gov.au/problems/evidence-integrity-warning",
  "title": "Audit evidence-integrity warning",
  "status": 200,
  "detail": "1 audit entry with sequence_number = -1 detected in the dead-letter queue for this simulation; downstream consumers MUST treat the affected window as evidence-incomplete.",
  "instance": "<sim_id>",
  "dlq_entry_count": 1,
  "earliest_dlq_entry_at": "2026-05-08T10:23:14Z",
  "uncertainty_reasons": ["etag_exhausted"],
  "affected_correlation_ids": ["<uuid-1>"]
}
```

**Reader contract**: failure to detect = bug; FR-049 audit-export and FR-054 lessons-capture include this warning at the top of their generated artefacts when applicable.

---

## 3. Other lifecycle 4xx responses

For completeness, the following pre-existing error families also use RFC 9457 problem-detail form:

| Type URI | Status | Raised by |
|---|---|---|
| `https://api.platform.example.gov.au/problems/forbidden` | 403 | FR-051 RBAC denial (JWT/role/tenant validation precedes idempotency replay) |
| `https://api.platform.example.gov.au/problems/not-found` | 404 | Simulation not found; sub-agent unknown |
| `https://api.platform.example.gov.au/problems/sequence-uncertainty` | 503 | ADR-036-007 sequence allocator retry exhaustion (`Retry-After: 5`) |

---

## 4. Content negotiation

- All listed responses send `Content-Type: application/problem+json` regardless of the client's `Accept` header (per RFC 9457 § 4) **but only when the request path matches the `SPEC_036_PROBLEM_JSON_ROUTES` allow-list defined in § 7**. Non-matching routes continue to use the legacy `{correlationId, statusCode, errorCategory, message}` envelope.
- Clients sending `Accept: application/problem+json` explicitly are preferred and will be optimised for first.
- The OpenAPI advertisement (`contracts/openapi-simulation.yaml`) references `#/components/schemas/ProblemDetails` on every error response.
- Locale (`detail` field): `en-AU` primary; future amendment may add `Content-Language` negotiation.

---

## 5. Testing

| Test | File | Purpose |
|---|---|---|
| Contract — every URI resolves to the catalogue | `tests/contract/test_problem_detail_uris.py` | Each `type` URI listed above MUST resolve to a published Markdown page under `docs/disaster-response-hub/error-catalogue/` |
| Contract — RFC 9457 envelope shape | `tests/contract/test_problem_details_shape.py` | Each emitted problem detail MUST conform to RFC 9457 § 3 envelope + § 3.2 extensions |
| Contract — spec-036 route allow-list | `tests/contract/test_spec_036_route_allow_list.py` | The `SPEC_036_PROBLEM_JSON_ROUTES` frozenset's contents MUST be byte-equal to the route enumeration in § 7 below AND every route declared with the `@router` decorator under `apps/api/app/api/routes/simulations_036.py` MUST appear in the frozenset (Cycle 2 pass-1 Q5). Synthetic 5xx (`RuntimeError` from a fixture endpoint) on any allow-listed route MUST emit `application/problem+json` (Cycle 2 pass-2 Q5). |
| Integration — `lifecycle-state-conflict` | `tests/integration/test_idempotency_round_trip.py` | `pause→resume→pause` (replay) returns 409 |
| Integration — `idempotency-key-conflict` | `tests/integration/test_idempotency_body_hash_mismatch.py` | Same key + different body returns 422 |
| Integration — `evidence-integrity-warning` | `tests/integration/test_audit_dlq_warning_propagation.py` | DLQ entry surfaces in FR-049 export with the warning header |

---

## 6. Backwards compatibility

Existing 4xx responses returning bare JSON (e.g. simulator scaffolding endpoints not in scope for FR-066, healthchecks, infrastructure pings, legacy spec-024 simulation endpoints under non-allow-listed paths) continue to work unchanged via the legacy `error_handler.py:24-72` middleware envelope. The new RFC 9457 surfaces are limited to the routes listed in § 7 — the four FR-066 lifecycle endpoints + the FR-049 export + the new evidence-integrity warning + every other route declared under `apps/api/app/api/routes/simulations_036.py`.

---

## 7. Spec-036 endpoint allow-list

Per Cycle 2 Amendment A2-05 (RFC 9457 contract-scope narrowing) and Cycle 2 pass-1 Q5 (allow-list selection mechanism), the spec-036 RFC 9457 surface is governed by an **explicit allow-list constant** (NOT URL-prefix match, NOT OpenAPI tag) defined in code:

```python
# apps/api/app/middleware/error_handler.py (or sibling module)
from typing import Final

SPEC_036_PROBLEM_JSON_ROUTES: Final[frozenset[str]] = frozenset({
    # FR-007 / Cycle 2 A2-01 — telemetry injection (degraded_dispatch, RFC 9457 errors)
    "/api/simulations/{sim_id}/inject-telemetry",
    # FR-059 / FR-066 — lifecycle endpoints (idempotent; RFC 9457 on conflict / refusal)
    "/api/simulations/{sim_id}/abort",
    "/api/simulations/{sim_id:uuid}/pause",
    "/api/simulations/{sim_id:uuid}/resume",
    # FR-013 — recent-signals (RBAC failures emit RFC 9457)
    "/api/simulations/{sim_id}/recent-signals",
    # FR-049 / FR-054 — outcome read (audit-export, evidence-integrity warning carrier)
    "/api/simulations/{sim_id}/outcome",
})
```

**Runtime mechanism** (per Cycle 2 pass-1 Q5):

1. The middleware at `apps/api/app/middleware/error_handler.py:24-72` checks `request.url.path` (after FastAPI path-parameter normalisation, e.g. `/api/simulations/{sim_id}/inject-telemetry`) against this frozenset.
2. **Matches** emit `application/problem+json` per § 1 envelope on **both 4xx AND 5xx** error responses (per Cycle 2 pass-2 Q5 — split scope rejected because ADR-036-007's `sequence-uncertainty` problem-detail is HTTP 503 5xx and is already enumerated as RFC 9457 in § 3 below).
3. **Non-matches** emit the legacy `{correlationId, statusCode, errorCategory, message}` envelope unchanged.
4. The pre-existing 2xx `evidence-integrity-warning` (§ 2.4) is an **explicitly-documented carve-out** emitted by the FR-049 export / FR-054 lessons-capture pathways via a `Warning` HTTP header on 200 responses with the structured RFC 9457 body in the response payload. This carve-out does NOT travel through `error_handler.py:24-72` and is unchanged by Cycle 2 pass-2 Q5.

**Why explicit allow-list (not prefix match, not OpenAPI tag)** — per Cycle 2 pass-1 Q5 rationale:

- Explicit allow-list is grep-able, unit-testable, and reviewable in a PR diff.
- URL-prefix match is fragile — legacy routes under `/api/simulations/*` from spec 024 could inadvertently start emitting RFC 9457 with a future addition.
- OpenAPI tag couples middleware to OpenAPI metadata (additional indirection at runtime).
- Constitution Principle V (no blast-radius onto legacy surfaces) is honoured by making the surface enumeration auditable.

**Single-source-of-truth contract test** — `tests/contract/test_spec_036_route_allow_list.py` MUST assert:

1. The `SPEC_036_PROBLEM_JSON_ROUTES` frozenset's contents are byte-equal to the route enumeration above.
2. Every route declared with the `@router` decorator under `apps/api/app/api/routes/simulations_036.py` appears in the frozenset (drift detection).
3. A synthetic 5xx (e.g. `RuntimeError` raised from a fixture endpoint) on any allow-listed route emits `application/problem+json`.

---

*Contract authored 2026-05-08 in the Step 8 amendment cycle; aligned with ADR-036-007, ADR-036-009. Cycle 2 revision 2026-05-09 — Amendment A2-05 narrowed § 1 universal-MIME claim to spec-036 endpoints (per pass-1 Q5 explicit `SPEC_036_PROBLEM_JSON_ROUTES` allow-list); pass-2 Q5 extended allow-list scope to BOTH 4xx AND 5xx response codes (with the 2xx `evidence-integrity-warning` § 2.4 preserved as documented carve-out via `Warning` header).*
