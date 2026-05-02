# Outcome Evaluator Contract — spec 034

> **Status**: Accepted (cycle-1, /speckit.tasks 2026-02-05). Reviewed and integrated by T173.

This is the human-readable contract for the FR-028 outcome-evaluator and
audit-list endpoints. It is a Phase-1 contract peer of
`coverage-trace-row.schema.json` and `persona-fixture.contract.md`,
authored at plan re-run per spec.md Pass 4 Q21 (request / response
shape, idempotency, error contract), Pass 5 Q27 (Phase-1 promotion +
JSON-Schema embedding pattern), and Pass 5 Q29 (routable range bounded
to `sc-001..sc-005`).

## Contract intent

The suite drives workflow-state assertions for each persona × outcome
tuple via two route-only endpoints (no net-new Azure resource — OOS-003
does not apply):

1. `POST /api/outcomes/sc-{001..005}/evaluate` — capstone-outcome
   evaluator returning a structured judgement.
2. `GET /api/audit/list` — correlation-keyed read-back of the
   append-only audit timeline.

Both endpoints are guarded by the dual-guard test-support contract
(see `persona-fixture.contract.md` §Activation): activation requires
`os.environ.get("AMA_TEST_SUPPORT") == "1"` AND
`settings.environment in {"dev", "test"}`. Production registration is
forbidden; reaching them in production returns `404 Not Found` (router
not registered) and an audit log entry recording the activation
refusal.

## Routable range — `sc-001..sc-005` only (Q29)

The evaluator endpoint serves **only** the five capstone-outcome
metrics whose `metric_inputs` are derivable from
`HazardScenarioFixture.baseline` (data-model.md §6):

| `sc_id`  | Capstone outcome                | `metric_inputs` source field          |
| -------- | ------------------------------- | ------------------------------------- |
| `sc-001` | Lives saved (≥ 1 community-language variant + vulnerable-pop filters) | `baseline.lives_at_risk`              |
| `sc-002` | 50 % faster signal-to-action    | `baseline.signal_to_action_ms`        |
| `sc-003` | 24-hour-earlier evacuation      | `baseline.evac_lead_hours`            |
| `sc-004` | 30 % logistics-friction reduction | `baseline.logistics_clicks`           |
| `sc-005` | 30 % economic-loss reduction (Sendai-aligned) | `baseline.economic_loss_aud` |

Requests for `sc-006..sc-011` (or any `sc_id` outside `001..005`)
return HTTP `400` with a body that names the CI-artefact owner of that
metric (Q29). Those metrics are derived from CI artefacts directly, not
from a workflow-state evaluator — they are owned by:

| `sc_id`  | CI-artefact owner                          |
| -------- | ------------------------------------------ |
| `sc-006` | `web-coverage-gate` (T153) — persona-coverage row count from `coverage-trace.json` |
| `sc-007` | `web-coverage-gate` (T153) — cross-jurisdiction tag count |
| `sc-008` | `web-coverage-gate` (T153) — cross-cutting JUnit XML scan |
| `sc-009` | `gap-register.py validate` (T045)          |
| `sc-010` | `verify-trace-determinism.ps1` (T051)      |
| `sc-011` | `web-coverage-shard` `timeout-minutes: 45` (`plan.md` L419) |

## Server-side contract — evaluator

### Endpoint

```
POST /api/outcomes/sc-{sc_id}/evaluate
```

`sc_id` is the zero-padded outcome number (`001`, `002`, `003`, `004`,
`005`). Path values outside this set return `400` per Q29.

### Request body

```json
{
  "scenario_id": "outcome-1-bushfire-extreme-heat",
  "persona_id": "ic-nsw-rfs",
  "correlation_id": "5d1f8a8e-12ab-4c3d-9ef0-aa11bb22cc33",
  "metric_inputs": {
    "lives_at_risk": 1200
  }
}
```

