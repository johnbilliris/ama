# ADR-036-010: Cycle 2 Amendment Cycle (Hybrid OTel, Degraded Dispatch, Z6/Z7 SLIs)

**Status**: Accepted
**Deciders**: API Architect, Solution Architect, Observability Engineer, Security Engineer, Compliance Auditor
**Date**: 2026-05-22
**Spec**: 036-sim-agent-extend (Cycle 2 amendments A2-01..A2-08)
**FR coverage**: FR-067 (per-subscriber correlation IDs), FR-068 (signal_pipeline.dispatch_failed envelope), FR-069 (Z6/Z7 SLIs + sample_count), FR-070 (cascade matrix consolidation), FR-048 (allocator-only sequence_number — strengthened)
**Constitution**: I (Primacy of Life — degraded-dispatch transparency), II (AIIMS-aligned outcomes), IV (Transparency and Auditability — byte-equality), VII (Consequence-aware delivery — synthetic smoke gate)
**Related ADRs**: ADR-036-001 (real sub-agent invocation), ADR-036-007 (gap-free sequence allocator), ADR-036-008 (SLI thresholds), ADR-036-009 (idempotency cache)

> **Co-authored-by**: Copilot <223556219+Copilot@users.noreply.github.com>

---

## Context

Cycle 1 of spec-036 closed 🟢 GREEN (final-sweep verdict at `tasks.md:1336`)
with the foundational telemetry-injection orchestrator, gap-free
sequence allocator (ADR-036-007), idempotency cache (ADR-036-009),
five SLIs (Z1..Z5), seven cascade fan-out rules, and 24 audit-envelope
entry types in production-shaped staging.

Cycle 2 opened with eight amendments (A2-01..A2-08) driven by three
operational discoveries during the post-Cycle-1 validation cohort
sweep:

1. **A2-01 / FR-067** — the orchestrator's single-correlation-id
   model could not distinguish per-subscriber dispatch outcomes when a
   fan-out partially failed. Telemetry showed "all-or-nothing"
   correlation that masked the failed subscriber's identity, breaking
   forensic replay.
2. **A2-02 / FR-069** — the five Cycle 1 SLIs lacked sample-floor
   guards. Staging promotion gates were green-lighting on as few as
   three samples per SLI per 24 h, which is statistically meaningless
   at P95 (the dispersion of 3 samples is unbounded under realistic
   load).
3. **A2-04 / FR-068** — the existing 24 audit envelopes had no entry
   for the dispatch-failed scenario. The orchestrator silently swallowed
   asyncio.TimeoutError and per-subscriber exceptions at
   `simulations_036.py:316-345` so investigators had no audit trail.

Five smaller findings (A2-03, A2-05, A2-06, A2-07, A2-08) bundled
collateral cleanups: cascade matrix consolidation, RFC 9457 route
allow-list, allocator-only `sequence_number` strengthening, sub_agent
enum case alignment, and changelog ergonomics.

The combined Cycle 2 task envelope (T-AA07..T-AA22, 16 tasks, 4 waves)
required a single ADR to record the cross-cutting decisions because
the changes interlock — particularly the BREAKING `TelemetryInjectionAck`
shape change (A2-01) and the entry-25 `signal_pipeline.dispatch_failed`
envelope (A2-04) MUST ship together for the degraded-dispatch handler
to be observable.

---

## Decision

Adopt the eight Cycle 2 amendments en bloc and ship them as a single
**OpenAPI v0.2.x → v0.3.0 BREAKING bump** with a six-step migration
recipe documented in `contracts/openapi-changelog.md`. Specifically:

### A2-01 — Hybrid OpenTelemetry propagation + per-subscriber correlation IDs

- **Decision**: Each fan-out subscriber receives its own UUID
  `correlation_id` AND inherits the parent's W3C TraceContext via OTel
  propagation. Both are recorded on the `TriggeredSubAgent` envelope
  inside `TelemetryInjectionAck`.
- **Why hybrid**: pure correlation IDs are stable across log lines but
  lack span-relationship semantics; pure TraceContext loses identity
  if the upstream APIM hop strips `traceparent`. Hybrid gives
  investigators BOTH a deterministic ID for grep AND a span tree for
  Application Insights end-to-end trace view.
