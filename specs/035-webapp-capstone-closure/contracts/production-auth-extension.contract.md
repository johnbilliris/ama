# Production-Auth Extension Envelope Contract

**Spec**: [`specs/035-webapp-capstone-closure/spec.md` § FR-009](../spec.md#functional-requirements) · [Clarifications Q10](../spec.md#clarifications)
**Research**: [`research.md` § R-007](../research.md#r-007--production-auth-extension-envelope-and-error-precedence)

This contract is **layered additively** over the spec-034 evaluator contract at [`specs/034-webapp-capstone-coverage/contracts/outcome-evaluator.contract.md`](../../034-webapp-capstone-coverage/contracts/outcome-evaluator.contract.md). The spec-034 success body is preserved verbatim per [OOS-006](../spec.md#out-of-scope); this contract only specifies the **error path**.

## Scope

Applies to the following production-reachable endpoints:

- `POST /api/outcomes/sc-{001..011}/evaluate`
- `GET /api/audit/list`
- `GET /api/auth/whoami`
- `POST /api/offline/replay`
- `POST /api/recovery/handover/sign`

## Success body (UNCHANGED from spec-034)

```json
{
  "status": "pass" | "fail" | "inconclusive",
  "evidence_refs": ["audit-id-1", "audit-id-2"],
  "metric_value": 0.97,
  "threshold": 0.95,
  "audit_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV"
}
```

## Error body (spec-035 extension envelope)

```json
{
  "error_code": "unauthorized" | "forbidden" | "sovereignty_denied" | "rate_limited" |
                "evaluator_not_routable" | "schema_invalid" | "seed_not_ready",
  "retry_after_seconds": 30 | null,
  "audit_id": "01ARZ3NDEKTSV4RRFFQ69G5FAV",
  "correlation_id": "9b2a4e0f-7c1c-4f18-9ad6-1c9a2f4f3a10"
}
```

`retry_after_seconds` is non-null only for `rate_limited` and `seed_not_ready`.

## HTTP status mapping

| `error_code` | HTTP | Notes |
|---|---|---|
| `unauthorized` | 401 | Missing / invalid / expired bearer |
| `forbidden` | 403 | Valid bearer; AppRole/persona mismatch (FR-011 stage-b) |
| `sovereignty_denied` | 403 | NN-1 violation (PSPF/PII at gateway) |
| `rate_limited` | 429 | `Retry-After` header MUST match `retry_after_seconds` |
| `evaluator_not_routable` | 400 | Unknown SC-id (sc-006..sc-011 not yet shipped, or typo) |
| `schema_invalid` | 422 | Pydantic validation failure |
| `seed_not_ready` | 503 | Cosmos warmup; transient |

## Error precedence ladder (highest → lowest)

The middleware stack MUST evaluate in this fixed order; the first match short-circuits:

1. `400 evaluator_not_routable` — sc-006..sc-011 not in registry (cheap to detect; identifies the CI-job owner immediately, regardless of bearer state).
2. `403 sovereignty_denied` — NN-1 wins (PSPF/PII classifier fired BEFORE auth check, because we never want to leak that an unauthenticated caller hit a regulated route).
3. `401 unauthorized` — invalid / missing / expired bearer.
4. `403 forbidden` — valid bearer, wrong AppRole or `persona_id` outside scope (FR-011 stage-b).
5. `429 rate_limited` — APIM-emitted; FastAPI middleware converts to envelope shape.
6. `422 schema_invalid` / `503 seed_not_ready` — payload / availability errors only after the caller is fully authorised.

## Audit row shape (always emitted, allowed/denied/rate-limited/schema-rejected)

```json
{
  "audit_id": "...",
  "correlation_id": "...",
  "outcome": "approved" | "denied" | "rate_limited" | "auth_unauthorized" | "auth_forbidden" |
              "sovereignty_denied" | "schema_invalid" | "seed_not_ready" | "evaluator_not_routable",
  "operator_identity": "<entra-oid>",
  "app_role": "<one of 11>",
  "persona_id": "<target>" | "*",
  "impersonated_persona_id": "<target>" | null,
  "impersonated_by": "<admin-oid>" | null,
  "route": "/api/outcomes/sc-001/evaluate",
  "extension_envelope": { ... },   // present iff outcome ∈ error states
  "timestamp": "..."
}
```

The `extension_envelope` MUST byte-equal the body returned to the caller.

## Tests

- Success-path contract test (preserves spec-034 numerics).
- One precedence-ladder test per pair of stacked error conditions (e.g., `rate_limited + schema_invalid` → 429 wins).
- Audit-row equality test: response `extension_envelope` byte-equals `extension_envelope` field on the appended row.