### Request JSON Schema (embedded for `ajv` validation)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ama.local/contracts/spec-034/outcome-evaluator-request.schema.json",
  "title": "EvaluatorRequest",
  "type": "object",
  "additionalProperties": false,
  "required": ["scenario_id", "persona_id", "correlation_id", "metric_inputs"],
  "properties": {
    "scenario_id": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9-]*[a-z0-9]$",
      "description": "Kebab-case scenario id; MUST resolve in bootstrap_seed_data() scenarios. Unknown values return 404."
    },
    "persona_id": {
      "type": "string",
      "pattern": "^[a-z0-9][a-z0-9-]*[a-z0-9]$",
      "description": "MUST resolve in bootstrap_seed_data().identities (ASM-011). Fixture-only identities are forbidden."
    },
    "correlation_id": {
      "type": "string",
      "format": "uuid",
      "description": "UUID v4 propagated via the X-Correlation-Id header chain. Idempotency tuple member."
    },
    "metric_inputs": {
      "type": "object",
      "description": "Shape is sc_id-specific; sourced from data-model.md §6 HazardScenarioFixture.baseline. See per-sc_id sub-schemas below.",
      "additionalProperties": true
    }
  }
}
```

### Per-`sc_id` `metric_inputs` shapes

```json
{
  "sc-001": { "type": "object", "required": ["lives_at_risk"],        "properties": { "lives_at_risk":        { "type": "number", "minimum": 0 } } },
  "sc-002": { "type": "object", "required": ["signal_to_action_ms"],  "properties": { "signal_to_action_ms":  { "type": "number", "minimum": 0 } } },
  "sc-003": { "type": "object", "required": ["evac_lead_hours"],      "properties": { "evac_lead_hours":      { "type": "number", "minimum": 0 } } },
  "sc-004": { "type": "object", "required": ["logistics_clicks"],     "properties": { "logistics_clicks":     { "type": "integer", "minimum": 0 } } },
  "sc-005": { "type": "object", "required": ["economic_loss_aud"],    "properties": { "economic_loss_aud":    { "type": "number", "minimum": 0 } } }
}
```

### Response 200

Matches FR-028 exactly:

```json
{
  "status": "pass",
  "evidence_refs": [
    "audit:5d1f8a8e-12ab-4c3d-9ef0-aa11bb22cc33",
    "trace:tests/e2e/web-coverage/capstone/outcome-1-bushfire-extreme-heat.spec.ts"
  ],
  "metric_value": 1187,
  "threshold": 1000,
  "audit_id": "11112222-3333-4444-5555-666677778888"
}
```

### Response 200 JSON Schema (embedded)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://ama.local/contracts/spec-034/outcome-evaluator-response.schema.json",
  "title": "EvaluatorResponse",
  "type": "object",
  "additionalProperties": false,
  "required": ["status", "evidence_refs", "metric_value", "threshold", "audit_id"],
  "properties": {
    "status":        { "type": "string", "enum": ["pass", "fail", "gap"] },
    "evidence_refs": { "type": "array",  "items": { "type": "string", "minLength": 1 }, "minItems": 0 },
    "metric_value":  { "oneOf": [{ "type": "number" }, { "type": "null" }] },
    "threshold":     { "oneOf": [{ "type": "number" }, { "type": "null" }] },
    "audit_id":      { "type": "string", "format": "uuid" }
  }
}
```

### Idempotency

Idempotency is keyed by the tuple
`(sc_id, scenario_id, persona_id, correlation_id)`:

- A repeated request with the same tuple returns the **same**
  `audit_id` and the **same** verdict (no fresh audit row, no
  duplicate counterfactual evaluation).
- A new `correlation_id` (with otherwise identical other tuple fields)
  triggers a fresh evaluation and a new audit-timeline row.
- Tests rely on this rule to retry safely after transient infrastructure
  failures without inflating the audit-row count or the SC-005
  counterfactual.

### Error responses

| Status | Body                                                                                                   | Trigger                                                                                       |
| ------ | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------- |
| `400`  | `{ "error": "evaluator_not_routable", "sc_id": "...", "suggested_action": "see SC-XXX ownership in spec.md FR-028 / Pass 5 Q29 — derived from CI artefacts (web-coverage-gate, gap-register, verify-trace-determinism), not from a workflow-state evaluator endpoint" }` | `sc_id` ∉ `{001..005}` (per Q29). Suite MUST NOT silently pass on this code. |
| `404`  | `{ "error": "scenario_not_found", "scenario_id": "...", "suggested_action": "register in bootstrap_seed_data() or update depth profile" }` | `scenario_id` not present in the seeded scenario registry. Suite MUST treat as `GAP-EVALUATOR-SCENARIO-MISSING` per FR-005 — silent pass forbidden. |
| `422`  | Standard FastAPI request-validation envelope                                                           | Request body fails the embedded JSON Schema above.                                            |
| `503`  | `{ "error": "seed_not_ready" }`                                                                        | `bootstrap_seed_data()` has not yet completed; suite waits for ready signal.                  |

### Audit emission

Every successful evaluation (HTTP 200) appends an audit row visible to
`/api/audit/list?correlation_id={correlation_id}`. The row carries
rationale, source references, confidence, operator identity (the
persona id under the dual-guard), and the evaluator's `audit_id`. The
audit append SLO is ≤ 2 s end-to-end (FR-004 / R-005).

## Server-side contract — audit-list

### Endpoint

```
GET /api/audit/list?correlation_id={uuid}&cycle={current|all}&limit={1..500}&cursor={opaque}
```

### Activation

Same dual-guard as the evaluator (`AMA_TEST_SUPPORT == "1"` AND
`environment in {"dev","test"}`); router is not registered in
production.

### Cycle semantics (Q22)