- **BREAKING**: `TelemetryInjectionAck.triggered_sub_agents` items
  changed from `string` → `TriggeredSubAgent` object
  `{correlation_id, dispatch_status, sub_agent, trigger_source}`.
  Migration: SDK consumers MUST update destructuring; pre-v0.3.0
  callers receive HTTP 400 from the response-validation middleware.

### A2-02 — Z6 + Z7 SLIs with `sample_count` column

- **Z6**: P95 sub-agent reply latency, partitioned by model
  (`gpt-4o`, `gpt-4o-mini`); thresholds tabulated in
  `contracts/sli-thresholds.md` table-Z6 (gpt-4o ≤ 4 000 ms warn /
  ≤ 5 000 ms breach; gpt-4o-mini ≤ 1 500 ms warn / ≤ 2 000 ms breach).
- **Z7**: map-overlay drift error budget. Inverse semantics — alert
  when `drift_budget_pct < 99.5 %` (NOT > a ceiling). Implemented as
  a special-case branch within `tests/staging_gates.py::assert_sli_thresholds()`.
- **Sample-floor**: NEW constant `MIN_SAMPLES_PER_SLI_24H = 30` in
  `tests/staging_gates.py`. Staging promotion fails closed (raises
  `StagingPromotionRefused`) if any SLI has <30 samples in the 24 h
  window.
- **Why 30**: classical n=30 rule-of-thumb for sample-mean stability.
  Below n=30 the P95 confidence interval spans more than ±10 % of
  the median, which is wider than the worst-case Z3/Z4 tolerances.

### A2-03 — Cascade matrix consolidation

- **Decision**: Remove `fan_out_rules:` from
  `apps/api/app/config/cascade_rules.yaml`; the in-memory
  `CASCADE_MATRIX` (`packages/domain/src/domain/sim_cascade_matrix.py`)
  is the single source of truth.
- **Build-time guard**: NEW contract test
  `tests/contract/test_cascade_yaml_no_fan_out_rules.py` fails the
  build if YAML drift reintroduces `fan_out_rules:`.
- **Round-trip e2e**: NEW test
  `tests/e2e/test_cascade_orchestrator_round_trip.py` walks
  every category, asserts the matrix dispatch set equals the
  PascalCase canonical set, and verifies each cascade completes
  within the FR-043 5 s budget.

### A2-04 — `signal_pipeline.dispatch_failed` audit envelope (entry-25)

- **Decision**: Add the 25th audit-envelope entry type
  `signal_pipeline.dispatch_failed`, written exactly once per
  `injection_correlation_id` from the degraded-dispatch handler.
- **Body-equality (CHK135)**: the `triggered_sub_agents` array on
  the HTTP 202 body and the `details.triggered_sub_agents` array on
  the audit envelope MUST be byte-equal under RFC 8785 JCS. Enforced
  by `tests/contract/test_dispatch_failed_body_audit_byte_equality.py`
  (CHK135 = highest-risk checklist item).
- **Lex ordering**: items are sorted by `sub_agent` (PascalCase)
  ascending so the JCS canonicalisation produces a single
  reproducible byte string.
- **5 s timeout**: per-subscriber dispatch ack deadline is
  `DISPATCH_ACK_TIMEOUT_SECONDS = 5.0` (exported from
  `apps/api/app/services/simulation/dispatch_status.py`).

### A2-05 — `SPEC_036_PROBLEM_JSON_ROUTES` allow-list

- **Decision**: NEW middleware
  `apps/api/app/middleware/spec_036_routes.py` exposing an explicit
  allow-list of routes that emit RFC 9457 problem+json responses on
  4xx AND 5xx. Other routes continue to use the legacy JSON envelope.
- **Why explicit allow-list (not regex)**: prevents accidental
  contamination of non-spec-036 routes and makes the contract test
  trivially complete (5 routes, 5 assertions).

### A2-06 — Allocator-only `sequence_number` (strengthen FR-048)

- **Decision**: Audit writer drops any caller-supplied
  `sequence_number` from the `details` dict and emits a WARNING log.
  The gap-free allocator (ADR-036-007) is the SOLE source of truth.
- **Schema interaction**: Some 25 typed schemas still declare
  `sequence_number: PositiveInt` in their details (e.g.
  `CascadeDepth2RefusedDetails`, `SignalPipelineDispatchFailedDetails`)
  — for those, the allocator-assigned value is injected AFTER
  allocation but BEFORE validation, so the schema continues to
  validate. For schemas that do NOT declare `sequence_number`
  (e.g. `InjectionRefusedDetails`), nothing is injected.