- `cycle=current` (default): returns rows with
  `audit_timestamp >= bootstrap_seed_data().current_cycle_start`. The
  server reads this timestamp directly from `bootstrap_seed_data()` —
  it does NOT consult the gap register. The suite-side
  `cycle-metadata.json` artefact (Q26) is the symmetric Playwright-side
  surface for the same value.
- `cycle=all`: opt-in only; reserved for FR-005 cross-cycle
  status-transition reads + FR-027 regression evidence (failing test id +
  reverted commit SHA + restored revision).

### Pagination

- Cursor-based; response includes `next_cursor: string | null`.
- `limit` defaults to `100`, capped at `500` to bound CI runtime per
  SC-011.

### Retention

Rows are append-only and **never deleted** (constitution §IV +
FR-010). The endpoint surface only filters and paginates; it never
truncates or rewrites the timeline. Tamper attempts are themselves
audit events (Q24 (a) — cf. `safety_critical_workflow:
observe-tamper-resist` in the depth-profile schema).

### Response shape

```json
{
  "count": 42,
  "items": [
    {
      "audit_id": "11112222-3333-4444-5555-666677778888",
      "audit_timestamp": "2025-11-20T03:15:42.187Z",
      "correlation_id": "5d1f8a8e-12ab-4c3d-9ef0-aa11bb22cc33",
      "operator_identity": { "persona_id": "ic-nsw-rfs" },
      "rationale": "AWS publish approved — vulnerable-population filter applied; community-language variants en + zh-Hans rendered.",
      "confidence": 0.94,
      "source_refs": [
        "incident:inc-bf-2025-11-001",
        "warning:wrn-bf-2025-11-001-v3"
      ],
      "outcome": "approved"
    }
  ],
  "next_cursor": null,
  "cycle": "current"
}
```

`AuditRow` matches FR-010's required fields: `audit_timestamp`,
`rationale`, `confidence`, `source_refs`, `operator_identity`, and
`correlation_id`. Tamper-attempt rows additionally carry
`outcome: "denied"` per Q24 (a).

## Client-side fixture binding

The Playwright fixture
`tests/e2e/web-coverage/_support/fixtures/evaluator.fixture.ts` (added
under tasks T173 + T146..T150) wraps the evaluator and audit-list
endpoints with:

- automatic `correlation_id` propagation via `correlationIdFixture`
  (already defined in plan.md §Fixtures);
- typed `EvaluatorRequest` / `EvaluatorResponse` aliases imported from
  `data-model.md` §EvaluatorRequest / §EvaluatorResponse;
- `expect.poll(...)` on the audit-list read-back so the FR-004 ≤ 2 s
  audit-append SLO is enforceable in tests;
- a 404 → `GAP-EVALUATOR-SCENARIO-MISSING` opener that calls
  `scripts/web-coverage/gap-register.py open` on the suite-side fallback
  audit shadow (tests/e2e/web-coverage/_artifacts/gap-register-audit.jsonl).

## CI gate binding

`web-coverage-gate` (T153) extension required by Q27:

- Validate every captured evaluator request payload (recorded by the
  reporter as a coverage annotation) against the embedded
  `EvaluatorRequest` JSON Schema using `ajv` (consistent with T047's
  schema-validator pattern).
- Validate every captured 200 response against the embedded
  `EvaluatorResponse` schema.
- Fail the gate on any request producing HTTP 400 (`evaluator_not_routable`)
  unless the originating spec is tagged `@expect:400`; this prevents
  accidental references to `sc-006..sc-011` evaluator URLs.
- Cross-link: each evaluator response's `audit_id` MUST resolve via
  `/api/audit/list?correlation_id={id}` to a row whose
  `operator_identity.persona_id` equals the request's `persona_id`.

## Production / staging behaviour

Identical to the persona-fixture contract:

- Routes are **not registered** unless the dual-guard activates.
- Reaching the URL in production returns `404 Not Found`; the
  unmounted-router event is logged with `environment=production
  AMA_TEST_SUPPORT=<value>` so post-mortems can confirm the guard fired.
- No IdP changes — OOS-007 still holds.

## Cross-references

- **FR-028 / FR-021** — spec.md (route-only addition; dual-guard activation).
- **FR-002 / FR-009 / FR-010 / FR-029** — workflow-state assertions consume this evaluator.
- **persona-fixture.contract.md** — canonical activation rule (this contract reuses it verbatim).
- **gap-register-entry.schema.json** — `GAP-EVALUATOR-SCENARIO-MISSING` and the additive `cycle_id` field.
- **cycle-metadata.schema.json** — `cycle_start_ts` / `cycle_id` symmetric to the audit-list `cycle=current` filter.
- **data-model.md** — `EvaluatorRequest`, `EvaluatorResponse` (added at cycle-1).
- **research.md** — R-021 (idempotency keying + scenario-id binding), R-022 (audit-list cycle filter), R-024 (env-var canonicalisation).
- **constitution.md §IV** — append-only auditability satisfied by the audit-list endpoint.