- **Removed**: orchestrator placeholder `"sequence_number": 1`
  literal at `cascade_orchestrator.py:225-235`. The placeholder was
  always overwritten by the allocator but its presence in the
  source code mis-suggested it was the source of truth.

### A2-07 — `sub_agent` enum 7-kebab → 9-PascalCase (with shim)

- **Decision**: New writes use the 9-PascalCase enum
  `{Comms, Evac, Health, Intel, Logistics, Operations, Planning,
  Resource, Risk}` aligning with the cascade matrix; historical
  Cycle 1 writes used 7-kebab-case (`communication`, `evacuation`,
  etc.).
- **Backward-compat shim**: `_KEBAB_TO_PASCAL` mapping in
  `apps/api/app/services/simulation/audit_writer.py` translates
  legacy kebab-case audit rows on read so historical evidence
  remains queryable. Enforced by
  `tests/migration/test_historical_kebab_case_audit_entries_readable.py`.

### A2-08 — `openapi-changelog.md` migration ledger

- **Decision**: NEW `contracts/openapi-changelog.md` documents the
  v0.2.x → v0.3.0 BREAKING migration steps, deprecation notices,
  and SDK update recipes. Future bumps append rows; v0.3.0 is the
  first row.

---

## Alternatives Considered

### A-1: Single correlation ID per dispatch (no per-subscriber)

- **Rejected**: would not satisfy the Cycle 2 amendment-pass-1 Q1
  ruling that per-subscriber outcomes MUST be individually
  identifiable in the audit trail.

### A-2: TraceContext-only (drop UUID correlation IDs)

- **Rejected**: APIM strips `traceparent` on the inbound hop in
  staging tenants where APIM is in pass-through mode, so a
  TraceContext-only design would lose identity on first hop.

### A-3: Sample-floor as runtime config (not constant)

- **Rejected**: would let an operator silently lower the floor and
  promote a build on insufficient samples. Hard-coding 30 in
  `tests/staging_gates.py` keeps the floor under code review and
  PR scrutiny.

### A-4: Add `sample_count` only to KQL (not SLI envelope)

- **Rejected**: KQL-only would not expose the sample count to the
  Bicep alerting pipeline or Azure Monitor workbook. The SLI envelope
  needs the column so workbook visualisations can dim cells with
  <30 samples.

### A-5: Soft-deprecate kebab-case enum (instead of hard switch)

- **Rejected**: would leave both case forms valid for new writes,
  causing JCS canonicalisation drift. The PascalCase → kebab-case
  shim (read-only, on legacy rows) is the minimal compatibility
  surface.

### A-6: Inline ADR notes into `tasks.md` §24 (no separate ADR file)

- **Rejected**: Cycle 2 introduces cross-cutting decisions that
  span four artefacts (spec, plan, contracts, data-model). A
  dedicated ADR is the durable record that survives task-list
  rotation.

---

## Consequences

### Positive

- Forensic replay restored for partial-failure dispatches via
  per-subscriber correlation IDs.
- Statistical floor (`MIN_SAMPLES_PER_SLI_24H = 30`) prevents
  spurious staging promotions on sparse SLI data.
- Audit trail closes the silent-swallow gap at
  `simulations_036.py:316-345` with the entry-25 envelope.
- Cascade fan-out has a single source of truth (matrix-only),
  eliminating YAML/code drift class.
- `openapi-changelog.md` gives SDK consumers a versioned migration
  ledger for future BREAKING changes.

### Negative

- BREAKING bump v0.2.x → v0.3.0 requires SDK consumer updates;
  pre-v0.3.0 callers see HTTP 400.
- ~10 µs additional per-dispatch overhead from per-subscriber UUID
  allocation (negligible at P95 budgets).
- Sample-floor may delay staging promotion in low-traffic test
  environments; mitigated by the synthetic smoke-injection job
  in `staging-promotion.yml` (5 categories × 8 events ≥ 40 floor).

### Neutral

- The `_KEBAB_TO_PASCAL` shim is read-only and adds 7 lines to the
  audit writer; expected to remain in place for the full Cycle 1
  evidence-retention window (12 months under FR-048 retention).

---

## Migration Recipe (cross-reference)

See `contracts/openapi-changelog.md` v0.3.0 row for the full
six-step SDK migration recipe. Summary:

1. Bump pinned `openapi-simulation.yaml` reference to v0.3.0.
2. Update `TelemetryInjectionAck.triggered_sub_agents` consumers:
   `string[]` → `TriggeredSubAgent[]`.
3. Add `dispatch_status` filter to client-side dashboards.
4. Update Application Insights workbooks to consume the new
   `signal_pipeline.dispatch_failed` entry type.
5. If you author audit envelopes directly, switch new writes to
   the 9-PascalCase `sub_agent` enum.
6. Re-run contract tests against v0.3.0 fixtures.

---

## Test Obligations

- Contract: `tests/contract/test_openapi_v030_schema.py` (5
  assertions on the BREAKING shape).
- Contract:
  `tests/contract/test_audit_envelope_entry_25_schema.py` (5
  entry-25 invariants).
- Contract:
  `tests/contract/test_dispatch_failed_body_audit_byte_equality.py`
  (CHK135 — RFC 8785 JCS byte-equality).
- Contract:
  `tests/contract/test_audit_envelope_sub_agent_enum_alignment.py`
  (9-PascalCase enum membership).
- Contract: `tests/contract/test_spec_036_route_allow_list.py`
  (5 routes, 5 assertions).
- Contract: `tests/contract/test_sli_kql_schema_v2.py` (Z6/Z7
  KQL contract + `sample_count` column).
- Contract:
  `tests/contract/test_cascade_yaml_no_fan_out_rules.py`
  (build-time matrix-only guard).
- Migration:
  `tests/migration/test_historical_kebab_case_audit_entries_readable.py`
  (8 assertions on `_KEBAB_TO_PASCAL` shim).
- Integration:
  `tests/integration/test_degraded_dispatch_handler.py`
  (3 outcomes: acknowledged, failed, timed_out).
- Integration: `tests/integration/test_dispatch_failed_idempotency.py`
  (replay = single envelope).
- Integration: `tests/integration/test_forensic_replay.py`
  (per-subscriber correlation_id round-trip).
- Integration:
  `tests/integration/test_assert_sli_thresholds_z6_z7.py`
  (sample-floor + threshold).
- E2E: `tests/e2e/test_cascade_orchestrator_round_trip.py`
  (5 categories × matrix dispatch).
- E2E: `tests/e2e/test_staging_smoke_injection_floor.py`
  (synthetic smoke ≥ 40 events).
- Unit: `tests/unit/test_audit_writer_rejects_caller_sequence_number.py`
  (allocator-only invariant).
- Unit: `tests/unit/test_orchestrator_per_subscriber_correlation_id.py`
  (UUID per subscriber).
- Unit: `tests/unit/test_orchestrator_otel_hybrid_propagation.py`
  (TraceContext + correlation_id co-existence).

---

## References

- Spec FR-067, FR-068, FR-069, FR-070, FR-048
- `specs/036-sim-agent-extend/spec.md` §§ Cycle 2 amendments
  A2-01..A2-08 (lines 86-234), Cycle 2 clarifications Pass-1 Q1..Q5,
  Pass-2 Q1..Q5 (lines 235-685)
- `specs/036-sim-agent-extend/plan.md` §§ C2.1-C2.6
- `specs/036-sim-agent-extend/data-model.md` § 11
- `specs/036-sim-agent-extend/checklists/quality.md` (CHK101..CHK156)
- `specs/036-sim-agent-extend/contracts/audit-envelope.md`
  (entry-25 + sub_agent enum 9-PascalCase)
- `specs/036-sim-agent-extend/contracts/sli-thresholds.md`
  (tables Z6 + Z7)
- `specs/036-sim-agent-extend/contracts/openapi-simulation.yaml`
  (v0.3.0 BREAKING)
- `specs/036-sim-agent-extend/contracts/openapi-changelog.md`
  (v0.3.0 row)
- ADR-036-001, ADR-036-007, ADR-036-008, ADR-036-009
- RFC 8785 — JSON Canonicalisation Scheme (JCS):
  <https://www.rfc-editor.org/rfc/rfc8785>
- W3C TraceContext: <https://www.w3.org/TR/trace-context/>
- RFC 9457 — Problem Details for HTTP APIs:
  <https://www.rfc-editor.org/rfc/rfc9457>
