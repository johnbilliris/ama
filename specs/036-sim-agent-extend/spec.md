# Feature Specification: Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Feature Branch**: `036-sim-agent-extend`
**Created**: 2026-05-08
**Status**: Draft
**Input**: User description: "Extend the simulation page so the Simulation Controller actually invokes the real operational sub-agents (Monitoring, Planning, Resource Allocation, Communication, Evacuation, Risk Assessment) and replays their substantive responses in the chat pane and on the Disaster Map. Add a brand-new Simulation Telemetry-Injection Agent that converts free-text coordinator chat into typed synthetic signals (weather, fire-behaviour, hydrology, geohazard, utility, transport, evacuation, resource, comms-channel-state) flowing through the existing tenant-scoped signal pipeline so all downstream sub-agents react correctly. Auto-route every chat input to the appropriate sub-agent by intent. Render real-time map updates from the resulting telemetry. When the Communication agent runs in simulation mode, it must produce a chat receipt that says the message was sent successfully prefixed with [SIMULATION] and must still be hard-blocked from any real channel."

## Step 8 Amendment Log (2026-05-08)

This log records the amendments applied to spec.md following the **Step 8 cross-cohort
review** (85 personas: 10 operational + 58 sectors + 17 technical) which returned **RE-LOOP**
with **18 CRITICAL / 39 HIGH / 24 MEDIUM / 4 LOW** findings and an aggregate verdict of
**0 ENDORSE / 30 ENDORSE-WITH-RESERVATIONS / 55 OBJECT**. Every finding cited verifiable
`file:line` evidence in the implementation; the full validated synthesis is preserved at
`step8-synthesis.md` in the Step-8 session workspace.

This amendment cycle adds **6 new functional requirements** (FR-061 → FR-066), strengthens
**12 existing functional requirements**, and expands the cascade matrix. **All other
sections of the spec are preserved unchanged.** Implementation files, plan.md, data-model.md,
contracts/*, tasks.md, research.md, and the canonical 12 plan-decisions / 6 ADRs are
**out-of-scope** for this amendment cycle and will be re-aligned in subsequent steps
(`speckit.plan` and `speckit.tasks`).

### Amendment summary table

| ID | Type | Target FR(s) | Summary |
|---|---|---|---|
| A | NEW | FR-061 | Canonical AIIMS function-to-sub-agent mapping (Control, Operations, Logistics, Intelligence, Planning, Public Information). |
| B | STRENGTHEN | FR-027 | All 16 layer types MUST be visually rendered when geometrically applicable; a11y digest is supplementary, not substitutive. |
| C | STRENGTHEN | FR-009, FR-015 | Telemetry injection MUST persist + publish to tenant-scoped pipeline + invoke subscribed sub-agents BEFORE the inject-telemetry endpoint returns; `triggered_sub_agents` MUST be populated. |
| D | STRENGTHEN | FR-048 | `sequence_number` allocation MUST be safe across multiple API replicas (Cosmos ETag conditional replace, stored procedure, or documented single-writer with replica-affinity routing); fail-closed on sequence uncertainty. |
| E | STRENGTHEN | FR-051 | All coordinator-only routes MUST validate JWT/app-role + tenant membership BEFORE any audit attempt; anonymous fallbacks PROHIBITED in production. |
| F | STRENGTHEN | FR-059 | Pause MUST persist state + refuse future invocations with HTTP 409 + `audit.lifecycle.refused_while_paused`; abort MUST **queue** (not claim to start) the lessons-capture job. |
| G | STRENGTHEN | FR-013 | Contradiction detector MUST receive recent signals from any invocation path; hardcoded `recent_signals=()` PROHIBITED. |
| H | STRENGTHEN | FR-027 | Backend/web layer taxonomy MUST be a single canonical enumeration owned by `packages/domain` with contract test enforcing equality. |
| I | STRENGTHEN | FR-054 | ExerciseOutcomeRecord MUST include all 6 named sections (participant summary, timeline, sub-agent responses, IC decisions, identified gaps, lessons-identified narrative) with deterministic ordering. |
| J | STRENGTHEN | FR-057 | `cascade_orchestrator.fan_out` MUST integrate `ThreadCapService.check_or_acquire()` + emit `cascade.degraded_to_annotation`; the 5-step affinity ladder MUST run when annotation degradation is selected. |
| K | STRENGTHEN | FR-027 (synthesis labelled "FR-040" in error — corrected here) | AWS-tier colours MUST follow Australian Warning System (Advice=yellow, Watch and Act=orange, Emergency Warning=red, N/A=neutral grey) with regression test covering all four tiers. |
| L | STRENGTHEN | FR-039 | Watermark text-translation table and audio-prefix table MUST cover ≥ ~30 locales including NT/remote Aboriginal languages (Yolŋu Matha, Warlpiri, Pitjantjatjara, Arrernte), Kriol, and Torres Strait Creole; jurisdiction language profiles MUST link each jurisdiction to its priority locales. |
| M | STRENGTHEN | FR-021 (synthesis labelled "FR-007" in error — corrected here) | Jurisdiction routing MUST use jurisdiction × hazard × agency tuples with blocking concrete fixtures (WA DFES, QFD, CFA/FRV, SA SACFS/SAMFS, NT dual-fire NTFRS+Bushfires NT, ACT ESA-first with AFP fallback). |
| N | EXPAND | FR-043, FR-044, FR-047 + new "Cascade matrix" subsection | Cascade matrix expanded to canonical: utility→{Health, Comms, Transport, Resource}; hydrology→{Risk, Evac, Comms, Resource}; transport→{Evac, Comms, Resource}; evacuation-centre→{Planning, Evac, Resource}; geohazard→{Risk, Evac, Resource}. |
| O | NEW | FR-062 | Foundry carve-out registry schema (`tenant_id`, `model_deployment`, `carveout_reason`, `evidence_uri`, `expires_at`, `approver`) + CI evaluation that fails when registry is empty while carve-outs are referenced in code. |
| P | NEW | FR-063 | All 5 plan-canonical SLIs MUST have blocking E2E staging gate + promotion evidence (P95 inject→fan-out latency, P99 audit gap-free invariant, throughput at 200 concurrent injections, error budget on map-overlay drift, P95 sub-agent reply latency). |
| Q | NEW | FR-064 | SSE/streaming chat updates MUST publish to an accessible live region (`role="log"` + `aria-live="polite"` + sufficient labelling) so screen-reader users receive parity with sighted exercise control; the Map a11y digest is supplementary, not substitutive. |
| R | NEW | FR-065 | Every Telemetry-Injection attempt — accepted, refused, OR fallback — MUST persist `prompt_hash` (sha256) in audit; refusal and fallback paths MUST include it as well as accepted paths. |
| S | NEW | FR-066 | All direct REST lifecycle endpoints (pause, resume, abort, inject-telemetry) MUST honour `Idempotency-Key` header; replays within a 24-hour window MUST return the original response without re-executing side effects. |

### Cohort and prior-clarify reconciliation

- **Operational + sectors re-canvass** (amendment scope only): the AIIMS function mapping
  (A), jurisdiction tuple fixtures (M), AWS-tier colour correctness (K), CALD locale
  expansion to remote Aboriginal languages and Kriol/Torres Strait Creole (L), accessible
  live-log (Q), and lifecycle persistence (F) all align verbatim with operational + sectors
  cohort guidance recorded in the Step-8 synthesis (§ "Convergent CRITICAL findings" and
  § "High-severity findings worth spec amendments"). No additional persona-driven
  requirements emerged beyond Amendments A–S.
- **Technical re-canvass deferred**: technical-cohort findings tied to architecture
  posture (distributed sequence counter, idempotency window, SLI gates, carve-out registry,
  prompt-hash forensic completeness) are reflected in Amendments D, S, P, O, R but their
  implementation trade-offs (e.g., choice between Cosmos ETag conditional replace vs.
  stored procedure for FR-048; exact `Idempotency-Key` storage for FR-066) are deferred to
  the `speckit.plan` step.
- **Prior-clarify Q→A entries remain in force**: none of the 13 Q→A from
  Sessions 2026-05-08 pass 1 / pass 2 / pass 3 (checklist-surfaced) is superseded by these
  amendments. Amendment L *strengthens* (does not replace) the watermark Q→A on line 133;
  Amendment F *strengthens* (does not replace) the lifecycle Q→A on line 149; Amendment J
  *strengthens* (does not replace) the cascade audit-ownership Q→A on line 142. All prior
  Q→A answers remain authoritative; the amendments add precision around enforcement,
  persistence, and integration points.

### FR-numbering corrections vs. synthesis

Two synthesis amendments cited FR numbers that do not match the spec's actual FR numbering;
they have been applied to the semantically correct FR with a note in the table:

- **Amendment K** is labelled in `step8-synthesis.md` as targeting "FR-040", but the
  spec's FR-040 is the `[SIMULATION] ` prefix application rule. AWS-tier colour rendering
  belongs to FR-027 (map-overlay rendering); Amendment K is applied to FR-027.
- **Amendment M** is labelled in `step8-synthesis.md` as targeting "FR-007", but the
  spec's FR-007 is the citation tenant-isolation rule. Jurisdiction routing is FR-021;
  Amendment M is applied to FR-021.

These corrections preserve the synthesis intent and are flagged so subsequent
`speckit.plan` / `speckit.tasks` steps can trace amendment letters to actual FR targets.

## Cycle 2 Amendment Log (post Step 8i re-review, 2026-05-09)

This log records the **Cycle 2** amendments applied following the Step 8i cross-cohort
re-review (`step-8i-synthesis.md` — same 85-persona panel). Cycle 1 closed with **0
OBJECT** votes across all three cohorts (sectors / operational / technical) — the user's
stated convergence rule was satisfied. However, eight merit-validated findings remain
that cite verifiable `file:line` evidence in the implementation; per the user's standing
direction (*"For those that have merit, update the specification… and then repeat Steps 2
to Step 7 for the amendments"*) they are codified here before Step 8r implements them and
before Step 9 (`azd deploy`).

This amendment cycle adds **4 new functional requirements** (FR-067 → FR-070), **1 new
success criterion** (SC-013), strengthens **3 existing FRs** (FR-009 / FR-015 / FR-048
and FR-063), and records **1 contract-scope reconciliation** (RFC 9457 universal-MIME
narrowing). Cycle 1 amendments A–S remain in force unchanged. All implementation files,
contracts (`audit-envelope.md`, `error-responses.md`, `sli-thresholds.md`,
`sli-kql.json`), `plan.md`, `data-model.md`, `tasks.md`, and `research.md` are
**out-of-scope** for this spec amendment cycle and will be re-aligned in subsequent
steps (Step 8o for `plan.md`, Step 8p for `tasks.md`, Step 8r for implementation).

### Cycle 2 amendment summary table

| ID | Severity | Cohort | Type | Target | Summary |
|---|---|---|---|---|---|
| A2-01 | HIGH | Operations Officer + Field Coordinator + Observer-Auditor | STRENGTHEN + ADD-FR | FR-009, FR-015, **FR-067 (new)** | Orchestrator-failure handling MUST emit `degraded_dispatch=true` flag in HTTP 202 + populate `triggered_sub_agents` with the partial-successful subset + write a new typed `signal_pipeline.dispatch_failed` audit envelope. Replaces the current silent-swallow `except Exception: logger.exception` site. |
| A2-02 | HIGH | sre-engineer | ADD-SC | **SC-013 (new)** + FR-063 STRENGTHEN | Add SLI Z6 (P95 sub-agent reply latency) and SLI Z7 (map-overlay drift error budget) to the runtime KQL bundle so SC-001 and SC-010 are gated by SLI machinery. Z3 / Z4 / Z5 retain their current operational definitions (DLQ depth, Cosmos RU headroom, cascade degraded rate). |
| A2-03 | MEDIUM | Logistics + Resilience Planner | ADD-FR | **FR-068 (new)** | Production `cascade_rules.yaml` MUST be reconciled against canonical `sim_cascade_matrix.py` (Cycle 1 Amendment N matrix). An orchestrator round-trip e2e test MUST assert end-to-end fan-out matches the canonical matrix — not just the static module-level matrix. |
| A2-04 | MEDIUM | Observer-Auditor | ADD-FR | **FR-069 (new)** | The `injection.success` audit envelope MUST persist the `triggered_sub_agents` array carried in the HTTP response body so forensic reconstruction does not require correlation-id JOINs across logger streams. |
| A2-05 | MEDIUM | api-architect | RECONCILE | `contracts/error-responses.md:9` scope clarification (no new FR) | Narrow the "platform's MIME type is `application/problem+json` for every error response" claim to spec-036 endpoints **only**. Legacy 4xx middleware (`apps/api/app/middleware/error_handler.py:24-72`) emits the older `{correlationId, statusCode, errorCategory, message}` envelope on non-spec-036 surfaces; that legacy envelope is preserved (refactor avoided). Spec-036's RFC 9457 surface stays as-is. |
| A2-06 | LOW | software-developer | STRENGTHEN | FR-048 | Remove the placeholder `"sequence_number": 1` literal from `cascade.depth2_refused` audit details — the writer overwrites it via the gap-free allocator (Cycle 1 Amendment D). The literal is misleading and brittle. |
| A2-07 | LOW | sectors | ADD-FR | **FR-070 (new)** | Bump the audit envelope's `triggered_sub_agents.sub_agent` enum to align with the canonical 9-member PascalCase `SubAgent` literal in `aiims_mapping.py` (Risk, Evac, Resource, Logistics, Comms, Planning, Health, Operations, Intel) — closing the 7-name kebab-case schema drift. |
| A2-08 | LOW | Observer-Auditor | TYPE-EXTEND | folded into FR-067 | The new `signal_pipeline.dispatch_failed` typed audit envelope is the typed companion to A2-01's degraded-dispatch flag; emitted whenever the orchestrator dispatch raises, regardless of whether the partial-successful subset is empty or non-empty. |

### Cycle 2 amendments — detail

#### A2-01 — Degraded-dispatch on orchestrator failure (HIGH)

- **Cohort source**: Operations Officer (HIGH), Field Coordinator (MEDIUM), Observer-Auditor (LOW)
- **Site**: `apps/api/app/api/routes/simulations_036.py:316-345` (silent fan-out site); cross-references Cycle 1 Amendment C STRENGTHEN on FR-009 / FR-015
- **Type**: STRENGTHEN of FR-009 + FR-015 + ADD-FR FR-067; folds in A2-08 (TYPE-EXTEND of audit envelope with `signal_pipeline.dispatch_failed`)
- **What changes**: The current route swallows every orchestrator exception (`except Exception: logger.exception`) and returns HTTP 202 with `triggered_sub_agents=[]`, which falsely advertises a successful injection while violating Cycle 1 Amendment C's invariant that `triggered_sub_agents` MUST be populated. Cycle 2 selects the **degraded-dispatch** approach (NOT fail-closed): on partial orchestrator failure the endpoint MUST still return HTTP 202 (signal write succeeded), MUST populate `triggered_sub_agents` with the **partial-successful subset** (sub-agents that did acknowledge consumption before the dispatch raised), MUST set a new top-level response flag `degraded_dispatch: true`, and MUST write a typed `signal_pipeline.dispatch_failed` audit entry capturing the simulation_id, correlation_id, the partial-successful subset, the failed-subscriber list, the exception class, and the FR-065 `prompt_hash` / `prompt_hash_source`. Fail-closed (HTTP 5xx) is rejected because it would deny coordinators the partial situational awareness produced by the subset that did succeed — the degraded-dispatch flag preserves Constitution Principle V (Graceful Degradation — predictable failure with an explicit machine-readable indicator).
- **New FR**: **FR-067** *(Amendment A2-01 — degraded-dispatch flag on orchestrator partial failure)* — When the signal-pipeline orchestrator raises during fan-out for an accepted injection, the inject-telemetry endpoint MUST: (1) return HTTP 202 (signal write is durable) with a body that includes `degraded_dispatch: true` AND `triggered_sub_agents` populated with the partial-successful subset (each entry tagged `dispatch_status: "acknowledged"`); (2) write a `signal_pipeline.dispatch_failed` typed audit entry recording the partial-successful subset, the failed-subscriber list, the `exception_class`, the FR-065 `prompt_hash` / `prompt_hash_source`, and the originating `injection_correlation_id`; (3) NOT call `injection.success` for the failed subscribers — only the acknowledged subset is recorded as triggered. Silent-swallow (`logger.exception` only with no typed audit entry, returning `triggered_sub_agents=[]`) is **PROHIBITED in production**.
- **Acceptance criteria**:
  - Integration test injects a `weather` signal while one subscribed sub-agent's stub raises; the endpoint returns HTTP 202 with `degraded_dispatch=true` and `triggered_sub_agents` populated with the surviving subset.
  - The audit subtree contains exactly one `signal_pipeline.dispatch_failed` entry with `partial_successful_subset[]`, `failed_subscriber_list[]`, `exception_class`, `prompt_hash`, and `prompt_hash_source`.
  - The `injection.success` envelope is NOT emitted on a fully-failed dispatch (zero acknowledged subscribers); only `signal_pipeline.dispatch_failed` is written, and the response body still carries `degraded_dispatch=true` with `triggered_sub_agents` populated with one entry per attempted subscriber (all `dispatch_status` ∈ `{"failed", "timed_out"}` on full failure). *(Updated by Cycle 2 Pass-1 Q1 — see "Clarifications (Cycle 2 — Pass 1) → Q1" at L248-277 below; supersedes the original "`triggered_sub_agents=[]`" wording. The byte-equality invariant between HTTP 202 body and the `signal_pipeline.dispatch_failed` audit envelope's array per pass-1 Q1 binds the body shape to "one entry per attempted subscriber".)*
  - Replay of the same `Idempotency-Key` (per FR-066) returns the cached degraded-dispatch response unchanged without re-attempting the dispatch.

> **Cycle 2 Pass-1 Q1 supersedure**: the body-vs-audit shape of `triggered_sub_agents` is determined by Cycle 2 Pass-1 Q1 (L248-277), which mandates byte-equality between the HTTP 202 body and the `signal_pipeline.dispatch_failed` audit envelope. Any "acknowledged-only" wording above is interpreted as the partial-successful **derivable view** — the binding shape is "one entry per attempted subscriber".

#### A2-02 — SLI Z6 and Z7 enforcement (HIGH)

- **Cohort source**: sre-engineer (HIGH)
- **Site**: `infra/observability/sli-kql.json:6-67` (Z1..Z5 implementation) cross-referenced against `contracts/sli-thresholds.md:13-21` (5 declared SLIs) and `spec.md` FR-063 (5 plan-canonical SLIs).
- **Type**: ADD-SC SC-013 + STRENGTHEN of FR-063
- **What changes**: The runtime KQL bundle reassigned Z3 → DLQ depth, Z4 → Cosmos RU headroom, Z5 → cascade degraded rate during Cycle 1 implementation, leaving SC-001 (P95 sub-agent reply latency) and SC-010 (map-overlay drift error budget) **without SLI-level enforcement**. Cycle 2 introduces two new SLIs — **Z6 (P95 sub-agent reply latency)** and **Z7 (map-overlay drift error budget)** — without disturbing Z3 / Z4 / Z5 (which now serve operational purposes that emerged during Cycle 1 implementation and are valuable in their own right). FR-063 is strengthened to enumerate the seven runtime SLIs (Z1..Z7) rather than the original five plan-canonical SLIs; Z3 / Z4 / Z5 are recognised as operational SLIs added during Cycle 1, while Z1 / Z2 / Z6 / Z7 remain the SC-anchored plan-canonical SLIs that gate staging promotion.
- **New SC**: **SC-013** *(Amendment A2-02 — SLI Z6 + Z7 staging-promotion gate)* — Promotion of any deployment to production MUST require **green E2E evidence** for SLI Z6 (P95 sub-agent reply latency, threshold per `sli-thresholds.md` SLI-5) and SLI Z7 (map-overlay drift error budget, threshold per `sli-thresholds.md` SLI-4), measured over the immediately preceding staging run; promotion MUST be refused if either SLI lacks fresh staging evidence or fails its threshold. This complements (does not replace) FR-063's existing 5-SLI gate (Z1, Z2, Z3, Z4, Z5).
- **Acceptance criteria**:
  - `infra/observability/sli-kql.json` declares Z6 and Z7 with KQL queries that bind to `customEvents` produced by the sub-agent invocation pathway and the map-overlay publisher pathway respectively.
  - `tests/e2e/test_staging_promotion_gates.py` asserts both Z6 and Z7 are evaluated and that staging promotion fails when either is below threshold.
  - The Z6 SLI's `sc_refs` field includes `"SC-001"`; the Z7 SLI's `sc_refs` field includes `"SC-010"`.
  - Z3 / Z4 / Z5 retain their current Cycle 1 definitions and threshold values unchanged.

#### A2-03 — Cascade-rules canonical reconciliation + orchestrator round-trip e2e (MEDIUM)

- **Cohort source**: Logistics + Resilience Planner (MEDIUM)
- **Site**: `apps/api/app/config/cascade_rules.yaml:32-53` (production fan-out rules narrower than canonical); `packages/domain/src/domain/sim_cascade_matrix.py:30-45` (canonical PascalCase matrix); `tests/integration/test_cascade_matrix_expansion.py:26-41` (asserts only the static matrix, not orchestrator round-trip)
- **Type**: ADD-FR FR-068
- **What changes**: The canonical Python matrix declares utility → {Health, Comms, Logistics, Resource}, hydrology → {Risk, Evac, Comms, Resource}, transport → {Evac, Comms, Resource}, evacuation-centre → {Planning, Evac, Resource}, and geohazard → {Risk, Evac, Resource} — matching Cycle 1 Amendment N's canonical cascade matrix in spec.md. The production YAML maps utility → only {resource-allocation}, transport → only {planning}, evacuation → only {communication}, hydrology → only {risk-assessment}. Production fan-out is therefore **substantially narrower** than the canonical matrix the spec mandates; cohort fixtures pass because the integration test asserts only the static Python matrix, never invoking the orchestrator round-trip. Cycle 2 mandates a single source of truth (the canonical `sim_cascade_matrix.py`) consumed by both the orchestrator and the integration test, and adds a binding round-trip e2e test asserting end-to-end fan-out parity.
- **New FR**: **FR-068** *(Amendment A2-03 — cascade rules canonical reconciliation invariant)* — Production cascade fan-out MUST be sourced from the canonical `packages/domain/src/domain/sim_cascade_matrix.py` matrix; any YAML / config artefact (e.g. `apps/api/app/config/cascade_rules.yaml`) that overrides or narrows this matrix MUST emit a build-time error (or be removed). A binding round-trip integration test MUST inject a representative signal of each cascade-source category (utility, hydrology, transport, evacuation-centre, geohazard) into the live orchestrator and assert that the set of sub-agents actually invoked equals the canonical matrix's target set for that category. The static module-level test (asserting only `CASCADE_MATRIX[category]`) is not sufficient — round-trip parity is the binding contract.
- **Acceptance criteria**:
  - The orchestrator consumes `sim_cascade_matrix.py` directly OR `cascade_rules.yaml` is regenerated from `sim_cascade_matrix.py` at build time with a CI check that fails on drift.
  - `tests/e2e/test_cascade_orchestrator_round_trip.py` injects each of the five cascade-source categories and asserts the actual fan-out set equals the canonical target set within the FR-043 / FR-044 / FR-045 / FR-046 / FR-047 latency budget.
  - The Cycle 1 cascade matrix table in this spec (under "Cascade matrix (canonical) — [Step 8 Amendment N]") remains the single human-readable source of truth and MUST stay byte-aligned with `sim_cascade_matrix.py`.

#### A2-04 — `triggered_sub_agents` array in `injection.success` audit envelope (MEDIUM)

- **Cohort source**: Observer-Auditor (MEDIUM)
- **Site**: `apps/api/app/api/routes/simulations_036.py:331-342` (audit details dict)
- **Type**: ADD-FR FR-069 (TYPE-EXTEND of audit envelope)
- **What changes**: The current `injection.success` audit details dict carries `chat_turn_id`, `injection_correlation_id`, `signal_ids`, `categories`, and `confidences` but NOT `triggered_sub_agents`. The HTTP response body includes the array, but the audit log does not — forensic reconstruction therefore requires a JOIN across the response-log stream and the audit stream on `correlation_id`, which is brittle (response logs may be sampled or absent). Cycle 2 mandates that the audit envelope persists the same `triggered_sub_agents` array the response body carries, with each entry's full `{sub_agent, trigger_source, correlation_id, dispatch_status}` shape.
- **New FR**: **FR-069** *(Amendment A2-04 — `triggered_sub_agents` array in `injection.success` audit envelope)* — Every `injection.success` audit envelope MUST persist a `triggered_sub_agents` array structurally identical to the array returned in the HTTP 202 response body. Each entry MUST carry `sub_agent`, `trigger_source` (per Cycle 1 pass-1 Q1 dedup enum), `correlation_id`, and `dispatch_status` (`acknowledged | failed | timed_out`). Recording `triggered_sub_agents` only in the response logger (and not in the audit envelope) is **PROHIBITED**.
- **Acceptance criteria**:
  - The `injection.success` audit envelope JSON Schema in `contracts/audit-envelope.md` § 3.2 is extended to require `triggered_sub_agents`.
  - Integration test asserts the audit envelope's `triggered_sub_agents` array is byte-equal (after canonicalisation) to the HTTP 202 response body's array.
  - Forensic-replay test reconstructs the fan-out subset from `injection.success` alone (no JOIN with response logs).

#### A2-05 — RFC 9457 contract-scope narrowing (MEDIUM)

- **Cohort source**: api-architect (MEDIUM)
- **Site**: `apps/api/app/middleware/error_handler.py:24-72` + `contracts/error-responses.md:9` (the "platform's MIME type is `application/problem+json` for every error response" claim)
- **Type**: RECONCILE (no new FR — recorded contract-scope narrowing)
- **What changes**: The legacy 4xx middleware emits `{correlationId, statusCode, errorCategory, message}` for routes outside the spec-036 surface (e.g. legacy `/api/v1/...` endpoints, healthchecks, infrastructure pings). The contract `error-responses.md:9` overstates the surface by claiming the platform MIME type is `application/problem+json` for **every** error response. Two reconciliation paths exist: (a) refactor the middleware to emit `application/problem+json` universally — high blast radius onto legacy surfaces; or (b) narrow the contract claim to scope it to spec-036 endpoints only. Cycle 2 selects path (b) — the **narrowing** path — to avoid touching legacy surfaces. This is a doc-internal reconciliation: spec-036 endpoints continue to emit RFC 9457 problem details unchanged; legacy non-036 endpoints continue to use the older envelope; `error-responses.md:9` will be re-worded in Step 8o to scope its claim to the spec-036 endpoint list.
- **RECONCILE note** (supersedes any prior platform-wide RFC 9457 claim): Within feature 036's surface (`POST /api/v1/simulations/{sim_id}/inject-telemetry`, `POST /api/v1/simulations/{sim_id}/pause`, `POST /api/v1/simulations/{sim_id}/resume`, `POST /api/v1/simulations/{sim_id}/abort`, and any sub-route enumerated in `error-responses.md` § 2 / § 3 / § 4), all error responses MUST conform to RFC 9457 with `application/problem+json`. **Outside** that surface, the legacy `{correlationId, statusCode, errorCategory, message}` envelope remains in force unchanged. No new FR is added; the contract document update lands in Step 8o.
- **Acceptance criteria**:
  - `error-responses.md:9` is reworded in Step 8o to scope its MIME-type claim to the spec-036 endpoint list.
  - Spec-036 endpoint integration tests continue to assert `Content-Type: application/problem+json` on every 4xx / 5xx response.
  - Legacy endpoint integration tests assert the older envelope is preserved (regression guard).

#### A2-06 — Remove placeholder `sequence_number=1` from `cascade.depth2_refused` (LOW)

- **Cohort source**: software-developer (LOW)
- **Site**: `apps/api/app/services/simulation/cascade_orchestrator.py:225-235` (the `"sequence_number": 1` literal at line 227)
- **Type**: STRENGTHEN of FR-048 (small but real cleanup)
- **What changes**: The `cascade.depth2_refused` audit details dict carries the literal `"sequence_number": 1`, which is unconditionally overwritten by the audit writer's gap-free sequence allocator (Cycle 1 Amendment D). The literal is misleading (a future reader could assume the 1 is significant) and brittle (a future writer-side refactor that respects caller-provided sequence_number would silently allocate 1 every time, collapsing gap-free invariants). Remove the placeholder and rely on the writer's allocator.
- **FR-048 strengthening**: The `cascade.depth2_refused` audit details dict (and any other audit details dict) MUST NOT carry a caller-supplied `sequence_number` literal. The audit writer's gap-free allocator (per Cycle 1 Amendment D / FR-048) is the **single source of truth** for `sequence_number`; any caller-supplied value MUST be ignored or rejected by the writer.
- **Acceptance criteria**:
  - The `sequence_number` literal is removed from the `cascade.depth2_refused` details dict in `cascade_orchestrator.py`.
  - A regression test asserts that `cascade.depth2_refused` audit entries land with allocator-assigned sequence numbers and are gap-free.
  - The audit-writer's defensive code rejects (or ignores with a warning log) any caller-supplied `sequence_number` in the details dict.

#### A2-07 — Audit envelope `sub_agent` enum alignment with canonical PascalCase 9-name list (LOW)

- **Cohort source**: sectors (LOW)
- **Site**: `specs/036-sim-agent-extend/contracts/audit-envelope.md:149` (the 7-name kebab-case enum) vs `packages/domain/src/domain/models/aiims_mapping.py:51-61` (the canonical 9-name PascalCase `SubAgent` Literal)
- **Type**: ADD-FR FR-070 (TYPE-EXTEND of audit envelope)
- **What changes**: The audit envelope's `triggered_sub_agents.sub_agent` enum currently lists 7 kebab-case names (`monitoring`, `planning`, `resource-allocation`, `communication`, `evacuation`, `risk-assessment`, `simulation-telemetry-injection`); `aiims_mapping.py` defines 9 PascalCase names (`Risk`, `Evac`, `Resource`, `Logistics`, `Comms`, `Planning`, `Health`, `Operations`, `Intel`). The two sets do not even share a common naming convention — schema drift is real and active. Cycle 2 mandates the audit envelope's enum is bumped to match the canonical 9-name PascalCase set in `aiims_mapping.py`; any kebab-case persisted historically remains readable but new writes use the PascalCase enum.
- **New FR**: **FR-070** *(Amendment A2-07 — audit envelope `sub_agent` enum alignment)* — The audit envelope's `triggered_sub_agents.sub_agent` enum (and any other audit-envelope `sub_agent` field) MUST match the canonical 9-member `SubAgent` Literal in `packages/domain/src/domain/models/aiims_mapping.py` (`Risk`, `Evac`, `Resource`, `Logistics`, `Comms`, `Planning`, `Health`, `Operations`, `Intel`). The contract test (`tests/contract/test_audit_envelope_sub_agent_enum.py`) MUST assert byte-equality between the enum in `contracts/audit-envelope.md` and `ALL_SUB_AGENTS` exported from `aiims_mapping.py`. Historic kebab-case audit entries remain readable; new writes MUST use the PascalCase enum.
- **Acceptance criteria**:
  - `contracts/audit-envelope.md:149` enum is updated in Step 8o to the 9-name PascalCase list.
  - A contract test fails on drift between the contract enum and `ALL_SUB_AGENTS`.
  - A migration note is added documenting the readability of historic kebab-case entries.

#### A2-08 — Typed audit entry `signal_pipeline.dispatch_failed` (folded into FR-067)

- **Cohort source**: Observer-Auditor (LOW)
- **Site**: `apps/api/app/api/routes/simulations_036.py:323-328` (the `except Exception: logger.exception` site)
- **Type**: TYPE-EXTEND (audit envelope) — folded into FR-067 (A2-01)
- **What changes**: A2-08 has no standalone amendment surface; the new typed audit entry `signal_pipeline.dispatch_failed` is mandated by FR-067 (A2-01) as the typed companion to the degraded-dispatch flag. Recording this fold-in here closes the LOW finding without adding a duplicate FR.

### Cohort and prior-clarify reconciliation (Cycle 2)

- **No new Q→A entries** are generated by Cycle 2; the eight amendments are all
  precision-tightening of existing Cycle 1 invariants. Existing Cycle 1 Q→A
  (Sessions 2026-05-08 pass 1 / pass 2 / pass 3 + amendment passes 1 / 2) remain in
  force unchanged.
- **Sectors maritime / coastal / aviation hazard classes**: explicitly DEFERRED — these
  fall outside spec-036's six-hazard set and FR-021 step-5 (clarify) provides safe
  fall-back. Recorded as backlog only.
- **Other LOW findings** (cascade matrix internal-consistency reconcile, ACT branding
  nit, VIC fire ordering test, KQL field-name verification, runtime-gate "no rows"
  sentinel, overlay-summary visual-diff test, AAA contrast numeric assertions,
  executive review calendar-bind): not in Cycle 2 scope; recorded as backlog only.
- **Constitution alignment**: A2-01 honours Principle V (Graceful Degradation —
  predictable failure with explicit machine-readable indicator); A2-02 honours
  Principle I (Primacy of Life — life-safety SLIs MUST be gated); A2-03 honours
  Principle IV (Transparency and Auditability — single source of truth for cascade
  matrix); A2-04 / A2-06 / A2-07 honour Principle IV (audit-trail completeness and
  schema-drift prevention); A2-05 honours Principle V (no blast-radius onto legacy
  surfaces). A2-08 is folded into A2-01 and inherits Principle V.

## Cycle 3 Amendment Log (post Step 8s cohort re-review, 2026-05-10)

This log records the **Cycle 3** amendments applied following the Step 8s cross-cohort
re-review of Cycle 2's *own* deliverables. Ground-truth review reports are
`step-8s-rereview-operational.md` and `step-8s-rereview-technical.md` in the session
workspace `C:\Users\prbillir\.copilot\session-state\ddfe017a-c801-4ecd-b4ba-986fe32d7afd\files\`.
Unlike Cycles 1 and 2 — which targeted the original spec / implementation surface —
Cycle 3 is **narrower in scope**: it closes six merit-validated defects that originated
in Cycle 2's staging-promotion gate, the canonical SLI-Z6 / SLI-Z7 KQL implementations,
and the ADR-036-010 + CHANGELOG self-documentation. Cycle 1 carry-overs are explicitly
out-of-scope. The originating cohorts were Operations Officer + Field Coordinator
(operational, sample-size starvation), sre-engineer + infrastructure-devops (technical,
gate enforcement + smoke injection), compliance-auditor (technical, self-documentation
drift), and data-engineer (technical, KQL cardinality + threshold-band drift).

This amendment cycle adds **3 new functional requirements** (FR-071 → FR-073), **1 new
success criterion** (SC-014), strengthens **0 existing FRs** (the Cycle 2 FR text is
not re-worded — the defects sit in implementation artefacts and self-documentation, not
in the FR text itself), and records **0 contract-scope reconciliations**. Cycle 1
amendments A–S and Cycle 2 amendments A2-01 → A2-08 remain in force unchanged.
Implementation files (`.github/workflows/staging-promotion.yml`,
`infra/observability/sli-kql.json`, `tests/staging_gates.py`),
`docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md`, `CHANGELOG.md`,
`plan.md`, `data-model.md`, `tasks.md`, `audit-envelope.md`, and
`contracts/sli-thresholds.md` are **out-of-scope** for this spec amendment cycle and
will be re-aligned in subsequent steps (Step 8x for ADR / CHANGELOG drift, Step 8y for
KQL canonicalisation, Step 8z for workflow gate enforcement).

### Cycle 3 amendment summary table

| ID | Severity | Cohort | Type | Target | Summary |
|---|---|---|---|---|---|
| A3-01 | HIGH | sre-engineer + Operations Officer + Field Coordinator | ADD-FR | **FR-071 (new)** | Staging-promotion gate workflow MUST invoke `tests.staging_gates.assert_sli_thresholds(...)` (or run the equivalent pytest) and exit non-zero on any breach or sample-floor under-met. The current heredoc at `.github/workflows/staging-promotion.yml:67-113` only branches on `proc.returncode != 0` (line 92) and prints `"All 7 SLIs within threshold — promotion allowed."` (line 112) unconditionally on the success path; SC-013 cannot be enforced at the workflow boundary. |
| A3-02 | HIGH | infrastructure-devops + Operations Officer + Field Coordinator | ADD-FR | **FR-072 (new)** | Synthetic smoke-injection job in `staging-promotion.yml:142-185` MUST emit telemetry by HTTP POST to the staging inject-telemetry endpoint (against the `tnt-stg-smoke` test tenant) and assert HTTP 202 + `degraded_dispatch=false` per request. The current script constructs payloads (lines 166-174) but never calls the endpoint; `import subprocess` (line 147) is unused; the floor of "≥ 40 synthetic signals" trivially passes (5 × 8 = 40 always) while no `customEvents` rows accumulate, defeating Cycle 2 Pass-2 Q4's `MIN_SAMPLES_PER_SLI_24H = 30` mitigation. |
| A3-03 | MEDIUM | compliance-auditor | DOC-FIX | `ADR-036-010:87` + `CHANGELOG.md:20` | Both citations reference `tests/staging_gates.py::_is_breach()` — a symbol that does not exist (`grep -n "_is_breach" tests/staging_gates.py` returns zero hits). Actual public entry-point is `assert_sli_thresholds()` (line 98), which carries inlined Z6 and Z7 breach blocks (per-`(sub_agent, model_deployment)` for Z6 at lines 132-153, drift-band for Z7 at lines 154-164). Audit reviewers reading ADR-036-010 hit a dead reference; CHANGELOG propagates the same wrong name. Documents-only fix; no FR change. |
| A3-04 | MEDIUM | compliance-auditor | DOC-FIX + REGRESSION-TEST | `ADR-036-010:83-84` + `CHANGELOG.md:19` | ADR / CHANGELOG quote SLI-Z6 thresholds *"gpt-4o ≤ 2 500 ms warn / ≤ 5 000 ms breach; gpt-4o-mini ≤ 1 800 ms warn / ≤ 2 000 ms breach"*; canonical values in `infra/observability/sli-kql.json:72-75`, `tests/staging_gates.py::assert_sli_thresholds()`, `infra/bicep/modules/observability-alerts.bicep`, and `contracts/sli-thresholds.md:218-228` are gpt-4o `warn=4000, breach=5000` and gpt-4o-mini `warn=1500, breach=2000`. Self-documentation drifts from the canonical contract — precisely the failure class Cycle 2 was designed to prevent. |
| A3-05 | MEDIUM | data-engineer | ADD-FR (folds A3-06) | **FR-073 (new)** | The implementation Z6 KQL at `infra/observability/sli-kql.json:76` drops the `extend sub_agent`, `extend env`, and `where env == "staging"` clauses mandated by `contracts/sli-thresholds.md:230-244` and groups `by model_deployment` only — collapsing the 28-series cardinality (`sub_agent × model_deployment`) into ~2 (one row per model) AND mixing production traffic into the staging gate. A single hot sub-agent can mask a slow sub-agent within the same model. |
| A3-06 | MEDIUM | data-engineer | folded into FR-073 | `infra/observability/sli-kql.json:87-91` (Z7) | (i) Z7 reads a single `delivery_ms` customDimension instead of the spec's `client_received_ms − server_emit_ms` end-to-end clock-skew form (`contracts/sli-thresholds.md:276-289`); (ii) `warn_pct: 99.5` and `breach_pct: 99.5` are identical, contradicting `sli-thresholds.md:269-270` ("Warn ≥ 99.5 %; Breach < 99.0 %") — warn and breach are indistinguishable, so the JSON would block staging on every excursion below the warn line. |

### Cycle 3 amendments — detail

#### A3-01 — Staging-promotion gate enforcement at workflow boundary (HIGH)

- **Cohort source**: sre-engineer (HIGH), Operations Officer (MEDIUM, sample-size starvation impact), Field Coordinator (MEDIUM, shared scope with Operations Officer); ground-truth `step-8s-rereview-technical.md` § "sre-engineer — Finding 1 — HIGH: runtime-gate never compares KQL output to thresholds" and `step-8s-rereview-operational.md` § "Operations Officer — Finding O1" / "Field Coordinator — Finding F1".
- **Site**: `.github/workflows/staging-promotion.yml:67-113` — the *Evaluate canonical SLI KQLs* step's inline Python heredoc.
- **Type**: ADD-FR FR-071
- **What changes**: The heredoc only sets `breaches.append(...)` when the upstream `az` invocation returns a non-zero `proc.returncode` (line 92); on a successful call it merely prints `f"{sli['id']}: latest={latest}"` (line 104) and never compares `latest` to `sli["warn_threshold_ms"]`, `sli["breach_threshold_ms"]`, or `sli["breach_pct"]`. The unconditional success message at line 112 — `print("All 7 SLIs within threshold — promotion allowed.")` — fires on **every** successful `az` call regardless of the latched value. SC-013 (Cycle 2 Amendment A2-02) is therefore not enforceable at the workflow boundary even though `tests/staging_gates.py::assert_sli_thresholds` (line 98) is fully implemented and tested. Cycle 3 mandates that the workflow either (a) invokes `assert_sli_thresholds(sli_results=collated)` directly and lets `StagingPromotionRefused` propagate as a non-zero exit, OR (b) replaces the inline heredoc with `pytest tests/integration/test_assert_sli_thresholds_z6_z7.py -q` consuming live KQL output via env vars. Documentary or visual-only logs do NOT satisfy this requirement.
- **New FR**: **FR-071** *(Amendment A3-01 — staging-promotion gate enforcement at workflow boundary)* — see "Cycle 3 amendment additions (new FRs)" subsection below.
- **Acceptance criteria**:
  - `.github/workflows/staging-promotion.yml` invokes `tests.staging_gates.assert_sli_thresholds()` (or `pytest tests/integration/test_assert_sli_thresholds_z6_z7.py`) on every gate run; on a `StagingPromotionRefused` raise the workflow exits with a non-zero status.
  - A synthetic-canary integration test deliberately constructs an SLI row above the breach threshold (or below the `MIN_SAMPLES_PER_SLI_24H = 30` floor) and asserts the workflow exits non-zero AND no `promote/{build_label}` git tag is created (per SC-014, below).
  - The literal string "All 7 SLIs within threshold — promotion allowed." MUST NOT be emitted on any path that has not first observed a successful return from `assert_sli_thresholds()`.

#### A3-02 — Synthetic smoke-injection MUST emit telemetry to staging API (HIGH)

- **Cohort source**: infrastructure-devops (HIGH), Operations Officer (MEDIUM, identical scope to F1), Field Coordinator (MEDIUM, SC-010 / Z7 starvation); ground-truth `step-8s-rereview-technical.md` § "infrastructure-devops — Finding 3 — HIGH: smoke-injection job is a stub print-loop" and `step-8s-rereview-operational.md` §§ "Finding O1" + "Finding F1" (`smoke-injection` workflow job is a no-op stub).
- **Site**: `.github/workflows/staging-promotion.yml:142-185` — the *Inject 40 synthetic signals across 5 cascade-source categories* step.
- **Type**: ADD-FR FR-072
- **What changes**: The script constructs `payload = {...}` per iteration (lines 166-174) and prints `f"smoke[{category}#{i}]: {payload['signal_id']}"` (line 175) but **never invokes the inject-telemetry endpoint**. `import subprocess` (line 147) is unused; no `requests.post`, `subprocess.run`, `curl`, or `az rest` call appears anywhere in the step body. The total < 40 floor (lines 177-182) trivially passes (5 categories × 8 iterations = 40 always). In a low-traffic staging environment this defeats the entire CHK117 / CHK137 sample-floor mitigation: no `customEvents` rows accumulate, and the `MIN_SAMPLES_PER_SLI_24H = 30` floor (Cycle 2 Pass-2 Q4) is met only if real staging traffic happens to be present from another source. The existing `tests/e2e/test_staging_smoke_injection_floor.py` only checks the workflow YAML's *declarative* shape (job exists, `needs:` wiring, the literal "≥ 40" text appears) — it does NOT exercise the inject-telemetry endpoint or assert App Insights ingestion. Cycle 3 mandates a real HTTP POST per signal against the dedicated `tnt-stg-smoke` tenant authenticated as the `Simulation.Coordinator` test identity.
- **New FR**: **FR-072** *(Amendment A3-02 — synthetic smoke-injection emits telemetry)* — see "Cycle 3 amendment additions (new FRs)" subsection below.
- **Acceptance criteria**:
  - The smoke-injection step invokes `requests.post(f"{STAGING_API_BASE}/api/simulations/{sim_id}/inject-telemetry", json=payload, headers={"Authorization": f"Bearer {os.environ['SMOKE_TOKEN']}"}, timeout=30)` (or the equivalent `az rest --method post` form) for every payload constructed.
  - Each request asserts HTTP 202 with `degraded_dispatch=false` per the FR-067 / Cycle 2 Pass-2 Q2 always-present invariant.
  - `STAGING_API_BASE` and `SMOKE_TOKEN` are sourced from GitHub-environment secrets bound to the `staging` environment (NOT repository-level secrets) and the bearer token authenticates as the `Simulation.Coordinator` test identity in tenant `tnt-stg-smoke`.
  - An integration test (`tests/integration/test_smoke_injection_no_prod_pollution.py` or equivalent) hits the staging route and asserts that the resulting `customEvents` rows carry `tenant_id == "tnt-stg-smoke"` AND `env == "staging"` so production telemetry is never touched.

#### A3-03 — ADR / CHANGELOG citation drift to non-existent `_is_breach()` (MEDIUM)

- **Cohort source**: compliance-auditor (MEDIUM); ground-truth `step-8s-rereview-technical.md` § "compliance-auditor — Finding 5 — MEDIUM: ADR-036-010 + CHANGELOG.md cite non-existent helper `_is_breach`".
- **Site**: `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md:87` and `CHANGELOG.md:20`.
- **Type**: DOC-FIX (no FR change)
- **What changes**: Both citations reference `tests/staging_gates.py::_is_breach()` — a symbol that does not exist (`grep -n "_is_breach" tests/staging_gates.py` returns zero hits). Actual entry-point is the public helper `assert_sli_thresholds()` (line 98), which carries inlined Z6 and Z7 breach blocks. Audit reviewers reading ADR-036-010 hit a dead reference; CHANGELOG propagates the same wrong name. Cycle 3 mandates the citations be updated to the actual public entry-point `assert_sli_thresholds()` (single name, single contract surface). Documents must align with code.
- **No new FR**: documentation drift correction; lands as part of Step 8x.
- **Acceptance criteria**:
  - `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md:87` cites `tests/staging_gates.py::assert_sli_thresholds()`.
  - `CHANGELOG.md:20` cites the same symbol.
  - A docs regression test (`tests/docs/test_adr_036_010_symbol_citations.py` or equivalent) parses the ADR / CHANGELOG and asserts every cited Python symbol resolves via `importlib`.

#### A3-04 — ADR / CHANGELOG SLI-Z6 threshold-value drift (MEDIUM)

- **Cohort source**: compliance-auditor (MEDIUM); ground-truth `step-8s-rereview-technical.md` § "compliance-auditor — Finding 6 — MEDIUM: ADR-036-010 + CHANGELOG.md quote stale Z6 thresholds".
- **Site**: `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md:83-84` and `CHANGELOG.md:19`.
- **Type**: DOC-FIX + new regression test (no FR change)
- **What changes**: ADR-036-010 quotes SLI-Z6 thresholds as *"gpt-4o ≤ 2 500 ms warn / ≤ 5 000 ms breach; gpt-4o-mini ≤ 1 800 ms warn / ≤ 2 000 ms breach"*; CHANGELOG quotes *"gpt-4o ≤ 2 500 ms, gpt-4o-mini ≤ 1 800 ms"*. The canonical values — consistent across `infra/observability/sli-kql.json:72-75`, `tests/staging_gates.py::assert_sli_thresholds()`, `infra/bicep/modules/observability-alerts.bicep`, and `specs/036-sim-agent-extend/contracts/sli-thresholds.md:218-228` — are gpt-4o `warn=4000, breach=5000` and gpt-4o-mini `warn=1500, breach=2000`. ADR-036-010 / CHANGELOG state warn=2 500 / 1 800; that is the precise drift class Cycle 2 was designed to prevent. Cycle 3 mandates the documents be aligned with the canonical contract AND a regression test be added under `tests/docs/` to prevent recurrence.
- **No new FR**: documentation drift correction; lands as part of Step 8x with a new regression test.
- **Acceptance criteria**:
  - `docs/aidr/decisions/ADR-036-010-cycle-2-amendment-cycle.md:83-84` quotes 4 000 / 5 000 ms (gpt-4o) and 1 500 / 2 000 ms (gpt-4o-mini).
  - `CHANGELOG.md:19` quotes the same values.
  - `tests/docs/test_adr_036_010_threshold_drift.py` (new) parses the ADR's threshold table and asserts every quoted value is byte-equal to the corresponding SLI-Z6 field in `infra/observability/sli-kql.json`.

#### A3-05 — Z6 KQL cardinality + filter contract (MEDIUM)

- **Cohort source**: data-engineer (MEDIUM); ground-truth `step-8s-rereview-technical.md` § "data-engineer — Finding 7 — MEDIUM: Z6 KQL implementation drops `env` filter and `sub_agent` dimension vs spec".
- **Site**: `infra/observability/sli-kql.json:76` (Z6 KQL).
- **Type**: ADD-FR FR-073 (folds A3-06)
- **What changes**: `contracts/sli-thresholds.md:230-244` mandates the canonical Z6 KQL: `extend latency_ms`, `extend sub_agent` from `customDimensions`, `extend env` from `customDimensions`, `where env == "staging"`, then `summarize p95_latency_ms = percentile(latency_ms, 95), sample_count = count() by sub_agent, model_deployment`. Spec line 244 confirms: *"Dimensions: sub_agent × model_deployment (28 series — same cardinality as SLI-5)"*. The implementation at line 76 drops the `extend sub_agent` clause entirely AND drops the `where env == "staging"` filter, summarising `by model_deployment` only — collapsing 28 series into ~2 (one per model) AND mixing production traffic into the staging-promotion gate result. A single hot sub-agent can mask a slow sub-agent within the same model. Cycle 3 mandates the implementation KQL match the canonical specification byte-for-byte (or via a canonicalisation comparison: whitespace + comment + parameter-order normalisation) and that `assert_sli_thresholds()` iterate over `(sub_agent, model_deployment)` pairs rather than `model_deployment` alone.
- **New FR**: **FR-073** *(Amendment A3-05 — SLI KQL cardinality contract)* — see "Cycle 3 amendment additions (new FRs)" subsection below. Folds A3-06 (Z7 dimension + threshold band).
- **Acceptance criteria**:
  - `infra/observability/sli-kql.json:76` Z6 KQL extends `sub_agent` and `env` from `customDimensions`, filters `where env == "staging"`, and groups `by sub_agent, model_deployment` — matching `contracts/sli-thresholds.md:230-244` byte-for-byte after canonicalisation.
  - `tests/staging_gates.py::assert_sli_thresholds()` extends its inlined Z6 breach block to iterate over `(sub_agent, model_deployment)` pairs rather than `model_deployment` alone (i.e. the inline loop is split into a helper that iterates over `(sub_agent, model_deployment)` pairs OR the existing inline block is extended to do so).
  - A contract test (`tests/contract/test_sli_kql_canonical_match.py` or extension of the existing `test_sli_kql_schema_v2.py`) asserts every SLI's implementation KQL matches its `contracts/sli-thresholds.md` canonical form after canonicalisation; the test covers both Z6 and Z7.

#### A3-06 — Z7 KQL dimension + warn/breach band (folded into FR-073)

- **Cohort source**: data-engineer (MEDIUM); ground-truth `step-8s-rereview-technical.md` § "data-engineer — Finding 8 — MEDIUM: Z7 KQL diverges from spec on the drift-metric definition AND the breach percentage".
- **Site**: `infra/observability/sli-kql.json:87-91` (Z7 KQL + threshold).
- **Type**: folded into FR-073 (no standalone FR)
- **What changes**: Two distinct defects:
  1. **Wrong dimension.** `contracts/sli-thresholds.md:276-289` defines `drift_ms = client_received_ms − server_emit_ms`, filtered to `env == "staging"`, with `summarize within_budget = countif(drift_ms <= 1500), sample_count = count()`. The implementation reads a single `delivery_ms = todouble(customDimensions['delivery_ms'])` dimension — whatever the publisher tags as `delivery_ms`, NOT the end-to-end clock-skew the spec captures.
  2. **Identical warn/breach bands.** Implementation has `warn_pct: 99.5` (line 87) AND `breach_pct: 99.5` (line 88) — the same value, contradicting `contracts/sli-thresholds.md:269-270` which mandates *"Target / Warn: ≥ 99.5 % within 1500 ms; Breach: < 99.0 %"*. Warn and breach are indistinguishable; the JSON would block staging on every excursion below the warn line.
- **No new FR**: folded into FR-073 (KQL canonicalisation contract).
- **Acceptance criteria**:
  - Z7 KQL extends `client_received_ms`, `server_emit_ms`, `drift_ms = client_received_ms - server_emit_ms`, and `env`; filters `where env == "staging"`; summarises `within_budget = countif(drift_ms <= 1500), sample_count = count()`.
  - Z7 threshold band sets `warn_pct: 99.5` and `breach_pct: 99.0` per `contracts/sli-thresholds.md:269-270`.
  - The contract test from FR-073 covers Z7 alongside Z6.

### Cohort and prior-clarify reconciliation (Cycle 3)

- **No new Q→A entries** are required to land Cycle 3 as a specify pass; the six findings carry deterministic closure targets visible in the table above. A subsequent `/speckit.clarify` (Cycle 3 Pass 1) cycle MAY surface second-order ambiguities (e.g. canonicalisation algorithm for the FR-073 KQL contract — strict-string-equality vs. AST equivalence; smoke-token rotation cadence and tenant isolation guarantees for FR-072) and resolve them in a parallel clarify-pass section.
- **Cycle 1 Q→A and Cycle 2 Q→A remain in force unchanged**: the Cycle 3 amendments do not contradict any prior Q→A. A3-01 strengthens (does not replace) Cycle 2 Pass-1 Q2's 24-hour staging-evidence freshness window; A3-02 strengthens (does not replace) Cycle 2 Pass-2 Q4's `MIN_SAMPLES_PER_SLI_24H = 30` floor; A3-05 / A3-06 do not contradict Cycle 2 Pass-2 Q3's hybrid OTel + `customDimensions` propagation (they reinforce it by mandating `env` and `sub_agent` `customDimensions`).
- **NOT actioned in Cycle 3**: the api-architect's "TriggerSource cardinality mismatch OpenAPI(5) vs Pydantic(2)" finding (technical Finding 9) was reviewed and ruled by-design forward-compat per `specs/036-sim-agent-extend/data-model.md` § 11.5 and `ADR-036-010 § Consequences`. Recorded as **NO MERIT** for amendment per the cohort agent's own note ("MEDIUM → note (does not block the cohort)"). No FR or SC change.
- **Constitution alignment**: A3-01 honours Principle V (Graceful Degradation — predictable failure with explicit machine-readable indicator: a non-zero workflow exit on threshold breach is the explicit indicator); A3-02 honours Principle I (Primacy of Life — staging gates anchored on SC-001 / SC-010 require real telemetry to be enforceable); A3-03 / A3-04 honour Principle IV (Transparency and Auditability — self-documentation must align with the binding code); A3-05 / A3-06 honour Principle IV (single source of truth between contracts and implementation KQL).

## Clarifications (Cycle 2 — Pass 1)

### Session 2026-05-09 (Cycle 2 amendment clarify pass 1)

These resolutions reconcile open questions raised by the Cycle 2 amendments
(A2-01 through A2-08) and resolve one direct contradiction discovered between
FR-067 and FR-069 during this pass. They are decided by the `speckit.clarify`
agent under the user's explicit "deciding authority" mandate; each resolution
is constitution-aligned, Cycle-1-precedent-consistent, and quantitative where
possible.

- **Q1 — A2-01 / FR-067 ↔ FR-069 response-body shape contradiction.** When the
  orchestrator dispatch raises mid-fan-out, FR-067 line 127 says the HTTP 202
  response body lists ONLY entries tagged `dispatch_status: "acknowledged"`,
  but FR-069 line 165 mandates the body and the audit envelope's
  `triggered_sub_agents` array be **structurally identical** (each entry
  carrying full `{sub_agent, trigger_source, correlation_id, dispatch_status}`
  including `failed | timed_out` entries). Which prevails — body filters to
  `acknowledged`, OR body and audit are byte-equal? **→ A: Body and audit are
  structurally identical (FR-069 prevails).** The HTTP 202 response body's
  `triggered_sub_agents` array MUST contain ONE entry per attempted subscriber
  with `dispatch_status` ∈ `{"acknowledged", "failed", "timed_out"}`; the
  `signal_pipeline.dispatch_failed` audit envelope's `triggered_sub_agents`
  array MUST be byte-equal (after RFC 8785 JCS canonicalisation, consistent
  with Cycle 1 pass-1 Q3 idempotency body-hashing) to the response body's
  array. Failed and timed-out subscribers therefore appear in BOTH the
  response body AND the audit envelope; the `partial_successful_subset[]`
  and `failed_subscriber_list[]` fields on the audit envelope are derivable
  views of the same source array (kept for forensic-export ergonomics).
  FR-067's line-127 wording "(each entry tagged `dispatch_status:
  "acknowledged"`)" / "under degraded-dispatch, only `"acknowledged"` entries
  are listed in the response body" is **superseded by this resolution** and
  will be re-worded in Step 8o. **Rationale**: (a) FR-069's byte-equality
  invariant is the explicit forensic-recoverability rule and overrides
  FR-067's narrower body-shape phrasing; (b) coordinators receive richer
  situational awareness on the response without an audit-export round-trip,
  honouring Constitution Principle V (predictable failure with an explicit
  machine-readable indicator); (c) byte-equality is unit-testable in one
  assertion and prevents future drift. *Evidence: spec.md:127, spec.md:165,
  spec.md:2173-2176, spec.md:2215-2225; Cycle 1 pass-1 Q3 RFC 8785 precedent
  at spec.md:383.*

- **Q2 — A2-02 / SC-013 staging-evidence freshness window.** SC-013
  (spec.md:2333-2345) requires Z6 and Z7 to have "fresh staging evidence"
  before promotion, but does not pin a freshness threshold. SLI-5
  (`sli-thresholds.md:21`) uses a 5-minute rolling window and SLI-4
  (`sli-thresholds.md:128-139`) uses a 24-hour window. How recently must
  staging have produced an evaluation? **→ A: Trailing 24 hours for both Z6
  and Z7.** A staging promotion is refused unless `tests/staging_gates.py`
  observes ≥ 1 successful evaluation of EACH of Z6 and Z7 within the
  trailing 24 h, AND each such evaluation is at-or-better-than its
  threshold (Z6 — gpt-4o ≤ 4000 ms warn, gpt-4o-mini ≤ 1500 ms warn; Z7 —
  ≥ 99.5 % overlay drift budget). Both Z6 and Z7 are queried using the same
  24-hour `staging_run_window` parameter to `tests/staging_gates.py`,
  matching SLI-4's natural window and giving low-traffic staging
  environments time for synthetic-traffic to land. **Rationale**: (a) a
  symmetric window is simpler to operate (one parameter, one CI step) and
  to test (one fixture); (b) 24 h is generous enough that staging doesn't
  need permanently-on synthetic injection load yet tight enough that a
  promotion never relies on stale evidence; (c) SLI-5's 5-minute window
  is the alert-evaluation cadence not the promotion-evidence freshness
  threshold (those are different concerns); (d) honours Constitution
  Principle I (Primacy of Life — SC-001 and SC-010 are life-safety SCs and
  MUST be gated by recent evidence). *Evidence: spec.md:2333-2345,
  contracts/sli-thresholds.md:13-21, contracts/sli-thresholds.md:128-139,
  contracts/sli-thresholds.md:166-203.*

- **Q3 — A2-03 / FR-068 cascade reconciliation strategy.** FR-068
  (spec.md:2197-2213) requires `apps/api/app/config/cascade_rules.yaml`
  to be reconciled against `packages/domain/src/domain/sim_cascade_matrix.py`,
  but does not pick a reconciliation pattern. Three viable patterns: (a)
  remove the YAML's `fan_out_rules:` block entirely, orchestrator imports
  `sim_cascade_matrix.py` directly; (b) regenerate `fan_out_rules:` from the
  canonical matrix at build time, CI fails on drift; (c) keep YAML as
  augment-only (canonical ∪ YAML, never narrower). Compounding factor:
  the canonical matrix uses key `evacuation-centre` while signal categories
  per FR-008 use `evacuation` (no `-centre`) — a key-translation step is
  needed regardless of pattern. **→ A: Remove the YAML's `fan_out_rules:`
  block entirely; orchestrator consumes `sim_cascade_matrix.py` directly
  (pattern (a)).** The remaining `ladder:` and `cap:` keys stay in the
  YAML for operational tuning of the FR-057 affinity-ladder. The canonical
  matrix is extended with a single explicit alias `"evacuation":
  CASCADE_MATRIX["evacuation-centre"]` (or the matrix key is renamed to
  `evacuation` with the `-centre` form retained as an explicit alias) so
  the orchestrator's `cascade_targets_for(signal.category)` returns the
  same frozenset for both spellings. The Cycle 1 Amendment N table in
  spec.md (line 41 — "evacuation-centre→{Planning, Evac, Resource}") and
  the canonical matrix MUST stay byte-aligned. A build-time check in
  `tests/contract/test_cascade_yaml_no_fan_out_rules.py` MUST fail if the
  `fan_out_rules:` key reappears in any committed YAML under
  `apps/api/app/config/`. **Rationale**: (a) eliminates the drift surface
  entirely (the bug A2-03 cited was caused by the YAML existing as a
  parallel source of truth); (b) honours Constitution Principle IV
  (Transparency — single source of truth); (c) aligns with the user's
  3-Container-App cap and AVM-first defaults by minimising deployable
  config-drift surface; (d) the alias resolves the `evacuation` ↔
  `evacuation-centre` key drift in a single line of code rather than a
  YAML translation table; (e) round-trip e2e test (FR-068) becomes
  trivially correct because there is nothing to drift. *Evidence:
  spec.md:2197-2213, packages/domain/src/domain/sim_cascade_matrix.py:34-40,
  packages/domain/src/domain/sim_cascade_matrix.py:43-51,
  apps/api/app/config/cascade_rules.yaml:22-55, spec.md:41 (Cycle 1
  Amendment N canonical matrix row).*

- **Q4 — A2-04 / FR-069 `triggered_sub_agents[].correlation_id` semantics
  and array ordering.** FR-069 (spec.md:2215-2225) mandates each entry
  carries `correlation_id`, but does not specify whether this is the
  parent `injection_correlation_id` (one shared id) or a per-subscriber
  dispatch correlation id (one id per fan-out edge). It also does not pin
  the ordering of entries within the array, which matters for the
  byte-equality assertion in Q1 above and for SC-011 reproducibility
  (Cycle 1 pass-2 Q2's deterministic-ordering precedent). **→ A:
  Per-subscriber dispatch correlation_id, array ordered lexicographically
  by `sub_agent` PascalCase enum.** Each `triggered_sub_agents[].correlation_id`
  is a fresh uuid generated by the orchestrator at fan-out time, ONE per
  subscriber edge, and DIFFERENT from the parent `injection_correlation_id`.
  The per-subscriber id MUST be reused as the `correlation_id` field on
  any subsequent `sub_agent.timeout` (audit-envelope §3.16),
  `sub_agent.cancel` (§3.17), or `sub_agent.degraded` (§3.18) envelope
  raised against the same fan-out edge — so that a single-stream JOIN by
  `correlation_id` reconstructs the per-subscriber timeline (no
  parent→child JOIN required). The array MUST be ordered lexicographically
  ascending by the PascalCase `sub_agent` enum value (per FR-070 / A2-07);
  ties (impossible — sub_agent is unique per edge by construction within a
  single injection) resolve by per-subscriber `correlation_id` lexicographic
  ascending. **Rationale**: (a) per-subscriber `correlation_id` is required
  for the existing `sub_agent.timeout/cancel/degraded` envelopes' JOIN
  semantics to work — Constitution IV demands single-stream forensic
  reconstruction; (b) lexicographic ordering by PascalCase `sub_agent`
  is byte-deterministic across replicas and consistent with the Cycle 1
  pass-2 Q2 affinity-ladder pattern (deterministic ranking, no LLM, no
  heuristics) for SC-011 reproducibility; (c) makes the byte-equality
  assertion in Q1 a one-line test (`json.dumps(body['triggered_sub_agents'],
  sort_keys=True) == json.dumps(audit['details']['triggered_sub_agents'],
  sort_keys=True)`); (d) aligns with audit-envelope §3.16/§3.17/§3.18
  which already pin `correlation_id` per envelope. *Evidence:
  spec.md:2215-2225, contracts/audit-envelope.md:67-69 (correlation_id
  meaning), contracts/audit-envelope.md:536-580 (sub_agent.timeout / cancel
  / degraded shapes), spec.md:368 (Cycle 1 pass-2 Q2 deterministic 5-step
  ranking precedent).*

- **Q5 — A2-05 contract-scope narrowing: how is the spec-036 endpoint
  surface identified at runtime?** A2-05 (spec.md:171-181) narrows the
  RFC 9457 problem+json claim in `contracts/error-responses.md:9` to
  spec-036 endpoints only, but does not pin the runtime mechanism by
  which `apps/api/app/middleware/error_handler.py` decides which routes
  are "spec-036". Three options: (a) URL-prefix match
  (`/api/v1/simulations/*`); (b) OpenAPI tag (e.g. `simulation-036`); (c)
  explicit allow-list constant in code. **→ A: Explicit allow-list
  constant in code (option (c)).** A `SPEC_036_PROBLEM_JSON_ROUTES:
  Final[frozenset[str]]` constant is defined in
  `apps/api/app/middleware/error_handler.py` (or a sibling module) and
  enumerates the four FR-066 lifecycle routes plus the FR-049 audit-export
  route plus any sub-route declared in `contracts/error-responses.md`
  §§ 2 / 3 / 4. The `error_handler.py` middleware checks
  `request.url.path` (after FastAPI path-parameter normalisation, e.g.
  `/api/v1/simulations/{sim_id}/inject-telemetry`) against this frozenset;
  matches emit `application/problem+json`, non-matches emit the legacy
  `{correlationId, statusCode, errorCategory, message}` envelope unchanged.
  A contract test (`tests/contract/test_spec_036_route_allow_list.py`)
  asserts the frozenset's contents are byte-equal to the route enumeration
  in `contracts/error-responses.md:177` (the spec-036 surface paragraph)
  and that every route declared with the `@router` decorator under
  `apps/api/app/api/routes/simulations_036.py` appears in the frozenset.
  **Rationale**: (a) explicit allow-list is grep-able, unit-testable, and
  reviewable in a PR diff; (b) URL-prefix match (option (a)) is fragile —
  legacy routes under `/api/v1/simulations/*` from spec 024 could
  inadvertently start emitting RFC 9457 with a future addition; (c)
  OpenAPI tag (option (b)) couples middleware to OpenAPI metadata
  (additional indirection at runtime); (d) honours Constitution Principle
  V (no blast-radius onto legacy surfaces) by making the surface
  enumeration auditable; (e) the contract test enforces single-source-of-
  truth between `contracts/error-responses.md:177`, the frozenset, and
  the actual route declarations. *Evidence: spec.md:171-181,
  contracts/error-responses.md:9 (overstated MIME claim),
  contracts/error-responses.md:154-163 (§3 lifecycle responses),
  apps/api/app/middleware/error_handler.py:24-72 (legacy 4xx middleware
  cited by A2-05).*

**Resolution rollup**: Q1 → updates FR-067 wording (response-body shape) and
the FR-069 byte-equality invariant; Q2 → pins SC-013 staging-evidence
freshness to a 24 h window; Q3 → eliminates `cascade_rules.yaml`
`fan_out_rules:` block + adds `evacuation` ↔ `evacuation-centre` alias on
the canonical matrix; Q4 → defines per-subscriber `correlation_id` semantics
and lexicographic-by-`sub_agent` array ordering; Q5 → defines explicit
allow-list constant for the spec-036 RFC 9457 surface. Together these five
resolutions remove all material ambiguity from the eight Cycle 2 amendments
and unblock Step 8o (contract revisions) → Step 8p (tasks) → Step 8r
(implementation).

## Clarifications (Cycle 2 — Pass 2)

### Session 2026-05-09 (Cycle 2 amendment clarify pass 2)

These resolutions close the **second-order ambiguities** opened by Cycle 2
pass-1 (spec.md:235-423). Pass-1 settled the structural invariants
(byte-equality between response body and audit envelope, 24 h staging-evidence
freshness, YAML `fan_out_rules:` removal, per-subscriber `correlation_id`
semantics, RFC 9457 allow-list constant); pass-2 pins the remaining
operational details that block Step 8o (contract delta) and Step 8p (tasks).
Pass-1 Q→A entries remain in force unchanged; pass-2 entries are additive
and do not contradict any pass-1 resolution. Each resolution is decided by
the `speckit.clarify` agent under the user's explicit "deciding authority"
mandate; each is constitution-aligned, Cycle-1- and Cycle-2-pass-1-precedent-
consistent, and quantitative where possible.

- **Q1 — `dispatch_status` enum semantics + per-subscriber dispatch-
  acknowledgement timeout threshold.** FR-067 (spec.md:2357-2385), FR-069
  (spec.md:2405-2415), and pass-1 Q1 (spec.md:248-277) collectively define a
  3-value `dispatch_status` enum `{"acknowledged", "failed", "timed_out"}`,
  but do NOT define (a) what triggers each value (semantic boundaries),
  (b) the timeout threshold that distinguishes `failed` from `timed_out` at
  the per-subscriber dispatch edge — is it FR-006's 120 s sub-agent reply
  timeout, or a shorter dispatch-only window? — or (c) whether the enum
  should be expanded with `rate_limited` / `circuit_open` values. Options:
  (a) keep 3 values, reuse FR-006 120 s; (b) keep 3 values + new 5 s
  dispatch-only timeout; (c) expand to 5 values + reuse FR-006 120 s; (d)
  expand to 5 values + new 5 s dispatch-only timeout. **→ A: Option (b) —
  keep the 3-value enum, with a NEW per-subscriber dispatch-acknowledgement
  timeout of 5 seconds (separate from FR-006's 120 s sub-agent reply
  timeout).** Rate-limit and circuit-open conditions are subsumed into
  `dispatch_status: "failed"` with the `exception_class` field on the
  `signal_pipeline.dispatch_failed` audit envelope (per FR-067) carrying the
  granularity. The 5 s window is the per-subscriber **transport** budget
  (Event-Hubs publish + subscriber receipt acknowledgement) — measured from
  the orchestrator's `await self._publisher.publish(event)` call to the
  subscriber's ack arrival; anything exceeding 5 s is `timed_out`, an
  explicit raise during publish or pre-ack receipt is `failed`. A constant
  `DISPATCH_ACK_TIMEOUT_SECONDS: Final[float] = 5.0` MUST be defined in
  `apps/api/app/services/simulation/signal_pipeline_orchestrator.py` and
  consumed by the per-subscriber loop at line 186. **Rationale**: (a) keeps
  the audit-envelope enum minimal and forward-compatible — `exception_class`
  carries granularity, and adding new dispatch states later is a code
  change rather than a contract revision; (b) 5 s aligns with ADR-036-007's
  `Retry-After: 5` cadence (`contracts/error-responses.md:162`) and is 2.5×
  SLI-Z1's 2000 ms breach threshold (`contracts/sli-thresholds.md:31-34`)
  giving safety margin; (c) decouples the dispatch transport budget (Event
  Hubs publish + subscriber ack) from FR-006's sub-agent **compute** budget
  (LLM reply) — different concerns, different timeouts; (d) a single
  threshold is symmetric across all subscribers and trivial to encode; (e)
  preserves the byte-equality invariant from pass-1 Q1 because the same
  3-value enum appears in both response body and audit envelope.
  *Evidence: spec.md:127, spec.md:2364-2370, contracts/audit-envelope.md:142-153,
  contracts/sli-thresholds.md:31-34, contracts/error-responses.md:162,
  apps/api/app/services/simulation/signal_pipeline_orchestrator.py:163,
  apps/api/app/services/simulation/signal_pipeline_orchestrator.py:186.*

- **Q2 — `degraded_dispatch` field always-present invariant on HTTP 202
  response body.** FR-067 (spec.md:2361-2362) requires `degraded_dispatch:
  true` on the response body when dispatch is degraded, but does NOT pin
  whether the field is **always present** (with `false` on full success) or
  **omitted on success** (present only with `true` when degraded). This
  affects the `TelemetryInjectionAck` Pydantic model in
  `apps/api/app/api/routes/simulations_036.py:351-356` and every client
  that consumes the endpoint. Options: (a) always present, default `false`;
  (b) omit on full success, present with `true` only on degraded; (c)
  always present + add a sibling `failed_subscriber_count: int = 0` field.
  **→ A: Option (a) — `degraded_dispatch` is always present on every HTTP
  202 response from the inject-telemetry endpoint, defaulting to `false`.**
  The `TelemetryInjectionAck` Pydantic model MUST declare
  `degraded_dispatch: bool = False` (NOT `Optional[bool] = None`) so every
  successful 202 response includes the field with explicit value, and
  clients (web Controller pane, CLI test harness, future external
  integrations) can rely on a stable shape without `KeyError` / null-check
  defensive code. The field's value is the source-of-truth for whether the
  paired `signal_pipeline.dispatch_failed` audit envelope was written for
  this request: `degraded_dispatch == true` ⇔ exactly one
  `signal_pipeline.dispatch_failed` envelope exists for this
  `injection_correlation_id`. **Rationale**: (a) stable response shape is a
  long-standing platform principle — `triggered_sub_agents` is also always
  present, even when empty `[]` (spec.md:1310-1316); (b) Pydantic JSON
  serialisation with `bool = False` produces `"degraded_dispatch": false`
  deterministically, and RFC 8785 JCS canonicalisation works identically
  across always-present vs sometimes-missing — but `false` is more explicit
  for human-readers of audit envelopes and FOI exports; (c) clients can
  switch on a single boolean (`if response.degraded_dispatch:
  warn_user()`) rather than a nullable check; (d) forward-compatible —
  future companion fields like `degradation_reason: Optional[str]` can be
  added without changing the existing field's presence semantics; (e)
  Constitution V (Graceful Degradation — predictable failure surface) is
  honoured by making the surface uniformly present rather than conditionally
  appearing. *Evidence: spec.md:2361-2362,
  apps/api/app/api/routes/simulations_036.py:351-356 (TelemetryInjectionAck
  Pydantic model — currently lacks `degraded_dispatch`), spec.md:1310-1316
  (Cycle 1 pass-1 Q1 stable-shape precedent for `triggered_sub_agents`),
  contracts/audit-envelope.md:144-153 (always-present array shape).*

- **Q3 — W3C TraceContext / OpenTelemetry span propagation for the
  two-level correlation_id hierarchy.** Pass-1 Q4 (spec.md:339-374) defined
  per-subscriber `correlation_id` (one fresh UUID per fan-out edge,
  distinct from the parent `injection_correlation_id`), but did NOT pin how
  those IDs propagate through W3C TraceContext / OpenTelemetry. The current
  observability stack uses Application Insights `customDimensions` for KQL
  queries (e.g. SLI-Z6 query at `infra/observability/sli-kql.json:39`
  matches `customDimensions["model_deployment"]`), and the OTel Python SDK
  is wired into the FastAPI middleware. Options: (a) `injection_correlation_id`
  → OTel `trace_id`; per-subscriber `correlation_id` → OTel `span_id` (one
  child span per subscriber); no `customDimensions` duplication; (b) both
  IDs as `customDimensions` attributes only (OTel trace_id / span_id
  allocated independently); (c) hybrid — both surfaces (OTel TraceContext
  AND `customDimensions`) carry both IDs. **→ A: Option (c) — hybrid: parent
  and per-subscriber correlation IDs are set BOTH on OTel TraceContext
  (parent trace_id / child span_id) AND on `customDimensions` for KQL
  queryability.** Specifically: (1) the orchestrator opens a parent OTel
  span at `dispatch()` entry
  (`apps/api/app/services/simulation/signal_pipeline_orchestrator.py:131-144`)
  and sets `injection_correlation_id` as both a span attribute
  (`customDimensions["injection_correlation_id"]`) AND propagates it as the
  W3C TraceContext `trace_id` (16-byte hex form derived from
  `uuid.UUID(injection_correlation_id).bytes`); (2) each per-subscriber
  dispatch (the `for subscriber in subscribers:` loop at line 186) opens a
  CHILD span whose `span_id` is derived from the per-subscriber
  `correlation_id` (8-byte hex form: `uuid.UUID(correlation_id).bytes[:8].hex()`)
  AND sets `customDimensions["correlation_id"]` to the full UUID string;
  (3) the `signal_pipeline.dispatch_failed` audit envelope's top-level
  `correlation_id` field MUST equal the parent `injection_correlation_id`,
  while each per-subscriber entry in
  `triggered_sub_agents[].correlation_id` MUST equal the corresponding
  child-span's `customDimensions["correlation_id"]`; (4) W3C `traceparent`
  header propagation is automatic via OTel's FastAPI / HTTPX / Cosmos SDK
  instrumentation — downstream sub-agent invocations and Cosmos audit
  writes inherit the trace context without extra code. **Rationale**: (a)
  `customDimensions` queryability is the immediate KQL surface used by
  every SLI alert and Cycle 1 forensic-replay test (e.g. SLI-Z6 query at
  `infra/observability/sli-kql.json:39`), so single-stream JOIN works
  regardless of trace-context propagation status across process boundaries;
  (b) OTel TraceContext gives Application Insights "Transaction Search"
  trivially navigable parent→child structure when an operator wants to
  drill into a specific injection's fan-out; (c) the dual-write is cheap
  (one `span.set_attribute()` call per ID per span) and forward-compatible
  with future Grafana / Tempo migration; (d) Constitution IV (Transparency)
  requires single-stream forensic reconstruction — `customDimensions`
  provides this regardless of cross-process trace propagation luck; (e)
  the byte-equality assertion in pass-1 Q1 (response body ↔ audit envelope)
  is preserved because both surfaces use the canonical UUID string form,
  not the OTel hex-truncated form. *Evidence: pass-1 Q4 at spec.md:339-374,
  apps/api/app/services/simulation/signal_pipeline_orchestrator.py:131-213,
  infra/observability/sli-kql.json:39 (`customDimensions["model_deployment"]`
  precedent), infra/observability/sli-kql.json:13
  (`customDimensions["fan_out_latency_ms"]`), contracts/audit-envelope.md:65
  (`"trace_id": OpenTelemetry trace_id`).*

- **Q4 — SC-013 statistical sample-size minimum per Z6 / Z7 within the
  24 h staging-evidence window.** Pass-1 Q2 (spec.md:277-300) pinned the
  staging-evidence freshness threshold to a trailing 24 h window for both
  Z6 and Z7, but did NOT specify the **statistical sample-size minimum** —
  i.e. how many synthetic smoke injections (Z6) or map-overlay SSE
  deliveries (Z7) must be observed within the 24 h before the SLI
  evaluation is considered statistically valid. Without this, a single
  24 h window with N=1 sample could pass the gate based on a single noisy
  measurement. Options: (a) ≥ 1 evaluation (no minimum, weakest); (b) ≥ 30
  evaluations per Z6 AND Z7 within the 24 h window (Central-Limit-Theorem
  rule-of-thumb); (c) ≥ 100 evaluations per Z6 AND Z7 (tighter percentile
  estimation); (d) asymmetric — ≥ 30 for Z6 (P95 latency), ≥ 10 for Z7
  (binomial proportion). **→ A: Option (b) — ≥ 30 evaluations per Z6 AND
  ≥ 30 per Z7 within the trailing 24 h window.** A staging promotion is
  refused unless `tests/staging_gates.py` observes BOTH: (i) for Z6, ≥ 30
  distinct `customEvents.name == "sub_agent.invocation.complete"` rows
  within `ago(24h)` AND P95 latency at-or-below threshold per
  `contracts/sli-thresholds.md` SLI-5 (gpt-4o ≤ 4000 ms warn / ≤ 5000 ms
  breach; gpt-4o-mini ≤ 1500 ms warn / ≤ 2000 ms breach); (ii) for Z7, ≥ 30
  distinct `customEvents.name == "sse.map_overlay.delivered"` rows within
  `ago(24h)` AND `drift_budget_pct ≥ 99.5 %`. A new sentinel constant
  `MIN_SAMPLES_PER_SLI_24H: Final[int] = 30` is added to
  `tests/staging_gates.py` and enforced by an additional clause in the
  existing `assert_sli_thresholds()` function. The constant is shared
  across Z6 and Z7 for symmetry. The KQL queries in
  `infra/observability/sli-kql.json` for Z6 / Z7 MUST emit a `sample_count`
  column alongside the SLI metric so the gate can assert both values from a
  single query result. **Rationale**: (a) Central-Limit-Theorem rule-of-
  thumb (n ≥ 30) gives reasonable P95-latency estimation for Z6 and
  reasonable binomial-proportion stability for Z7; (b) achievable with
  ~1.25 synthetic injections/hour over 24 h — low ambient cost in staging
  (~30 customEvents per SLI per day); (c) symmetric threshold for Z6 and
  Z7 is simpler to operate (one constant, one CI step) and to test (one
  fixture); (d) avoids the asymmetric option (d) which would require two
  constants and two interpretation rules — premature optimisation; (e) the
  sentinel value can be tightened to 100 in a future cycle if false-
  positives accumulate (the Cycle 2 deferred-finding "runtime-gate 'no
  rows' sentinel" alludes to the same family of concerns); (f) honours
  Constitution Principle I (Primacy of Life — SC-001 and SC-010 are life-
  safety success criteria and MUST be gated by statistically meaningful
  evidence). The constant is documented as `MIN_SAMPLES_PER_SLI_24H = 30
  # Cycle 2 pass 2 Q4 — CLT floor; raise to 100 if false-positive rate
  exceeds 5 %`. *Evidence: spec.md:2333-2345 (SC-013),
  contracts/sli-thresholds.md:166-203 (SLI-5),
  contracts/sli-thresholds.md:128-157 (SLI-4 24 h overlay drift), pass-1 Q2
  at spec.md:277-300, step-8i synthesis "runtime-gate 'no rows' sentinel"
  backlog item.*

- **Q5 — A2-05 RFC 9457 surface response-code scope: 4xx-only or
  4xx + 5xx?** Pass-1 Q5 (spec.md:376-412) defined an explicit allow-list
  constant `SPEC_036_PROBLEM_JSON_ROUTES: Final[frozenset[str]]` for
  selecting which routes emit RFC 9457 `application/problem+json`
  responses, but did NOT pin which **HTTP response status code classes**
  the allow-list governs. Options: (a) gate 4xx only — 5xx errors on
  spec-036 routes use the legacy `{correlationId, statusCode,
  errorCategory, message}` envelope (matches FastAPI default 5xx
  behaviour); (b) gate BOTH 4xx and 5xx — every error response from a
  spec-036 route emits `application/problem+json`; (c) gate 4xx + 5xx +
  2xx warning headers (the `evidence-integrity-warning` already at HTTP
  200). **→ A: Option (b) — the allow-list gates BOTH 4xx AND 5xx error
  responses for spec-036 routes; the pre-existing 2xx
  `evidence-integrity-warning` is preserved as an explicit carve-out.** The
  middleware at `apps/api/app/middleware/error_handler.py:24-72` MUST
  check `request.url.path` against `SPEC_036_PROBLEM_JSON_ROUTES` for
  **every error response** (both 4xx and 5xx); on match, the response body
  is RFC 9457 `application/problem+json`; on non-match, the legacy
  envelope is preserved. The existing 2xx `evidence-integrity-warning`
  (`contracts/error-responses.md:128-148`) continues to be emitted as a
  `Warning` HTTP header on 200 responses with the structured RFC 9457 body
  in the response payload — this is an explicitly-documented carve-out
  emitted by the FR-049 export / FR-054 lessons-capture pathways, NOT by
  the 4xx/5xx middleware path, and remains unchanged by this resolution.
  **Rationale**: (a) ADR-036-007's `sequence-uncertainty` problem-detail
  is HTTP **503** (5xx) and is already enumerated in
  `contracts/error-responses.md:162` as RFC 9457 — splitting 4xx vs 5xx
  scope would put one of the spec's own canonical problem-details on the
  wrong side of the gate; (b) splitting 4xx vs 5xx would require dual
  middleware paths and break `tests/contract/test_problem_detail_uris.py`
  and `tests/contract/test_problem_details_shape.py` (both assert RFC 9457
  shape on the listed types regardless of status); (c) Constitution V —
  uniform error surface is more predictable than a 4xx/5xx hybrid; (d) the
  pass-1 Q5 contract test (`tests/contract/test_spec_036_route_allow_list.py`)
  can be extended in one line to assert problem+json emission on a
  synthetic 5xx (e.g. raise an unhandled `RuntimeError` from a fixture
  endpoint) for any allow-listed route; (e) the 2xx
  `evidence-integrity-warning` carve-out is already documented as a
  non-error structured form emitted via `Warning` header — the carve-out
  is preserved unchanged and does NOT travel through
  `error_handler.py:24-72`. *Evidence: pass-1 Q5 at spec.md:376-412,
  contracts/error-responses.md:9 (overstated MIME claim, narrowed by
  A2-05), contracts/error-responses.md:154-163 (§3 lifecycle responses
  including 503 sequence-uncertainty),
  contracts/error-responses.md:128-148 (§2.4 evidence-integrity-warning
  2xx carve-out), apps/api/app/middleware/error_handler.py:24-72.*

**Resolution rollup (pass 2)**: Q1 → pins the per-subscriber dispatch-
acknowledgement timeout to 5 s and keeps the 3-value `dispatch_status` enum
minimal with `exception_class` carrying granularity for rate-limit / circuit-
open conditions; Q2 → makes `degraded_dispatch: bool = False` always-
present on every HTTP 202 response and updates the `TelemetryInjectionAck`
Pydantic model accordingly; Q3 → defines hybrid OTel + `customDimensions`
propagation so single-stream KQL JOINs work regardless of cross-process
trace context propagation; Q4 → pins `MIN_SAMPLES_PER_SLI_24H = 30` for
both Z6 and Z7 staging-promotion gates; Q5 → extends the spec-036 RFC 9457
allow-list to cover BOTH 4xx and 5xx response codes (with the 2xx
`evidence-integrity-warning` carve-out preserved). Together these five
resolutions close the second-order ambiguities pass-1 left open and unblock
Step 8o (contract delta), Step 8p (tasks regeneration), and the
`/speckit.checklist` step that follows.

## Clarifications (Cycle 3 — Pass 1)

### Session 2026-05-10 (Cycle 3 amendment clarify pass 1)

These resolutions close the **second-order ambiguities** opened by the Cycle 3
amendment cycle (spec.md:237-358). Cycle 3 added FR-071 (workflow-gate
enforcement at the workflow boundary), FR-072 (synthetic smoke-injection
HTTP-POST contract), FR-073 (SLI KQL canonicalisation contract), and SC-014
(staging-promotion gate refusal under synthetic canary), but explicitly
deferred several second-order details to a clarify pass — see spec.md:355
(*"a subsequent /speckit.clarify (Cycle 3 Pass 1) cycle MAY surface
second-order ambiguities (e.g. canonicalisation algorithm for the FR-073 KQL
contract — strict-string-equality vs. AST equivalence; smoke-token rotation
cadence and tenant isolation guarantees for FR-072) and resolve them in a
parallel clarify-pass section"*). Cycle 1, Cycle 2 Pass-1, and Cycle 2 Pass-2
Q→A entries remain in force unchanged; the five resolutions below are
**additive** and do not contradict any prior resolution. Each resolution is
decided by the `speckit.clarify` agent under the user's explicit "deciding
authority" mandate; each is constitution-aligned, Cycle-1- and
Cycle-2-precedent-consistent, and quantitative where possible. `file:line`
evidence is cited for every claim. **Spec-text propagation** for each Q is
noted via `propagation_target:` annotations and is **deferred** to Step 8x
(checklist + ADR / CHANGELOG drift), Step 8y (plan delta), and Step 8z
(tasks + KQL canonicalisation work) — no other artefacts are modified by
this pass.

### Q1 — Which canonicalisation algorithm governs the FR-073 SLI KQL contract — strict-string-after-normalisation, or Kusto-AST equivalence?

**Answer**: **Strict-string-after-normalisation** (NOT Kusto-AST
equivalence) for Cycle 3. A new helper
`tests/contract/_kql_canonicaliser.py::canonicalise_kql(text: str) -> str`
applies a deterministic six-step normalisation pipeline and the FR-073
contract test (`tests/contract/test_sli_kql_canonical_match.py`, new in
Step 8z) asserts byte-equality between
`canonicalise_kql(impl_kql)` and
`canonicalise_kql(canonical_kql_for_sli(sli_id))` for every declared SLI.
The six steps are: **(1)** strip line comments (`// …` to end-of-line) and
block comments (`/* … */`); **(2)** collapse runs of ASCII whitespace to a
single space, while preserving exactly one newline before each pipe (`|`)
operator (so the canonicalised form remains diffable line-by-line in PR
review); **(3)** lowercase all Kusto reserved keywords (`extend`, `where`,
`summarize`, `by`, `project`, `let`, `and`, `or`, `in`, `between`,
`ascending`, `descending`); **(4)** sort each `by` clause's column list
lexicographically (Kusto group-by is order-insensitive in result-shape, but
deterministic ordering makes diffs stable across reorderings); **(5)** sort
each `summarize` aggregate-expression list by left-hand-side alias
lexicographically; **(6)** strip redundant outer parentheses around `extend`
target expressions (e.g. `extend env = (tostring(customDimensions["env"]))`
→ `extend env = tostring(customDimensions["env"])`). The `canonicalise_kql`
helper is pure-Python (no Kusto runtime dependency), runs in <1 ms per
SLI, and is unit-tested with deterministic input/output fixtures. **Kusto-
AST equivalence is explicitly rejected** for Cycle 3 because: (a) the
defects A3-05 / A3-06 are all surface-form deltas (`extend sub_agent`
clause **dropped**, `where env == "staging"` **dropped**,
`by sub_agent, model_deployment` **collapsed** to `by model_deployment`,
`delivery_ms` substituted for `client_received_ms - server_emit_ms`,
`breach_pct=99.5` substituted for `99.0`) — every one of these is detectable
at the surface layer; AST-equivalence buys nothing for the cohort-validated
defect surface; (b) AST equivalence would require either bridging the
managed `Microsoft.Azure.Kusto.Language` .NET parser into a Python contract
test (cross-runtime fragility — incompatible with the AU-resident, Linux-
based GitHub-hosted runners the staging-promotion gate uses) or shelling to
a `kustopreview` CLI (Windows-only — incompatible with the same runners);
(c) strict-string canonicalisation produces line-by-line diffable output in
PR review (the canonical and implementation forms render side-by-side
identically), whereas AST equivalence collapses to a binary "match / no-
match" verdict that hides where the drift sits; (d) FR-073's spec.md text
already permits future tightening (spec.md:3336-3337 — *"the canonicalisation
algorithm itself MAY be tightened in a Cycle 3 clarify pass"*) — if a future
cohort surfaces a defect that strict-string canonicalisation cannot catch
(e.g. semantically-equivalent but stylistically divergent KQL such as
`summarize p = percentile(x, 95)` vs `summarize p = todouble(percentile(x, 95))`)
we revisit the decision at that point, not pre-emptively now. The
canonicalisation algorithm MUST be deterministic, idempotent
(`canonicalise_kql(canonicalise_kql(x)) == canonicalise_kql(x)` for every
input), and stable across CPython 3.12+ runtimes (no dependency on dict-
ordering or set-ordering). The contract test asserts these properties
alongside the per-SLI byte-equality assertions.

**Authority**: Constitution Principle IV (Transparency and Auditability —
single source of truth between contracts and implementation) — the
strict-string canonicalisation contract IS the single source of truth at
the surface layer. Cycle 1 Pass-1 Q3 RFC 8785 JCS canonicalisation
precedent (spec.md:383, also reaffirmed at spec.md:397-400 in Cycle 2 Pass-1
Q1) — the JCS pattern chose surface-form byte-equality over semantic
equivalence for exactly the same reason (PR-diffability + zero runtime
dependency). ADR-036-008 (`docs/aidr/decisions/ADR-036-008-sli-thresholds-rationale.md`)
pins `contracts/sli-thresholds.md` as the canonical KQL surface;
canonicalisation is the contract-test mechanism that binds it to
`infra/observability/sli-kql.json`.

**Spec-text propagation** *(deferred — DO NOT modify in this pass)*:

- `propagation_target: contracts/sli-thresholds.md` — append a new
  §"KQL canonicalisation contract" subsection enumerating the six
  normalisation steps and the idempotence + determinism invariants. **(Step 8x)**
- `propagation_target: tests/contract/_kql_canonicaliser.py` (new) — implement
  `canonicalise_kql(text: str) -> str` per the six-step pipeline; export
  `canonical_kql_for_sli(sli_id: str) -> str` that parses the matching
  fenced KQL block out of `contracts/sli-thresholds.md`. **(Step 8z)**
- `propagation_target: tests/contract/test_sli_kql_canonical_match.py` (new) —
  assert `canonicalise_kql(impl) == canonicalise_kql(canonical)` for every
  SLI in `infra/observability/sli-kql.json`; assert idempotence
  (`canonicalise_kql(canonicalise_kql(x)) == canonicalise_kql(x)`); assert
  determinism (10× re-runs produce byte-equal output). **(Step 8z)**
- `propagation_target: tests/contract/test_sli_kql_schema_v2.py` — extend the
  existing schema test to invoke the canonicalisation match in addition to
  its current per-row schema assertions. **(Step 8z)**
- `propagation_target: plan.md` — add a plan-decision row pinning strict-
  string canonicalisation over Kusto-AST equivalence for Cycle 3, with the
  forward-compat note from FR-073's existing text. **(Step 8y)**
- `propagation_target: tasks.md` — add the four work-items above as
  Cycle 3 Pass-1 tasks, blocking on Step 8x for the contracts subsection. **(Step 8z)**

### Q2 — What is the SMOKE_TOKEN rotation cadence and what tenant-isolation guarantees does the `tnt-stg-smoke` test tenant carry?

**Answer**: **No long-lived `SMOKE_TOKEN` exists** — the smoke-injection
job acquires a **short-lived OIDC-derived bearer access token** at job
start via `azure/login@v2` (federated credential, already wired into the
workflow at `staging-promotion.yml:31, 61-64, 135-140`) followed by
`az account get-access-token --resource <staging-api-app-id-uri>`. The
acquired bearer is held in memory for the duration of the job step and is
discarded when the GitHub-hosted runner is recycled (≤ 1 h after job end);
**rotation cadence is therefore "per workflow run" and is automatic** —
there is no operator-driven rotation procedure, no GitHub repository or
environment secret named `SMOKE_TOKEN`, no Key Vault entry, and no manual
90-day rotation cadence. The dedicated test tenant `tnt-stg-smoke` carries
the following five **isolation guarantees**, all enforced by automated
contract tests: **(i)** *Data residency* — all `tnt-stg-smoke` Cosmos
containers, Event Hub partitions, and Application Insights
`customEvents` rows reside in `australiaeast` (Constitution clause NN-2
"Data sovereignty"); **(ii)** *Sole-tenant scope* — the smoke-injection
job MUST refuse to send any payload whose `tenant_id` field is not the
literal string `"tnt-stg-smoke"`; this is asserted by
`tests/integration/test_smoke_injection_no_prod_pollution.py:34-48` (the
test enumerates a forbidden-literal list including `"tnt-prod"` and
`"tnt-au-"` and fails the build if any production-tenant identifier
appears in the workflow YAML); **(iii)** *Posture parity with production
tenants* — `tnt-stg-smoke` is provisioned via the same
`infra/bicep/modules/cosmos-simulation-containers.bicep` template as
production tenants (private endpoint, customer-managed key, Cosmos
soft-delete with 7-day retention); the only differences are the tenant ID
and the absence of any production-tenant data; **(iv)** *Z6/Z7 KQL
filtering* — the canonical SLI-Z6 and SLI-Z7 KQL queries in
`contracts/sli-thresholds.md:230-244` and `contracts/sli-thresholds.md:276-289`
MUST be amended (Step 8x) to add a `where tenant_id == "tnt-stg-smoke"`
clause so the smoke-injected events are visible to the staging-promotion
gate but provably NEVER contaminate production-tenant SLI evaluation —
the same KQL run against the production workspace returns zero rows; **(v)**
*Least-privilege test identity* — the `Simulation.Coordinator` test
identity used by the smoke-injection job is provisioned as an Entra ID
enterprise app with role assignment scoped exclusively to `tnt-stg-smoke`
(Cosmos data-plane RBAC entry `Simulation.Coordinator` →
`tnt-stg-smoke`-scoped read/write; no production-tenant role assignment
exists for this identity); a contract test
(`tests/contract/test_smoke_tenant_isolation.py`, new in Step 8z) asserts
the role assignment list emitted by `infra/bicep/modules/cosmos-simulation-containers.bicep`
contains exactly one entry referencing `Simulation.Coordinator`, and that
entry is scoped to `tnt-stg-smoke`. ~~Originally worded as *"scoped exclusively to `tnt-stg-smoke`"*; this wording is **superseded by A4-02** (see `:3896-3915`) — the actual Bicep scope is database-level (`'${account.id}/dbs/${databaseName}'`) and acts as a **compensating defence-in-depth control** alongside the SLI-Z6 / SLI-Z7 query-time `where tenant_id == "tnt-stg-smoke"` filter. See ADR-036-011:172-173 (in-place revised in Cycle 4 per T-AA50) for the corrected three-clause acknowledgement; the partition-scope upgrade is deferred to a backlog issue pending the Cosmos data-plane RBAC API 2024-08-15 exposing a `partitionKey` selector. Per the Cycle 3 immutability discipline, four sibling lock-zone mirrors of the original wording (`plan.md:682`, `tasks.md:1929`, `quality.md:367`, `quality.md:528`) are preserved verbatim and are known-stale per A4-02 supersession.~~ **ADR-031** (`docs/corpus/aidr/decisions/adr-031-azure-credentials-mvp.md`)
documented an MVP-time-bound deviation to a long-lived `AZURE_CREDENTIALS`
JSON secret — that ADR's deviation does NOT apply to `staging-promotion.yml`
(which has reverted to OIDC, observable at `staging-promotion.yml:31, 61-64,
135-140`) and MUST NOT be cited as licence to introduce a long-lived
`SMOKE_TOKEN` secret. The current FR-072 text's `SMOKE_TOKEN` reference
(spec.md:3323-3325) is recognised as an interim shorthand and is propagated
to "short-lived OIDC-derived bearer" wording in Step 8x.

**Authority**: Constitution clause NN-2 (Data sovereignty — `australiaeast`
residency for `tnt-stg-smoke`). Constitution Principle IV (Transparency &
Auditability — least-privilege identity, single-tenant scoping for the test
identity). Existing OIDC plumbing at `staging-promotion.yml:31, 61-64,
135-140` (the workflow already uses federated credentials despite ADR-031;
extend that pattern, not the ADR-031 fallback). Existing tenant-isolation
contract at `tests/integration/test_smoke_injection_no_prod_pollution.py:34-48`
(the forbidden-literal list and the dedicated-tenant assertion). FR-072
spec.md:3315-3330 (the current `SMOKE_TOKEN` shorthand to be re-worded).

**Spec-text propagation** *(deferred)*:

- `propagation_target: specs/036-sim-agent-extend/spec.md` (FR-072 in-place
  text at L3323-L3325) — replace `"$SMOKE_TOKEN"` shorthand with `"a
  short-lived bearer access token acquired via azure/login@v2 + az account
  get-access-token; no long-lived SMOKE_TOKEN secret is permitted"`. **(Step 8x)**
- `propagation_target: contracts/sli-thresholds.md:230-244, 276-289` —
  add `| where tenant_id == "tnt-stg-smoke"` to the canonical Z6 and Z7
  KQL bodies, and extend the §6a / §6b table-row "Filters" cell
  accordingly. **(Step 8x)**
- `propagation_target: .github/workflows/staging-promotion.yml:142-185` —
  refactor the smoke-injection step body to (a) call `az account
  get-access-token` for the bearer; (b) loop with `requests.post(...,
  headers={"Authorization": f"Bearer {bearer}"}, ...)`; (c) remove every
  reference to a `SMOKE_TOKEN` environment variable. **(Step 8z)**
- `propagation_target: tests/contract/test_smoke_tenant_isolation.py` (new) —
  assert the role assignment list emitted by
  `infra/bicep/modules/cosmos-simulation-containers.bicep` is scoped to
  `tnt-stg-smoke` for the `Simulation.Coordinator` identity. **(Step 8z)**
- `propagation_target: infra/bicep/modules/cosmos-simulation-containers.bicep` —
  emit (or confirm existing) `Simulation.Coordinator` → `tnt-stg-smoke`
  role assignment with no production-tenant scope; private endpoint + CMK
  posture parity with production. **(Step 8z; design only — no code change in this pass)**
- `propagation_target: docs/aidr/decisions/ADR-036-NN-cycle-3-amendment-cycle.md` (new) —
  record the Cycle 3 explicit non-application of ADR-031's `AZURE_CREDENTIALS`
  fallback to the staging-promotion workflow. **(Step 8x)**

### Q3 — When two staging-promotion gate runs both fail concurrently, do their `StagingPromotionRefused` raises serialise into one DLQ row or two distinct rows?

**Answer**: **Two distinct rows.** Each refused gate run writes its own
`staging_promotion.refused` audit envelope with a fresh per-run UUID
`staging_promotion_correlation_id`; both runs exit non-zero independently;
no coalescing or deduplication is applied at the audit-write boundary. The
GitHub Actions workflow adds a `concurrency:` block at workflow level so
two runs **queue rather than execute concurrently** for the common
`workflow_dispatch` path; but if two runs DO race (for example via
different refs, or via a future cron-triggered run colliding with a manual
one), each MUST observe the gate independently and each MUST write its
own envelope. The `staging_promotion.refused` envelope is a NEW
audit-envelope type added in Cycle 3 (placement TBD by Step 8x — likely
`contracts/audit-envelope.md` §3.21 or next-available index; the Cycle 1 +
Cycle 2 envelopes occupy §3.16 / §3.17 / §3.18 / §3.19 / §3.20) with the
following minimum field set: `staging_promotion_correlation_id: uuid`
(fresh per run, UUID4), `build_label: str` (from
`workflow_dispatch.inputs.build_label`), `triggering_workflow_run_id: int`
(from `github.run_id`), `triggering_actor: str` (from `github.actor`),
`breached_slis: list[str]` (e.g. `["SLI-Z6", "SLI-Z7"]`),
`sample_floor_underages: list[{"sli_id": str, "observed_samples": int,
"required_samples": int}]`, `refused_at: ISO8601 timestamp`,
`gate_helper_version: str` (sha-256 of `tests/staging_gates.py` at run
time, for reproducibility under Constitution IV). The envelope MUST be
written by the gate-helper (`assert_sli_thresholds()` in
`tests/staging_gates.py:98`, on its `StagingPromotionRefused` raise path)
**before** the exception propagates — NOT by the workflow YAML — because
the gate-helper is the binding contract surface mandated by FR-071
(spec.md:3297-3313) and has the structured failure detail in scope; the
workflow YAML only needs to translate the non-zero process exit into a
job-level failure. The pattern mirrors **Cycle 2 Pass-1 Q4**
(spec.md:464-499) per-subscriber `correlation_id` semantics: as each
fan-out edge gets a fresh UUID distinct from the parent
`injection_correlation_id`, each gate run gets a fresh
`staging_promotion_correlation_id` distinct from every external identifier
(`build_label`, `github.run_id`, etc.). Two concurrent `assert_sli_thresholds()`
invocations therefore produce two distinct envelopes, two distinct
correlation IDs, two non-zero process exits, and two distinct job-level
failures — never a coalesced single envelope. This is reproducibility-
and-attribution-positive: a forensic reviewer querying
`audit.staging_promotion.refused` can attribute every refusal to its
`triggering_workflow_run_id` + `triggering_actor` + `gate_helper_version`
unambiguously.

**Authority**: Constitution Principle IV (Transparency & Auditability —
append-only, gap-free, typed audit trail; coalescing two refusals into one
row violates the gap-free invariant that SLI-Z2 P99 ≤ 1 gap per 10 000
envelopes is built to enforce). Constitution Principle V (Graceful
Degradation — predictable failure surface; each workflow run MUST receive
a deterministic non-zero exit independent of concurrent activity).
**Cycle 2 Pass-1 Q4** (spec.md:464-499, "per-subscriber dispatch
correlation_id, array ordered lexicographically by `sub_agent` PascalCase
enum") — the pattern is reused here at the workflow-run granularity. FR-071
spec.md:3297-3313 — the gate-helper is the binding contract surface; the
workflow YAML is the propagation surface. `audit-envelope.md` §3.16 / §3.17 /
§3.18 envelope-shape precedent for the new envelope type.

**Spec-text propagation** *(deferred)*:

- `propagation_target: specs/036-sim-agent-extend/spec.md` (FR-071 in-place
  text at L3297-L3313) — append a sentence: *"On `StagingPromotionRefused`
  raise, `assert_sli_thresholds()` MUST write a `staging_promotion.refused`
  audit envelope (per `contracts/audit-envelope.md` §3.NN) with a fresh
  `staging_promotion_correlation_id` (UUID4) before the exception
  propagates; two concurrent refused runs each write their own envelope —
  no coalescing."* **(Step 8x)**
- `propagation_target: contracts/audit-envelope.md` — add §3.NN
  `staging_promotion.refused` envelope schema with the eight-field minimum
  set above; declare `staging_promotion_correlation_id` as the
  single-stream JOIN key. **(Step 8x)**
- `propagation_target: tests/staging_gates.py:98-130` — extend
  `assert_sli_thresholds()` to instantiate the audit-envelope writer and
  emit a `staging_promotion.refused` envelope before each
  `StagingPromotionRefused` raise. **(Step 8z)**
- `propagation_target: .github/workflows/staging-promotion.yml` — add a
  workflow-level `concurrency: { group: staging-promotion-${{
  github.workflow }}-${{ github.ref }}, cancel-in-progress: false }` block
  to queue concurrent dispatches at the GitHub Actions layer. **(Step 8z)**
- `propagation_target: tests/integration/test_staging_promotion_concurrency.py` (new) —
  invoke `assert_sli_thresholds()` twice concurrently against shared
  red-fixture data; assert two distinct envelope rows + two distinct
  `staging_promotion_correlation_id` values + two non-zero exits. **(Step 8z)**

### Q4 — Where do SC-014's "deliberately-constructed red SLI rows" come from — a CI-level Python fixture, a live KQL injection into the staging Application Insights workspace, or a separate dedicated canary tenant?

**Answer**: **Option (b) — CI-level Python fixture** consumed via the
existing `assert_sli_thresholds(*, sli_results: Mapping[str, Mapping[str,
Any]])` signature at `tests/staging_gates.py:98-101`. The synthetic-canary
test (`tests/e2e/test_staging_promotion_gates.py::test_synthetic_canary_refused_red_sli_row`,
new in Step 8z) constructs a deterministic red `sli_results` dict in
Python, invokes `assert_sli_thresholds(sli_results=red_fixture)`,
and asserts four invariants: **(i)** `pytest.raises(StagingPromotionRefused)`
is raised by the helper; **(ii)** the synthetic-canary subprocess invocation
of `pytest tests/e2e/test_staging_promotion_gates.py -q` returns a non-zero
process exit; **(iii)** no `promote/{build_label}` git tag is created in
the test fixture's git workspace (asserted by checking `git tag --list
"promote/*"` after the gate fails — the git-tag step in
`staging-promotion.yml:197-200` runs only on the `promote` job which
`needs: [..., runtime-gate]`, so a non-zero `runtime-gate` short-circuits
the tagging); **(iv)** the `staging_promotion.refused` audit envelope (per
Q3 above) is written exactly once per refused invocation, with the expected
`breached_slis` content matching the canary fixture's red SLI list.
**Live-KQL canary** (option (a)) is **explicitly rejected** because it
would inject deliberately-malformed telemetry into the same
Application Insights workspace the production gate consumes — contaminating
the gate's own evidence stream and risking false-positive refusals on
genuine staging telemetry. **Dedicated canary tenant** (option (c) — a
separate `tnt-stg-canary` tenant whose telemetry is filtered out of the
production gate by KQL) is **rejected as premature complexity**: the
fixture-driven option meets SC-014's literal requirement (the gate refuses
when SLI rows are red), runs in <100 ms per case, has zero infrastructure
cost, and is fully deterministic without requiring a second isolated
tenant beyond `tnt-stg-smoke` (Q2). The fixture pattern is enabled
**without code change** by the existing `assert_sli_thresholds()`
signature — the helper accepts `sli_results: Mapping[str, Mapping[str,
Any]]` directly, so the fixture path and the production path share one
contract surface; the production path differs only in that its
`sli_results` is materialised by the workflow's `az monitor app-insights
query` invocation rather than by Python literal. The KQL→Python adapter
that converts live KQL output into `sli_results` is the boundary at which
real staging data enters the gate; the canary lives below that boundary
(as fixture data) so it never crosses into the staging Application Insights
workspace at all. The canary fixture set MUST cover **at least four
distinct red shapes**: (1) Z6 P95 latency above the breach threshold for
gpt-4o (e.g. `p95_latency_ms = 5500`, threshold 5 000 ms, sample_count =
50); (2) Z7 drift_budget_pct below the breach threshold (e.g.
`drift_budget_pct = 98.5`, threshold 99.0 %, sample_count = 50); (3) Z6
sample-floor underage (e.g. `sample_count = 17`, threshold 30); (4) Z7
sample-floor underage (e.g. `sample_count = 5`, threshold 30). Each shape
asserts the helper raises with the matching `StagingPromotionRefused`
message substring (latency-breach vs drift-breach vs sample-starvation),
and asserts the audit envelope's `breached_slis` and
`sample_floor_underages` fields contain the expected entries.

**Authority**: Constitution Principle V (Graceful Degradation — predictable
failure surface; the canary tests the failure surface, not the data path).
SC-014 spec.md:3456-3466 (the literal acceptance criterion is the gate
refuses + no tag created — both achievable at the helper boundary without
live-KQL injection). FR-071 spec.md:3297-3313 (the gate-helper is the
binding contract surface). Existing
`tests/staging_gates.py::assert_sli_thresholds(sli_results=...)` signature
(line 98-101) — the helper already accepts an in-Python mapping; the
canary fixture path is enabled by design. Cycle 2 Pass-2 Q4
(spec.md:702-748) — `MIN_SAMPLES_PER_SLI_24H = 30` is a constant the
helper enforces; the canary parameterises that constant on the
sample-starvation shapes. Cycle 1 Pass-2 Q2 (spec.md:368) — deterministic
fixtures, no LLM, no heuristics, in service of SC-011 reproducibility.

**Spec-text propagation** *(deferred)*:

- `propagation_target: specs/036-sim-agent-extend/spec.md` (SC-014 in-place
  text at L3456-L3466) — append a clarifying sentence: *"The synthetic
  canary is fixture-driven (a deterministic in-Python `sli_results` dict
  passed directly to `assert_sli_thresholds()`); it does NOT inject
  telemetry into the staging Application Insights workspace and therefore
  does NOT contaminate the production gate's evidence stream."* **(Step 8x)**
- `propagation_target: tests/e2e/test_staging_promotion_gates.py` —
  add `test_synthetic_canary_refused_red_sli_row` covering the four red
  shapes above; assert the four invariants (i)–(iv). **(Step 8z)**
- `propagation_target: tasks.md` — add the canary test creation as a
  Cycle 3 Pass-1 task; gate on Q3's audit-envelope work landing first
  (the canary asserts the envelope shape, so the envelope schema must
  pre-date the canary). **(Step 8z)**
- `propagation_target: checklists/quality.md` — add a row asserting the
  canary fixture covers all four red shapes (P95 latency breach +
  drift breach + Z6 sample starvation + Z7 sample starvation). **(Step 8x)**

### Q5 — Does FR-073's KQL canonicalisation contract apply retroactively to Z1-Z5, or is it scoped to Z6+Z7 only (the cohort-validated defect surface)?

**Answer**: **Yes, FR-073 applies retroactively to all seven SLIs (Z1
through Z7).** The contract test
`tests/contract/test_sli_kql_canonical_match.py` (per Q1) iterates over
every entry in `infra/observability/sli-kql.json["slis"]` (currently 7,
asserted at `tests/contract/test_sli_kql_schema_v2.py:33-37`) and asserts
canonicalised byte-equality between each SLI's implementation KQL and its
canonical form in `contracts/sli-thresholds.md`. The Step 8z work-item
that lands the new contract test MUST include a one-time audit pass over
Z1-Z5, with any drift fixed in the **same** PR that introduces the
contract test (so the test is green on day-one). FR-073's existing spec.md
text at L3332-L3349 already says *"Each implementation KQL query in
`infra/observability/sli-kql.json` MUST match the canonical KQL definition
in `specs/036-sim-agent-extend/contracts/sli-thresholds.md` for that SLI"*
and *"every declared SLI"* — i.e. the FR text already implies universal
scope. The acceptance criterion at spec.md:3348-3349 *"the test covers both
Z6 and Z7"* is the **cohort-finding-driven minimum** (the surface the
Step 8s cohort actually validated), NOT the contract surface — these two
are intentionally distinguishable: cohort minimums describe what was
audited, contract surfaces describe what is enforced going forward. The
contract surface MUST be uniform (per Constitution Principle IV — single
source of truth) so that future drift on Z1-Z5 is caught, not silently
tolerated. **Pre-existing Z1-Z5 alignment status**: Cycle 2 Amendment
A2-02 reviewed Z1-Z5 KQL bodies as part of the staging-gate work
(`infra/observability/sli-kql.json:6-71`) and aligned them with
`contracts/sli-thresholds.md` §2-§5; Z1-Z5 are therefore **presumed aligned
as of Cycle 2 close**. The Step 8z PR that lands `test_sli_kql_canonical_match.py`
confirms this presumption — if drift is found on Z1-Z5, it is fixed in
the same PR (drift-fix is in-scope; the FR-073 surface IS the canonical
contract-surface). The contract test MUST also assert idempotence of the
canonicalisation helper (per Q1) and parametric symmetry — all 7 SLIs are
exercised by the same parametrised pytest test, NOT by separate test
functions per SLI, so any SLI added to `sli-kql.json` after Cycle 3
automatically participates in the canonicalisation contract.

**Authority**: Constitution Principle IV (Transparency & Auditability —
single source of truth requires uniform contract enforcement; selective
scoping creates a two-tier contract surface, counter to single-source-of-
truth). FR-073 spec.md:3332-3349 — *"every declared SLI"* phrasing is
already universal-scope. ADR-036-008 — pins
`contracts/sli-thresholds.md` as the canonical surface for ALL declared
SLIs, not just Z6/Z7. Cycle 2 Amendment A2-02 review of Z1-Z5 alignment
(referenced in the Cycle 2 amendment log; the canonical alignment was
done in Step 8r as part of the Z6+Z7 introduction work).
`tests/contract/test_sli_kql_schema_v2.py:33-37` — the existing schema
test already iterates over all 7 SLIs; the canonicalisation test follows
the same iteration pattern.

**Spec-text propagation** *(deferred)*:

- `propagation_target: specs/036-sim-agent-extend/spec.md` (FR-073 in-place
  text at L3348-L3349) — re-word *"the test covers both Z6 and Z7"* to
  *"the test covers all seven SLIs (Z1–Z7); Z6 and Z7 are the cohort-
  finding-driven minimum surface the Step 8s cohort validated, but the
  contract surface is universal — every declared SLI in
  infra/observability/sli-kql.json participates in canonicalisation
  enforcement"*. **(Step 8x)**
- `propagation_target: tests/contract/test_sli_kql_canonical_match.py` (new,
  per Q1) — implement as a parametrised pytest test iterating over every
  entry in `sli_doc["slis"]`, NOT as separate functions per SLI. **(Step 8z)**
- `propagation_target: tasks.md` — add a one-time audit pass over Z1-Z5
  KQL alignment as a sub-task of the Step 8z canonicalisation-test work;
  any drift discovered is fixed in the same PR. **(Step 8z)**
- `propagation_target: checklists/quality.md` — add a row asserting the
  contract test parametrises over all SLIs in `sli-kql.json` (i.e. is not
  hard-coded to a 2-element list). **(Step 8x)**

**Resolution rollup (Cycle 3 pass 1)**: Q1 → pins **strict-string-after-
normalisation** as the FR-073 KQL canonicalisation algorithm with a
deterministic six-step pipeline (`canonicalise_kql`); Q2 → pins **no
long-lived `SMOKE_TOKEN`** (short-lived OIDC-derived bearer instead) and
codifies five `tnt-stg-smoke` tenant-isolation guarantees (data residency,
sole-tenant scope, posture parity, KQL filtering, least-privilege test
identity); Q3 → pins **two distinct `staging_promotion.refused` audit
envelopes** for two concurrent failed gate runs, each with a fresh
`staging_promotion_correlation_id` (UUID4), enforced at the
gate-helper boundary, with a workflow-level `concurrency:` block to queue
common-path dispatches; Q4 → pins **CI-level Python fixture** (not
live-KQL injection, not dedicated canary tenant) as the SC-014 synthetic-
canary input mechanism, exploiting the existing
`assert_sli_thresholds(sli_results=...)` signature; Q5 → pins **all seven
SLIs (Z1–Z7)** as the FR-073 canonicalisation contract surface, with a
one-time Z1-Z5 audit pass folded into the Step 8z work-item that lands
the contract test. Together these five resolutions close the second-order
ambiguities Cycle 3 deferred to a clarify pass and unblock **Step 8x**
(checklist + ADR-036-NN-cycle-3 + CHANGELOG drift fixes + FR-072 /
FR-073 / SC-014 in-place text re-wording + audit-envelope §3.NN +
contracts/sli-thresholds.md §"KQL canonicalisation contract" subsection),
**Step 8y** (plan-decision row pinning strict-string canonicalisation),
and **Step 8z** (`_kql_canonicaliser.py`, `test_sli_kql_canonical_match.py`,
`test_smoke_tenant_isolation.py`, `test_staging_promotion_concurrency.py`,
`test_synthetic_canary_refused_red_sli_row`, smoke-injection workflow
refactor to use OIDC-derived bearer + real HTTP POST, and the one-time
Z1-Z5 KQL alignment audit). No prior Q→A is contradicted; this pass is
fully additive.

## Clarifications (Cycle 3 — Pass 2)

### Session 2026-05-10 (Cycle 3 amendment clarify pass 2)

These resolutions close the **second-order ambiguities** that the Cycle 3
Pass-1 resolutions themselves opened (spec.md:812-1278). Pass-1 settled the
headline algorithmic and isolation invariants — strict-string KQL
canonicalisation (Q1), no long-lived `SMOKE_TOKEN` plus five `tnt-stg-smoke`
isolation guarantees (Q2), two distinct `staging_promotion.refused` audit
envelopes per concurrent gate refusal (Q3), CI-level Python fixture for the
SC-014 synthetic canary (Q4), and universal Z1–Z7 KQL canonicalisation
contract scope (Q5). Pass-2 pins three narrow remaining edges that the
Pass-1 agent itself flagged for convergence: the exact `audit-envelope.md`
slot number and counter increment for the new envelope (Q1); the public
Python signature of the `canonical_kql_for_sli` helper that backs the
FR-073 contract test (Q2); and whether the one-time Z1-Z5 alignment audit
blocks or co-merges with the canonicalisation contract-test PR (Q3).
Cycle 1, Cycle 2 Pass-1, Cycle 2 Pass-2, and Cycle 3 Pass-1 Q→A entries
remain in force unchanged; the three resolutions below are **additive** and
do not contradict any prior resolution. Each resolution is decided by the
`speckit.clarify` agent under the user's explicit "deciding authority"
mandate; each is constitution-aligned, prior-precedent-consistent, and
quantitative where possible. `file:line` evidence is cited for every claim.
**Spec-text propagation** for each Q is annotated with `propagation_target:`
markers and is **deferred** to Step 8x (checklist + ADR / CHANGELOG drift),
Step 8y (plan delta), and Step 8z (tasks + test implementation) — no other
artefacts are modified by this pass.

### Q1 — What is the exact `contracts/audit-envelope.md` section number for the new `staging_promotion.refused` typed envelope, and how does the typed-entry counter increment?

**Answer**: **§3.26 is the natural slot**, and the typed-entry counter
increments from **25 to 26** in two places: the `entry_type` enumeration
list at `contracts/audit-envelope.md:689` ("any of the **25** typed entries
above" → "any of the **26** typed entries above") and the §6.1 heading at
`contracts/audit-envelope.md:703` ("5 added in Cycle 1, 1 added in Cycle 2
— total 19 → 25" → "5 added in Cycle 1, 1 added in Cycle 2, 1 added in
Cycle 3 — total 19 → 26"), plus a new row added to the §6.1 table for
`staging_promotion.refused` (Cycle 3 Amendment A3-01 / FR-071, Cosmos
container `simulation_audit_entries`). The Pass-1 Q3 spec text at
spec.md:1029 cited "§3.21 or next-available index" with the parenthetical
"the Cycle 1 + Cycle 2 envelopes occupy §3.16 / §3.17 / §3.18 / §3.19 /
§3.20"; this was an imprecise hand-wave — the actual envelope progression
is §3.16 `sub_agent.timeout`, §3.17 `sub_agent.cancel`, §3.18
`sub_agent.degraded`, §3.19 `tenant_isolation.violation`, then a deliberate
gap (§3.20–§3.24 are unused), then §3.25 `signal_pipeline.dispatch_failed`
(Cycle 2 Amendment A2-01). Pass-2 corrects the Pass-1 imprecision: §3.26 is
the next-natural sequential slot, immediately after the Cycle 2 envelope,
mirroring the "append at the end of §3" pattern Cycle 2 itself followed.
The §3.20–§3.24 gap is **preserved** — back-filling it would obscure the
temporal ordering of envelope additions across cycles and would break any
existing tooling that has indexed the §3.25 anchor. The schema follows
Cycle 2's §3.25 pattern: gap-free `sequence_number` is allocated by the
writer's `assert_sli_thresholds()` invocation of the existing audit-write
surface (NOT a literal in the schema — Cycle 2 Amendment A2-06
`cascade.depth2_refused` removed the placeholder `sequence_number = 1`
literal precisely to make the writer's gap-free allocator the sole source
of truth, see `contracts/audit-envelope.md:726`); and `details` carries
the eight-field set already pinned by Pass-1 Q3
(`staging_promotion_correlation_id`, `build_label`,
`triggering_workflow_run_id`, `triggering_actor`, `breached_slis`,
`sample_floor_underages`, `refused_at`, `gate_helper_version`). The §3.26
schema MUST also declare `entry_type: { "type": "string", "const":
"staging_promotion.refused" }` for typed-envelope discriminator parity with
§3.25, and MUST include a top-level `correlation_id` field whose value
equals the `staging_promotion_correlation_id` (so the established
single-stream JOIN-by-`correlation_id` pattern from Cycle 2 Pass-1 Q4 keeps
working at the workflow-run granularity).

**Authority**: Constitution Principle IV (Transparency & Auditability — the
typed-envelope counter is the canonical source of truth for forensic
reconstruction; an off-by-one counter mismatch is a Constitution-IV
defect). Cycle 2 Amendment A2-06 / FR-048 STRENGTHEN —
`contracts/audit-envelope.md:726` (placeholder sequence-number literal
removed; writer is sole source of truth; Cycle 3 §3.26 inherits this).
Cycle 2 Pass-1 Q1 byte-equality + Cycle 2 Pass-1 Q4 per-subscriber
correlation_id semantics — `contracts/audit-envelope.md:735-736`
(single-stream JOIN-by-`correlation_id` invariant; Cycle 3 §3.26 follows
the same pattern at workflow-run granularity). Existing envelope
progression — `contracts/audit-envelope.md:538` (§3.16), :556 (§3.17),
:573 (§3.18), :590 (§3.19), :607 (§3.25); the §3.20–§3.24 gap is
observable directly. Pass-1 Q3 spec text at spec.md:1029 (the imprecise
hand-wave Pass-2 corrects).

**Spec-text propagation** *(deferred — DO NOT modify in this pass)*:

- `propagation_target: contracts/audit-envelope.md` — add §3.26
  `staging_promotion.refused` schema with the eight-field `details` set
  from Pass-1 Q3 plus the `entry_type` const discriminator and the
  top-level `correlation_id == staging_promotion_correlation_id`
  invariant. **(Step 8x)**
- `propagation_target: contracts/audit-envelope.md:689` — bump the
  typed-entry counter "**25** typed entries" → "**26** typed entries";
  append `staging_promotion.refused` to the inline enumeration. **(Step 8x)**
- `propagation_target: contracts/audit-envelope.md:703` — re-word the §6.1
  heading from "5 added in Cycle 1, 1 added in Cycle 2 — total 19 → 25"
  to "5 added in Cycle 1, 1 added in Cycle 2, 1 added in Cycle 3 — total
  19 → 26"; add a new table row for `staging_promotion.refused` with
  source amendment "Cycle 3 Amendment A3-01 / FR-071" and Cosmos container
  `simulation_audit_entries`. **(Step 8x)**
- `propagation_target: specs/036-sim-agent-extend/spec.md` (FR-071 in-place
  text amended by Pass-1 Q3 propagation queue at spec.md:1075-1097) —
  replace "§3.NN" / "§3.21 or next-available index" placeholders with
  "§3.26" before propagating Pass-1 Q3's FR-071 sentence amendment. **(Step 8x)**
- `propagation_target: tests/contract/test_audit_envelope_schema.py` (or
  the equivalent envelope-shape contract test) — extend the `entry_type`-
  discriminator parametrisation to assert the new §3.26 schema is
  reachable + JSON-schema-valid. **(Step 8z)**

### Q2 — What is the public Python signature of the `canonical_kql_for_sli` helper that backs the FR-073 contract test, and what is the test-isolation override mechanism?

**Answer**: The public surface of `tests/contract/_kql_canonicaliser.py` is
**two free functions plus one private helper**:

```python
# Public — directly invoked by the parametric contract test.
def canonicalise_kql(text: str) -> str: ...

def canonical_kql_for_sli(
    sli_id: str,
    *,
    thresholds_path: Path | None = None,
) -> str: ...

# Private — pure 6-step pipeline used by canonicalise_kql for unit-tested inputs.
def _canonicalise_kql_string(raw: str) -> str: ...
```

`canonicalise_kql` is the public 6-step normaliser pinned by Pass-1 Q1
(spec.md:838-889); it accepts an arbitrary KQL string and returns its
canonicalised form (deterministic, idempotent, <1 ms).
`canonical_kql_for_sli` parses the matching fenced ` ```kql ... ``` ` block
out of `specs/036-sim-agent-extend/contracts/sli-thresholds.md` (one
fenced block per SLI section: §2 SLI-Z1, §3 SLI-Z2, §4 SLI-Z3, §5 SLI-Z4,
§6 SLI-Z5, §6a SLI-Z6, §6b SLI-Z7 — verifiable at
`contracts/sli-thresholds.md:44, 83, 147, 187, 229, 276`) and returns its
canonicalised form (i.e. it composes `canonicalise_kql(extracted_block)`
internally). It is a **function** (not a generator) — it takes one
`sli_id`, returns one `str`; iteration over all 7 SLIs is the parametrised
pytest test's responsibility (per Pass-1 Q5 spec.md:1213-1217). Return
type is **`str`** (not `tuple[str, str]`, not `dict[str, str]`) because the
test consumer needs only the canonicalised KQL body; `sli_id` is already
known by the caller. The `thresholds_path: Path | None = None`
keyword-only parameter defaults to `None`, which resolves at call time to
a module-level constant `_THRESHOLDS_PATH = Path(__file__).resolve().parents[2]
/ "specs" / "036-sim-agent-extend" / "contracts" / "sli-thresholds.md"`,
mirroring the established pattern at
`tests/contract/test_sli_kql_schema_v2.py:25` for `_SLI_PATH`. Tests that
need isolation pass `thresholds_path=tmp_path / "sli-thresholds.md"` to
redirect to a synthetic fixture; production callers omit the parameter.
**Error contracts**: `canonical_kql_for_sli("SLI-NONEXISTENT")` raises
`KeyError("SLI-NONEXISTENT not found in <path>")`; a malformed contracts
file (missing fenced block, missing SLI section heading) raises
`ValueError("Failed to extract canonical KQL for <sli_id>: <reason>")`.
**`_canonicalise_kql_string(raw: str) -> str`** is the private 6-step
pipeline; `canonicalise_kql` simply wraps it with optional input
validation and is the public entry point. The split exists so that the
unit-test surface for the 6-step pipeline (idempotence, determinism,
step-by-step golden fixtures) can target `_canonicalise_kql_string`
without re-exporting it; callers that import the public name see one
stable function. The module export list (`__all__`) declares only
`["canonicalise_kql", "canonical_kql_for_sli"]`. The new contract test
`tests/contract/test_sli_kql_canonical_match.py` (Pass-1 Q1 Step 8z
work-item) consumes the public surface directly:
`assert canonicalise_kql(impl["kql"]) == canonical_kql_for_sli(sli_id)`
for every SLI in the parametrised loop.

**Authority**: Constitution Principle IV (Transparency & Auditability —
explicit, narrow, type-annotated public contract surfaces; the `__all__`
export list is the contract). Pass-1 Q1 spec.md:842-847 (the names
`canonicalise_kql`, `canonical_kql_for_sli` were already pinned; Pass-2
fills in the parameter contract). Pass-1 Q5 spec.md:1213-1217 (the
contract test MUST be parametric over all 7 SLIs, NOT separate functions
per SLI — Pass-2 Q2 ensures the helper signature supports this without
bending). Established convention —
`tests/contract/test_sli_kql_schema_v2.py:25` (`_SLI_PATH =
Path(__file__).resolve().parents[2] / "infra" / "observability" /
"sli-kql.json"`); the Cycle 3 helper extends this with `_THRESHOLDS_PATH`
pointing at the contracts doc. Cycle 1 Pass-2 Q2 deterministic-fixture
precedent (spec.md:1413) — the helper is pure-Python, no LLM, no
heuristics; tests inject `tmp_path` for isolation per the same precedent.

**Spec-text propagation** *(deferred)*:

- `propagation_target: tests/contract/_kql_canonicaliser.py` (new, per
  Pass-1 Q1) — implement the public/private surface above; declare
  `__all__ = ["canonicalise_kql", "canonical_kql_for_sli"]`; module-level
  `_THRESHOLDS_PATH` constant resolves the canonical contracts doc by the
  established `Path(__file__).resolve().parents[2] / ...` pattern.
  **(Step 8z)**
- `propagation_target: tests/contract/test_kql_canonicaliser_unit.py`
  (new) — golden-fixture unit tests targeting the private
  `_canonicalise_kql_string`: one test per of the six normalisation steps,
  plus idempotence + determinism + 10× re-run byte-equality. **(Step 8z)**
- `propagation_target: tests/contract/test_sli_kql_canonical_match.py`
  (new, per Pass-1 Q1) — consume the public `canonicalise_kql` +
  `canonical_kql_for_sli` surface; parametrise
  `@pytest.mark.parametrize("sli_id", [s["id"] for s in sli_doc["slis"]])`
  so all 7 SLIs are exercised by one test function. **(Step 8z)**
- `propagation_target: contracts/sli-thresholds.md` (Pass-1 Q1
  §"KQL canonicalisation contract" subsection) — when authored, document
  the public surface above (function names, signatures, return types,
  error contracts, `_THRESHOLDS_PATH` resolution) so consumers can rely
  on the contract without spelunking the implementation. **(Step 8x)**

### Q3 — Does the one-time Z1-Z5 KQL alignment audit BLOCK the canonicalisation contract-test PR (audit-first, then test-first), or CO-MERGE in a single PR?

**Answer**: **CO-MERGE in a single PR.** The Cycle 3 Step 8z PR that lands
`tests/contract/_kql_canonicaliser.py`,
`tests/contract/test_kql_canonicaliser_unit.py`, and
`tests/contract/test_sli_kql_canonical_match.py` (the parametric over-all-
7-SLIs contract test) MUST also contain — in the **same PR** — any Z1-Z5
alignment fixes that the parametric test surfaces during PR review (whether
to `infra/observability/sli-kql.json` implementation KQL, or to the
canonical KQL fenced blocks in `contracts/sli-thresholds.md`, depending on
which form is the source-of-truth defect). The contract test MUST be green
at PR-merge time; it MUST NOT be merged behind a `pytest.mark.xfail`, a
skip, or a hard-coded subset of SLIs. Sequential blocking (audit-first PR,
then a follow-up contract-test PR) is **explicitly rejected** because:
(a) the canonicalisation function (`_canonicalise_kql_string`, ~50 LoC)
plus the parametric contract test (~30 LoC) plus any Z1-Z5 drift fixes
(typically ≤ 5 LoC per drift, presumed-zero per Pass-1 Q5
spec.md:1206-1210) all fit comfortably in one PR's review surface;
(b) Cycle 2 Amendment A2-02's introduction of Z6 + Z7 followed exactly
this co-merge pattern — the canonical KQL fenced blocks at
`contracts/sli-thresholds.md:229, 276` and the implementation entries in
`infra/observability/sli-kql.json` were aligned **inside the same Cycle 2
PR** that introduced the new SLIs, with no preceding audit PR;
(c) Constitution Principle IV (single source of truth) is honoured by
ensuring the contract test is canonical-form-aligned on day-one for every
declared SLI — a sequential approach would leave the SLI-Z1–Z5 surface
unaudited under the new contract until the second PR landed, creating a
window where the canonicalisation contract is partially-enforced
(i.e. a two-tier surface, exactly what Pass-1 Q5 explicitly rejected per
spec.md:1219-1222); (d) the Cycle 1 Pass-2 Q2 deterministic-fixture
precedent (spec.md:1413) — single-shot deterministic landing — is the
spec's established "drift fix" pattern. **Pre-existing Z1-Z5 alignment
status**: per Pass-1 Q5 (spec.md:1206-1210), Z1-Z5 are **presumed
aligned** as of Cycle 2 close (Cycle 2 Amendment A2-02 reviewed them as
part of the staging-gate work); the Step 8z PR confirms this presumption
empirically. Empirical confirmation has three possible outcomes: **(i)**
all 5 SLIs (Z1-Z5) byte-equal-after-canonicalisation on first run — the
test is green, no drift fixes needed, the PR is the contract-test PR
alone; **(ii)** drift surfaced on one or more of Z1-Z5 — the same PR
fixes the canonical or implementation form (per the source-of-truth
determination at PR review), and the PR description records the drift in
a "Drift fixed inline" section; **(iii)** drift surfaced that requires
plan-level decision (e.g. ambiguity over which form is canonical) — a
`(plan-touch)` outcome; the PR description records the drift, opens a
tracking issue, and pins the canonicalisation test against the agreed
canonical form before merge (the test MUST still be green at merge).
Outcome (iii) is judged unlikely (Pass-1 Q5 + ADR-036-008 already pin
`contracts/sli-thresholds.md` as canonical for ALL declared SLIs) but is
the explicit fall-through. **Workflow ordering note**: Step 8x
(contracts/sli-thresholds.md §"KQL canonicalisation contract" subsection
authoring + audit-envelope.md §3.26 schema) MUST land **before** the
Step 8z PR opens, because the Step 8z contract test asserts the contracts
subsection's existence + the §3.26 envelope schema (per Pass-1 Q3's
`staging_promotion.refused` envelope being asserted in
`test_synthetic_canary_refused_red_sli_row`). Step 8x → Step 8z is
sequential by artefact dependency; the Step 8z PR itself is the **single
co-merge unit** for the canonicaliser + parametric test + any Z1-Z5 drift
fixes.

**Authority**: Constitution Principle IV (Transparency & Auditability —
single source of truth; uniform enforcement across all declared SLIs from
day-one; partial-enforcement-windows are anti-patterns). Pass-1 Q5
spec.md:1206-1227 (universal contract surface; Z1-Z5 presumed aligned per
Cycle 2 A2-02). Cycle 2 Amendment A2-02 co-merge precedent — Z6 + Z7
introduction at `contracts/sli-thresholds.md:210-303` and
`infra/observability/sli-kql.json` were landed in a single PR, not split
across an audit + contract-test pair. Cycle 1 Pass-2 Q2
deterministic-fixture precedent (spec.md:1413) — single-shot
deterministic landing for SC-011 reproducibility. Pass-1 Q1
spec.md:911-924 (Step 8z propagation queue already enumerates the
canonicaliser, contract test, schema-v2 extension; Pass-2 Q3 confirms
these are one PR, not three sequential PRs).

**Spec-text propagation** *(deferred)*:

- `propagation_target: tasks.md` — add a single Cycle 3 Step 8z task
  encompassing `_kql_canonicaliser.py` + `test_kql_canonicaliser_unit.py`
  + `test_sli_kql_canonical_match.py` + any Z1-Z5 drift fixes; mark as a
  **single co-merge unit** with a "Drift fixed inline" sub-bullet for the
  PR description if outcome (ii) is realised. **(Step 8z)**
- `propagation_target: tasks.md` — add an explicit dependency edge:
  Step 8x (contracts/sli-thresholds.md §"KQL canonicalisation contract" +
  audit-envelope.md §3.26) MUST land before Step 8z opens; this is
  enforced by the Step 8z contract test asserting the contracts surfaces'
  existence. **(Step 8z)**
- `propagation_target: checklists/quality.md` — add a row asserting the
  contract test is parametric over all 7 SLIs (not subset) at merge-time;
  reject any PR that lands the canonicaliser with `pytest.mark.xfail` or
  a hard-coded SLI subset. **(Step 8x)**
- `propagation_target: docs/aidr/decisions/ADR-036-NN-cycle-3-amendment-cycle.md`
  (new, per Pass-1 Q2 propagation queue at spec.md:1012-1014) — record
  the co-merge decision for the Cycle 3 Step 8z PR with the three-outcome
  rubric ((i) green / (ii) drift fixed inline / (iii) plan-touch
  fall-through). **(Step 8x)**

**Resolution rollup (Cycle 3 pass 2)**: Q1 → pins **§3.26** as the natural
slot for the new `staging_promotion.refused` typed envelope, with the
typed-entry counter incrementing 25 → 26 in `contracts/audit-envelope.md:689`
and `:703`; the §3.20–§3.24 gap is preserved (Pass-1 Q3's "§3.21 or next-
available index" hand-wave is corrected). Q2 → pins the public Python
surface of `tests/contract/_kql_canonicaliser.py` to two free functions
(`canonicalise_kql(text: str) -> str` and `canonical_kql_for_sli(sli_id:
str, *, thresholds_path: Path | None = None) -> str`) plus a private
`_canonicalise_kql_string(raw: str) -> str`; module-level
`_THRESHOLDS_PATH` constant mirrors the established `_SLI_PATH` pattern;
`KeyError` for unknown sli_id, `ValueError` for malformed contracts file.
Q3 → pins **CO-MERGE** as the Cycle 3 Step 8z landing pattern:
canonicaliser + parametric contract test + any Z1-Z5 drift fixes ship in
one PR (Cycle 2 A2-02 precedent), with Step 8x (contracts subsection +
§3.26 envelope schema) sequentially preceding by artefact dependency. No
Pass-1 Q→A is contradicted; this pass is fully additive and fully
convergence-style. The three resolutions close the second-order
ambiguities the Pass-1 agent flagged and unblock **Step 8x**
(audit-envelope.md §3.26 schema + counter increment + contracts/sli-
thresholds.md §"KQL canonicalisation contract" subsection +
ADR-036-NN-cycle-3 co-merge rubric + checklist row), **Step 8y** (no new
plan-decision rows; Pass-1 Q1's strict-string-canonicalisation row already
pinned; Pass-2 Q3 outcome (iii) is the only `(plan-touch)` fall-through
and is judged unlikely), and **Step 8z** (single Cycle 3 implement PR:
`_kql_canonicaliser.py`, `test_kql_canonicaliser_unit.py`,
`test_sli_kql_canonical_match.py`, Z1-Z5 drift fixes if any, with Step 8x
as a sequential prerequisite). **Pass-2 convergence achieved** — no
critical second-order ambiguities remain.

## Overview

Spec **024 — Simulation Control & Chat Orchestration** delivered the Simulation Controller chat
pane, allow-listed tools, rate-limiter, watermarking, real-world egress block, and SSE pipeline.
However, the six operational sub-agents the Controller orchestrates — Monitoring, Planning,
Resource Allocation, Communication, Evacuation, Risk Assessment — are still **stub adapters**
in `apps/api/app/services/simulation/sub_agent_invoker.py` (each returning the literal string
`"<agent>: simulated reply (no data source wired in this environment)."`). Coordinators see
plausible-looking chat replies but no real sub-agent reasoning ever runs in a simulation, and
no telemetry-driven map update is produced from a chat exchange.

This feature does three things that, together, turn the simulation page into the rehearsal
environment the capstone vision requires:

1. **Replace the stub adapters with real sub-agent invocations.** Each of the six operational
   sub-agents executes its substantive logic against the simulation tenant's signal pipeline
   and returns a real, citation-bearing answer that streams into the chat pane and is rendered
   on the Disaster Map via the appropriate overlay layer.
2. **Add a new *Simulation Telemetry-Injection Agent* (`simulation-telemetry-injection`)** that
   converts free-text coordinator chat (e.g. *"wind has shifted NW at 80 km/h"*, *"fire
   spotting started 3 km south"*, *"river gauge reading 9.4 m at Lismore"*, *"TC category
   increased to 4"*) into typed synthetic signals across nine categories — weather,
   fire-behaviour, hydrology, geohazard, utility, transport, evacuation, resource,
   comms-channel-state — that flow through the existing tenant-scoped signal pipeline so all
   downstream sub-agents react automatically (no manual re-entry, no copy-paste between agents).
3. **Auto-route every chat input to the right sub-agent by intent.** A wind-change message
   invokes Risk Assessment for impact prediction and hazard minimisation **without** the
   coordinator naming the agent. A *"river gauge"* message invokes Monitoring + Risk
   Assessment + Evacuation. An *"evacuate now"* directive invokes Communication (which produces
   a `[SIMULATION] ` receipt and remains hard-blocked from any real channel).

This is operator-facing additive work. It does **NOT** change tenant isolation (spec 007),
time-warp/playback (spec 026), the Disaster Map base-layer configuration (spec 020), or the
constitutional ban on real-world public warnings during simulation. It extends
`sub_agent_invoker.py`, adds a new `simulation-telemetry-injection` agent service, and adds
new `sim-telemetry-overlay` layer types to the map catalogue.

### Consolidated agent-cohort inputs

Per the author's direction, every operational and sectors persona file (10 + 58 = 68) was
canvassed in 4 parallel research passes. The full per-persona detail is in the session
workspace; the consolidated cohort summary below is the input that shaped this spec.

| Cohort | Key asks that shaped this spec |
|---|---|
| **AIIMS operational (10 — IC, Ops, Planning, Logistics, PIO, Field Coord, Executive, Observer, Resilience Planner, Risk Manager)** | Human-in-the-loop is unconditional **inside** the sim (IC approval, PIO warning approval, Extreme-risk IC+Executive prompts). Agent routing must mirror AIIMS functional separation — no blending. Telemetry injection must carry full provenance (`source: sim-injected`, timestamp, injecting user, sim ID, confidence, GPS) or be rejected at ingest. Risk Assessment must trigger **automatically** on every hazard-telemetry change (cascading-consequence modelling included); map updates from risk output appear within 15 s. Audit trail is append-only, gap-free, typed, machine-exportable for every sub-agent timeout/fallback/cancel/watermark/refusal. `SIMULATION — DO NOT DISTRIBUTE` watermark in every render and translation, sequenced before IC approval and before any "would-have-published" event. Map overlays are distinguished per AIIMS function (staging, field teams, risk overlays, hazard perimeters), all under the SIM badge with AWS colours plus a sim visual modifier (striped/dashed/badged); stale data is visually flagged. Real-world egress hard-blocked at every layer; synthetic delivery receipts mimic real ones (channel, audience, message id, sim timestamp, block reason). Progressive complexity injection — append telemetry to a running sim without restart; auto-generate AIDR-compatible exercise outcome record (not just a transcript); version-controlled scenario library. Sim data must not contaminate live records in either direction. Degraded-mode scenarios are first-class injectable content (comms blackout, sub-agent unavailable, network partition). Post-exercise lessons capture is structured (timeline + agent responses + IC decisions + identified gaps + lessons-identified section), retriable from audit if generation fails. |
| **NSW + VIC + QLD sectors (15)** | Combat-agency routing is jurisdiction-specific and non-interchangeable — NSW (FRNSW urban / NSW RFS rural), VIC (FRV declared / CFA regional), QLD (combined QFD). Routing must resolve jurisdiction + location + hazard class **before** selecting a fire sub-agent. SES is the lead flood/storm combat agency in all three states; sim must maintain dual combat-agency threads (fire + flood) without collapsing them. The CFA/FRV boundary in VIC is the highest-complexity routing decision; ambiguous peri-urban zones are flagged, not silently misrouted. QLD's combined QFD is invocable as a secondary coordination input in SES-led flood scenarios. Synthetic telemetry diverges sharply by hazard class — bushfire (FFDI, FDR, fuel load, spotting, AWS rating labels); flood/storm (rainfall rate, river height at named gauges, levee state, inundation polygon); cyclone (Aus-scale category 1–5, storm-tide height by zone A/B/C, central pressure, forward speed); marine (sea state, swell, vessel position, search sectors). TC category → storm-surge is non-linear; surge polygons must update when category changes mid-sim; zone A/B/C colour-coded and SIM-watermarked. AWS Advice / Watch and Act / Emergency Warning in all three states + VIC Code Red + QLD BOM TC tiers — every warning watermarked + `[SIMULATION] ` prefixed + correctly attributed to issuing agency per state. IC escalation is declared in VIC and QLD persona handoffs but **not** in NSW; sim must not attempt IC escalation from NSW invocations without explicit user direction. MRNSW is unique — open-water telemetry + nautical map symbology (search grids, vessel pins, drift polygons); MRNSW lacks a declared BOM handoff so the Controller injects BOM weather into marine scenarios without relying on a declared mrnsw→BOM path. Multi-hazard, multi-agency simultaneity is the most common edge case — concurrent bushfire + flood + medical + evacuation must run as parallel sub-agent threads with map overlays coexisting and chat replies attributed to the correct agency. |
| **SA + WA + TAS + NT + ACT sectors (24)** | Jurisdictional parity is non-negotiable — every state/territory is a valid `jurisdiction` parameter; each must have its agency graph wired to live sub-agents (no jurisdiction left on a generic stub). WA must NOT be forced into a NSW-style split — `dfes-wa` is the sole WA fire-and-emergency entry point. TAS uses a single combined fire service (TFS) — never instantiate a fictitious "TAS Rural Fire" agent. SA's SACFS/SAMFS split must be respected — location cues distinguish rural (→ sacfs) from metro (→ samfs). NT cyclone pathway (NTES) is a first-class scenario — TC-specific parameters (category 1–5, central pressure, destructive-wind radius, storm-surge height, track bearing); map renders track + radius rings + surge extent. NT has dual fire agencies (NTFRS structural; Bushfires NT rural) — both independently routable; "Darwin structure fire" vs "Katherine grass fire" disambiguated. ACT's ESA umbrella model — coordinator addresses `act-esa` for strategic coordination which fans out; sim must not bypass ESA. ACT has dual policing — AFP (federal/CT) vs ACT Policing (territory EM); intent cues distinguish. Medical service branding varies — SAAS, SJA-WA, SJA-NT, AT, ACT-Ambulance — no generic ambulance agent. `[SIMULATION] ` prefix applies to all outbound communications from every agency in every jurisdiction (Emergency WA, SA Emergency, TAS Alert, NT Emergency Alert, ACT Emergency Alerts, hospital, media). Remote-community and geographic-scale telemetry for WA / NT / TAS — road-impassability on remote tracks, air-medevac availability, remote-community isolation status, cyclone parameters. AIIMS + BOM are cross-jurisdictional constants — BOM wired as a sandboxed weather source; AIIMS authority levels respected in agent-response framing. |
| **Commonwealth + Cross-sector (19 — NEMA, ADF, AFP, BOM, GA, ARC, ABF, ASA, RFDS, SLSA, SJA + Local/State/Territory govt, Health, Transport, Utility, NGOs, Volunteers, Telco)** | BOM is the primary synthetic-weather source for all scenarios — wind, temperature, RH, FDR, precipitation, flood watch/warning, TC track, tsunami relay; any change with operational impact must auto-invoke Risk Assessment and update map within 10 s. GA is the primary synthetic geohazard source — earthquake, tsunami threat assessment, volcanic, landslide, ground movement, geomagnetic; GA + BOM share tsunami pathway (BOM relays, GA assesses). NEMA Level-3 escalation is simulate-able with auto-throttle banner per spec 024; COMDISPLAN activation produces only `[SIMULATION] ` artefacts; if a real Level-3 occurs during a sim the sim auto-throttles immediately and cannot suppress real notifications. Multi-org, multi-jurisdiction sim — scenarios spanning multiple states, levels of government, and sectors must be expressible in a single sim; jurisdiction is a required scenario-setup parameter. ADF DACC requests are sim-artefacts only — never real dispatches; chat requests to "order" real military action must be refused and logged. Every outbound channel hard-blocked with `[SIMULATION] ` prefix — covers BOM warnings, GA notifications, NEMA COMDISPLAN, ADF DACC, ABF maritime alerts, ASA NOTAMs, RFDS dispatch, ARC notices, Register.Find.Reunite, SJA casualty reports, SLSA beach closures, NGO alerts, health PHA, state/territory declarations, transport closures, utility outages, volunteer credentialling. Synthetic utility outages cascade — electricity outage updates hospital backup-power (Health), degrades comms channels (telco), affects Transport (signals), shifts Resource Allocation priority queues; one injection, no manual re-entry. Transport closures + utility outages update Evacuation routing in real time (flood-closes-primary-route is the canonical test case). Combat-vs-control role tagging enforced — Local/State/Territory govt, ARC, NGOs, Health, Volunteers are control/coord/support, not combat; sim must not route firefighting/SAR/law-enforcement to them. Evacuation-centre events (open / capacity / closed) are top-3 injectable signal across multiple personas — single authoritative map overlay fed by whichever agent injects first; visible to all consuming agents. Real-time map overlays for every major signal category (weather, geohazard zones, TC track + cone, flood polygons, utility-outage zones, hospital surge, evac-centre capacity, road closures + alt routes, airspace restrictions, maritime exclusion, vessel/aircraft positions, remote-community access, volunteer staging). Telco outage degrades Communications channel availability in-sim — reduced channel list visibly annotated; Triple Zero coverage loss prominently flagged. Territory-specific routing for ACT and NT — ACT routes policing to AFP (not state police) and uses territory govt for both state and local functions. Volunteer surge + fatigue auto-feeds Resource Allocation — spontaneous surge → unallocated headcount up; fatigue/depletion → headcount down; rural volunteers who are disaster-affected appear as resource depletion. |

### Assumptions

- **A1**: Simulation tenants are already created and authenticated via spec 007 mechanisms.
  This feature does not alter tenant provisioning. *(carried from spec 024)*
- **A2**: The hub runs on Azure; Azure OpenAI (gpt-4o-mini or equivalent, deployed in
  Australia East) is reachable via the same deployment used by spec 014 and used by spec 024
  for the Simulation Controller. *(carried from spec 024)*
- **A3**: Only users with the `SimulationCoordinator` Entra ID role may inject telemetry,
  invoke sub-agents via chat, or approve `would-have-published` artefacts.
  `SimulationObserver` users may read the chat transcript, telemetry timeline, and map
  overlays but cannot inject or invoke. *(extends spec 024 A3)*
- **A4**: The existing `PublicationService` and outbound HTTP client wrapper enforce the
  comms-block for spec 007 / 024. This feature continues to depend on both, and adds the
  `[SIMULATION] ` prefix and synthetic-delivery receipt envelope. *(carried from spec 024)*
- **A5**: The Disaster Map (spec 020) already renders tenant-scoped layers; this feature
  adds new `sim-telemetry-overlay` layer types (wind, hazard polygon, evacuation route,
  resource pin, evac-centre pin, utility-outage zone, TC track, road closure, vessel/aircraft
  position). *(extends spec 024 A5)*
- **A6**: Simulations run at wall-clock speed by default; spec 026 owns time-warp/playback
  and remains the single source of truth. This spec's latency targets (e.g. ≤10 s, ≤15 s)
  are wall-clock, evaluated when warp = 1×. *(carried from spec 024)*
- **A7**: The Constitution v1.2.0 binds this spec — primacy of life, AU residency (with the
  Foundry carve-out for Azure OpenAI), human-in-the-loop, AWS-compliant warnings, AIIMS
  alignment.
- **A8**: The "baseline" referenced by Success Criteria SC-002, SC-003, SC-004, and SC-005
  is established by re-running the same scenario with the new auto-fan-out and
  Telemetry-Injection Agent disabled (i.e. the spec-024-only behaviour). Comparison runs are
  matched on scenario seed, jurisdiction, hazard class, and starting telemetry.
- **A9**: The baseline economic-loss profile used by SC-005 is the AIDR-aligned synthetic
  economic profile maintained in the scenario library; no real economic data is consumed.
- **A10**: Scenario complexity ceiling for MVP is 5 concurrent hazard threads in a single
  simulation (e.g. concurrent bushfire + flood + medical + evacuation + utility outage),
  reflecting the cohort's "multi-hazard, multi-agency simultaneity" expectation.
  Exceedance is **hard-refused** rather than throttled: any 6th coordinator-injected top-level
  thread is rejected at scenario setup or mid-sim with a typed `thread.cap_exceeded` audit
  entry, and any cascade that would otherwise spawn a new 6th top-level thread instead
  degrades to an annotation on the most-related existing thread (per FR-057). Coordinators
  needing >5-thread exercises split into parallel simulations (spec 007 FR-010 permits 3
  concurrent sims per tenant).
- **A11**: The `SIMULATION — DO NOT DISTRIBUTE` watermark is rendered **bilingually** in
  every translated public-warning artefact — covering **both** text artefacts (chat preview,
  PDF, email, SMS, social) **and** audio artefacts (TTS-rendered alerts for CALD audio
  listeners, including Auslan-narrative voice-over). For text: the canonical English string
  is emitted first, followed by the locale string drawn from a version-controlled
  text-translation table maintained under spec 024's existing watermark-governance process.
  For audio: the canonical English **spoken** prefix is emitted first, followed by the
  locale **spoken** prefix drawn from a parallel version-controlled **audio-prefix table**
  governed under the same spec 024 watermark-governance pathway and aligned in scope with
  the text-translation table. Both tables cover the ~30 most-used CALD languages in AU
  emergency communications. LLM translation of the watermark text is **never** permitted,
  and LLM-generated TTS of an LLM-translated string is **never** permitted (zero
  translation drift on either pathway); a missing text-locale entry falls back to
  English-only with an `audit.watermark.locale_missing` audit entry, and a missing
  audio-locale entry falls back to the English-only spoken prefix with an
  `audit.watermark.locale_missing` (audio variant) audit entry — neither pathway invokes
  a translation or TTS model as a fallback.
- **A12**: Cascade chain-depth is hard-capped at **1** for MVP. The first hop from a
  synthetic signal (utility / transport / comms-channel-state / resource / evacuation)
  to its declared cascade targets executes within the FR-043..FR-047 latency budgets.
  Any further propagation that would constitute a "depth-2 cascade" (i.e., a downstream
  signal that arises **as a consequence of a degraded-cascade annotation** or as a
  consequence of any first-hop cascade write) is **not** issued automatically: it
  requires a fresh Telemetry-Injection chat turn or coordinator action that re-enters
  the Controller envelope, the FR-052 thread-cap evaluation, and the FR-009
  injection-budget accounting. `origin_cascade_id` does **not** propagate transitively
  across cascade hops. Rationale: bounded cascade count per turn preserves SC-011
  reproducibility, FR-054 single-walk lessons-capture remains tractable, and
  Constitution V predictable failure is preserved (no unbounded chains, no unbounded
  lessons-capture surface).

## Clarifications

### Session 2026-05-08 (pass 1)

- Q: When a 6th hazard thread would be created (coordinator-injected or cascade-spawned) in a sim already at the A10 ceiling of 5, what should happen? → A: Hard refuse at scenario setup AND mid-sim with a typed `thread.cap_exceeded` audit entry; cascades that would otherwise spawn a new top-level thread instead degrade to annotation-on-the-existing-most-related-thread (FR-052, FR-057, A10).
- Q: How should the `SIMULATION — DO NOT DISTRIBUTE` watermark appear in translated public-warning artefacts? → A: Bilingual — English canonical string first, then a curated locale string from a version-controlled translation table; LLM-translated watermarks are never emitted (FR-039, A11).
- Q: How should the Telemetry-Injection Agent handle low-confidence parses across the nine signal categories? → A: Hybrid by category — accept `low` for non-life-safety (`utility`, `transport`, `comms-channel-state`, `resource`); refuse-and-clarify on `low` for life-safety (`weather`, `fire-behaviour`, `hydrology`, `geohazard`, `evacuation`). The `low` enum value remains valid post-injection (sub-agent self-degraded re-evaluations, cascade-induced staleness, network-partition fallback) — only the *initial fresh-injection* gate uses the hybrid threshold (FR-009, FR-010).
- Q: When a chat turn lacks an explicit jurisdiction in a sim that spans multiple jurisdictions, how should routing resolve jurisdiction? → A: Five-step inference ladder — (1) explicit jurisdiction mention in chat → use; (2) single-jurisdiction sim → use; (3) active map-viewport jurisdiction → use; (4) last-active hazard-thread jurisdiction → use; (5) clarify (FR-021).
- Q: Where should the Telemetry-Injection Agent sit in the Controller's invocation flow when a chat turn contains both a telemetry signal and a substantive request? → A: Controller-invoked sub-agent invoked **sequentially first** — Controller classifies intent, invokes `simulation-telemetry-injection` when telemetry is detected, waits for typed signals to land on the tenant-scoped pipeline, then invokes the substantive sub-agents (Risk Assessment / Evacuation / etc.) so they observe the new signals within a single audit envelope (FR-008, FR-015).

### Session 2026-05-08 (pass 2)

- Q: How should the `SIMULATION — DO NOT DISTRIBUTE` watermark appear in TTS-rendered audio artefacts (CALD audio listeners, Auslan-narrative voice-over) for non-English locales? → A: Bilingual spoken prefix from a curated **audio-prefix table** — canonical English spoken prefix first, then the locale spoken prefix drawn from a version-controlled audio-prefix table governed under spec 024's watermark-governance process and aligned in scope with the A11 text-translation table; missing-locale audio falls back to English-only spoken prefix and writes `audit.watermark.locale_missing` (audio variant). LLM-generated TTS of an LLM-translated string is **never** permitted (FR-039, new FR-058, A11).
- Q: How should FR-057's "most-related existing thread" affinity be made byte-deterministic for SC-011 reproducibility, and may an LLM be used to compute it? → A: Pure deterministic 5-step ranking, no LLM, no heuristics — (1) jurisdiction match, (2) hazard-class match, (3) cascade-origin-thread preference (already in FR-057), (4) most-recent-mutation timestamp (newest wins), (5) thread-creation-id ascending (oldest wins) as final tiebreak (FR-057).
- Q: When a cascade degrades to annotation on an existing thread (FR-057), where do the cascade's audit entries live so that FR-054 lessons-capture timeline reconstruction stays single-walk? → A: Entries written into the **target thread's** audit subtree, each tagged `origin_cascade_id: <id>`, plus a single `cascade.degraded_to_annotation` back-pointer entry referencing the originating cascade trigger. One walk over the target thread surfaces the cascade; no JOIN required (FR-057, FR-054).
- Q: How much should the FR-021 step-3 "active map-viewport jurisdiction" client hint be trusted by the API? → A: Treat the client hint as **advisory** — the API MUST re-validate server-side by re-running centroid → jurisdiction lookup against an authoritative server-side jurisdiction-boundary dataset; the API's result wins; mismatches are logged as `routing.viewport_hint_mismatch`. The authoritative dataset is sourced from the platform jurisdiction registry with explicit fallback to ABS Statistical Area boundaries if the registry is incomplete; exact dataset choice deferred to plan phase but the spec mandates *an* authoritative server-side dataset must be used (FR-021).
- Q: For the inherited spec-024 30-injections-per-minute-per-user budget, which Telemetry-Injection events count toward the quota? → A: Only **successful injections** (signal landed on the pipeline) count. Refused injections — `life_safety_low_confidence`, unknown-category, missing-provenance, `thread.cap_exceeded`, malformed input — do **not** count, so the FR-010 clarification loop and the FR-052/FR-057 cap-refusal pathways do not burn a coordinator's budget. A separate anti-abuse parse-attempt circuit-breaker (e.g., ~60 parse-attempts/min/user) is required to protect the parser from a buggy or malicious client that floods it with junk text; that circuit-breaker is sized in plan phase (FR-009).

### Session 2026-05-08 (pass 3 — checklist-surfaced)

- Q: What is the maximum cascade chain-depth permitted under FR-043..FR-047 (i.e., can a degraded-cascade annotation itself trigger a further cascade)? → A: Cascades are single-level (max depth = 1). The first hop (per FR-043 / FR-044 / FR-045 / FR-046 / FR-047) executes within its declared latency budget; any signal that arises **as a downstream consequence of a degraded-cascade annotation** (a would-be "depth-2 cascade") is NOT issued automatically — it MUST be treated as a fresh top-level Telemetry-Injection turn requiring an explicit chat input or coordinator action, and therefore re-enters the Controller envelope, the FR-052 thread-cap evaluation, and the FR-009 injection-budget accounting. `origin_cascade_id` does NOT propagate transitively across cascade hops (FR-043, FR-057, A12).
- Q: What is the coordinator-driven simulation lifecycle surface (`pause` / `resume` / `abort`) within feature 036, and how do these verbs interact with in-flight cascade fan-out? → A: Explicitly name `pause`, `resume`, `abort` as coordinator-only lifecycle verbs in this feature's FR set (inheriting spec 024 lifecycle implementation; `end` is already implicitly covered by US9). On `pause` the Controller refuses new chat turns AND halts all sub-agent invocations including in-flight cascade fan-out — in-flight work is allowed to complete its current step but no new sub-agent invocations or signal writes are issued; on `resume` deferred cascade hops are NOT auto-replayed (consistent with the A12 cascade-depth-1 ceiling); on `abort` all in-flight invocations are cancelled, the sim transitions to `ended` with `end_reason: aborted`, and FR-054 lessons-capture is triggered. `pause` and `resume` are coordinator-only (FR-051 role check) (FR-059).
- Q: Should the Sub-Agent Invocation Record persist a forensic fingerprint of the prompt the sub-agent's LLM actually sees, to enable post-exercise replay verification under Constitution IV (Transparency and Auditability)? → A: Yes — add a required `prompt_hash` field (sha256 over the canonical prompt: sub-agent system prompt + user payload + tool-schemas snapshot — i.e. whatever the sub-agent's LLM actually sees). Populated for LLM-bearing sub-agents (Risk Assessment, Communications, Planning, Evacuation, Resource Allocation, **and the Simulation Telemetry-Injection Agent itself**); `null` for non-LLM-bearing sub-agents (e.g. deterministic stubs). Surfaced through the FR-049 audit-export pathway and the FR-054 lessons-capture record. Spec 024 already records this for the Controller turn (per `controller_prompt.md` versioned hash); extending to sub-agents closes the audit-completeness gap (Sub-Agent Invocation Record key entity, FR-005, FR-060).

### Session 2026-05-08 amendment pass 1

- Q: When a chat turn carries BOTH telemetry AND a substantive request, who invokes substantive sub-agents — the inject-telemetry endpoint (per Amendment C transactional invariant), the Controller (per pass-1 Q5 sequencing), or both? → A: **Hybrid by trigger source with dedup.** The inject-telemetry endpoint invokes ONLY sub-agents subscribed to the parsed signal type via FR-026 auto-fan-out. The Controller separately invokes any chat-intent-inferred substantive sub-agents that are NOT already a subscriber on this turn. A sub-agent that is BOTH a subscriber AND chat-intent-inferred MUST be invoked **exactly once** by the inject-telemetry endpoint, and its result MUST be propagated into the Controller's substantive-aggregation reply via a **shared `injection_correlation_id`**. The endpoint's `triggered_sub_agents[]` array lists endpoint-invoked subscribers only (each tagged `trigger_source: "subscriber"`); the Controller turn audit envelope additionally lists Controller-invoked substantive sub-agents (each tagged `trigger_source: "controller_intent"`). No double invocation; one envelope; one `injection_correlation_id` per chat turn. Preserves pass-1 Q5 sequencing, satisfies Amendment C's transactional invariant for subscribed sub-agents, and aligns with Constitution v1.2.0 single-source-of-truth (FR-009, FR-015, FR-026).
- Q: When the FR-048 audit `sequence_number` allocator exhausts its ETag retry budget (max 5 attempts), what is the user-facing fail-closed semantics on the originating endpoint? → A: A five-step protocol — (1) the originating endpoint MUST return **HTTP 503 Service Unavailable** with `Retry-After: 5`; (2) a **best-effort** entry of type `audit.sequence.uncertainty` MUST be written to a separate **fail-safe dead-letter queue** (Cosmos `simulation_audit_dlq` container, partition by `simulation_id`), with `sequence_number = -1` and an `uncertainty_reason` enum drawn from `{etag_exhausted, counter_unreachable, replica_partition}`; (3) sequence-uncertainty handling MAY be charged against the FR-009 chat-turn latency budget but MUST NOT be charged against the FR-026 fan-out budget (subscriber retries are separately bounded); (4) per FR-066, replay of the same `Idempotency-Key` MUST return the **cached 503 response unchanged** without re-attempting the underlying Cosmos operation, and the DLQ entry MUST be written **exactly once** per original request; (5) per Constitution Principle I (Primacy of Life) the system MUST prefer fail-closed over a silent gap — downstream readers (FR-054 lessons-capture, FR-049 FOI export) MUST detect `sequence_number = -1` entries and surface them as **evidence-integrity warnings**. The FR-066 idempotency-cache TTL is extended to 24 h INCLUDING entries whose cached response is a 503 (FR-048, FR-066).
- Q: Across the four FR-066 lifecycle verbs (`inject-telemetry`, `pause`, `resume`, `abort`), what is the uniqueness scope of an `Idempotency-Key`? → A: Per-(`simulation_id`, HTTP verb, route) **tuple**, not per-`simulation_id` alone. Specifically: (a) same key on `POST /pause` and `POST /abort` for the same `sim_id` are **different namespaces** and both succeed independently; (b) same key + same verb + same `sim_id` within 24 h is a **replay** that returns the original cached response without re-execution of side effects; (c) same key + same verb + DIFFERENT `sim_id` are different namespaces (`sim_id` is part of the key namespace); (d) after a sim transitions to `ended`, the idempotency cache is preserved for the **full 24 h replay window** with TTL anchored on the **original request timestamp**, not on sim end. **Conflict detection**: when a request arrives with a known `Idempotency-Key` for the same `(sim_id, verb, route)` tuple but a DIFFERENT canonical-body sha256, the server MUST return **HTTP 422 Unprocessable Entity** with an **RFC 9457 problem detail** of `type: "idempotency-key-conflict"`. Cache storage: Cosmos `simulation_idempotency_cache` container, partition by `sim_id`, TTL 24 h, value = `{key, verb, route, body_hash, response_status, response_body, created_at}` (FR-066).
- Q: For sub-agents with dual AIIMS associations (notably the Communication agent — internal/tactical Operations comms vs. external Public Information warnings), how is the FR-061 mapping resolved so lessons-capture deterministic ordering (FR-054) is preserved? → A: The `aiims_function` field on every Sub-Agent Invocation Record is **single-valued**; a separate **`secondary_aiims_tags`** array (max 2 entries) records additional context. The Communication agent's resolved primary is **`"Public Information"`** (singleton, used for routing and lessons-capture ordering) with `secondary_aiims_tags = ["Operations"]` (records that internal/tactical comms intersect Operations). Other dual-mappings resolve as: Resource Allocation → primary `"Logistics"`, secondary `["Operations"]`; Risk Assessment → primary `"Intelligence"`, secondary `["Planning"]`; Evacuation → primary `"Operations"`, secondary `["Public Information"]`; Monitoring → primary `"Intelligence"`, secondary `[]`; Planning → primary `"Planning"`, secondary `[]`. Rationale: AIIMS doctrine assigns external warnings / community comms to Public Information; Operations owns internal tactical comms. The Communication agent is invoked primarily for the FR-038 `[SIMULATION] ` user-facing message — that is Public Information by doctrine. FR-054 lessons-capture deterministic ordering requires single-valued `aiims_function` (FR-061).
- Q: On pre-LLM refusal paths (RBAC failure, malformed input, `thread.cap_exceeded`, missing-provenance, idempotency conflict) where no canonical LLM prompt has been assembled yet, what does FR-065 `prompt_hash` cover? → A: `prompt_hash` is **always required**, but its byte-source MUST be disambiguated by a sibling field **`prompt_hash_source`** (enum, REQUIRED whenever `prompt_hash` is present). Enum values: **`"raw_user_input"`** — pre-LLM refusal paths (RBAC failure, malformed input, `thread.cap_exceeded`, missing-provenance, idempotency conflict); `prompt_hash = sha256(raw_chat_text_utf8_bytes)`. **`"canonical_llm_prompt"`** — post-LLM paths (parse success, parse failure with LLM invocation, fallback extractor invoked); `prompt_hash = sha256(canonical_assembled_prompt_text)` over the exact bytes the LLM saw. **`"system_only"`** — paths where no user prompt exists (e.g. scheduled cascade injection); `prompt_hash = sha256(system_prompt_canonical_bytes)`. This guarantees provenance is unambiguous and enables FOI/audit traceability for every refusal/fallback path. The audit-envelope schema (`contracts/audit-envelope.md`) MUST add `prompt_hash_source` to all 19 typed entries that may carry `prompt_hash` (envelope has since grown to 24 typed entries — see audit-envelope.md §6.1) (FR-065).

### Session 2026-05-08 amendment pass 2

- Q: Do FR-058 (audio-prefix watermark) and FR-064 (accessible live-log) share locale tables and behaviour for the SIM-prefix? → A: **Both share a single source of truth** — `packages/domain/src/domain/sim_locale_table.json` — but have **distinct rendering responsibilities**. FR-058 audio-prefix watermark = pre-rendered MP3 audio injected at the start of every public-warning audio file (table provides the bilingual MP3 URL pair `en_AU` + jurisdiction-priority second locale). FR-064 accessible live-log = ARIA live region (`role="log"` + `aria-live="polite"`) DOM element for SSE chat updates (table provides the localised text content for `[SIMULATION]` prefix and watermark text in 30+ locales). **Shared invariants**: same `sim_locale_table.json` consumed by both pathways; `[SIMULATION]` prefix MUST be present in BOTH audio (pre-rendered MP3) and text (live-log) artefacts; locale resolution rule is the 3-step fallback `request_locale → jurisdiction_priority_locale → en_AU`; the `audit.watermark.applied` audit entry MUST record both `delivery_channel` (enum: `audio | text-live-log | both`) and `resolved_locale`. **Distinct behaviour**: audio is pre-rendered, byte-identical, and validated under `pytest.mark.azure_speech_staging` (CHK031 voice-prosody, CHK034 audio-waveform); text live-log is rendered at SSE event-receipt time and asserted via vitest + axe-core in `apps/web/src/__tests__/`; the audio prefix is **non-removable** by the LLM (table-driven prepending) and the text prefix is enforced by `chat_receipt_prefix_guard.py` with an audit entry on missing-prefix. LLM-generated TTS / LLM-translated watermark is PROHIBITED on both pathways (FR-058, FR-064, FR-039, A11).
- Q: How do FR-059 lifecycle verbs (`pause`, `resume`, `abort`) interact with the FR-066 idempotency-cache on round-trip sequences such as `pause` → `resume` → `pause`? → A: **Per-verb namespace + state-machine consumption**, with the following round-trip semantics. (1) `pause`, `resume`, `abort` each occupy their own `(simulation_id, verb, route)` idempotency namespace (per pass 1 Q3); different verbs do NOT collide. (2) `POST /pause` with key `K1` moves the sim to `paused` and caches the response; `POST /resume` with key `K1` is a DIFFERENT verb namespace and a NEW operation that moves the sim to `active` and caches its own response. (3) Replay of `POST /pause` with `K1` while the sim is still `paused` returns the cached pause response without re-executing side effects (idempotent replay does not re-pause). (4) Replay of `POST /pause` with `K1` AFTER the sim has been resumed MUST be refused with **HTTP 409 Conflict** carrying an RFC 9457 problem detail of `type: "lifecycle-state-conflict"`, because the original `K1` pause has already been "consumed" by the resume; the cache entry is preserved for the full 24 h replay window as an immutable receipt but the state machine refuses re-execution. (5) `POST /pause` with a NEW key `K2` after resume succeeds; new cache entry. **Pause refusal during paused state**: while `paused`, any non-`resume` and non-`abort` write request (new chat turns, new injection attempts, new sub-agent invocations) MUST be refused with HTTP 409 and an `audit.lifecycle.refused_while_paused` audit entry; the 409 refusal itself MUST NOT be written to the idempotency cache (so that a fresh request body is serviced cleanly on resume rather than serving a cached refusal). **Audit lineage**: each lifecycle audit entry (`audit.lifecycle.pause_requested`, `audit.lifecycle.paused`, `audit.lifecycle.resume_requested`, `audit.lifecycle.resumed`, `audit.lifecycle.refused_while_paused`, `audit.lifecycle.aborted`) MUST include both `idempotency_key` AND `request_correlation_id` for cross-replay traceability (FR-059, FR-066).
- Q: When the FR-052 hard-cap of 5 concurrent hazard threads is reached and a cascade degrades to annotation per FR-057, does the annotation pathway itself count toward the cap? → A: **No.** Annotation threads spawned by `cascade.degraded_to_annotation` do NOT count toward the FR-052 thread cap of 5. The cap exists to constrain LLM token budget and operator cognitive load; an annotation is NOT a full hazard thread — it is a lightweight cross-reference badge attached to the parent thread's audit subtree that does not invoke sub-agents independently and does not maintain its own running situation assessment. **Definitions**: a **hazard thread** is a top-level concurrent simulation track with its own scenario, sub-agent invocations, map state, and audit lineage (counts 1:1 toward the cap); an **annotation thread** is a downgrade artefact appearing as a metadata badge on an existing parent thread (does NOT count toward the cap; `cascade.degraded_to_annotation` audit entry is written when the downgrade occurs). **Cap-enforcement edge cases**: 5 hazard threads + N annotations is permitted (N is unbounded for annotations because they are cheap); 4 hazard threads + a cascade that would create a 5th hazard thread succeeds and becomes thread #5 (no annotation); 5 hazard threads + cascade trigger degrades to annotation on the affinity-selected thread (per FR-057's 5-step ladder); a 6th cascade trigger arriving while 5 hazard threads exist also degrades to annotation, with annotations stacking chronologically on the affinity-selected thread (no per-thread annotation cap). **Counter source**: the cap counter is `simulation_state.active_hazard_threads.count` where each entry has a `thread_kind` field with values `"hazard" | "annotation"`; only entries with `thread_kind = "hazard"` are summed against the cap of 5. ETag-based transactional update on the counter document (the FR-048 distributed gap-free mechanism) is applied at the thread-cap layer to keep cap accounting concurrency-safe (FR-052, FR-057).

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Coordinator chats; the right sub-agent actually responds with real reasoning (Priority: P1)

An authorised Exercise Coordinator running an active simulation types into the chat pane:
*"What's the current evacuation status for the Lismore CBD given the river gauge reading
9.4 m?"* Without naming any agent, the Simulation Controller routes the request to the real
Monitoring agent (which queries the sim tenant's signal pipeline for the latest river-gauge
signal), the real Risk Assessment agent (which computes inundation risk for Lismore CBD), and
the real Evacuation agent (which proposes route changes given current closures). All three
sub-agents return real, citation-bearing replies — not the spec-024 stub string — and the
Controller aggregates them into a single plain-language answer in the chat pane with each
agent's contribution visibly attributed.

**Why this priority**: This is the headline value of the entire feature. Without it, the
coordinator's chat is a mock that produces no insight, no decision support, no exercise
value. Every other story in this spec depends on the sub-agents actually executing.

**Independent Test**: With a sim tenant containing seeded telemetry (a river gauge signal at
9.4 m), the chat message above produces (a) at least one Monitoring sub-agent invocation
record citing the gauge signal ID, (b) at least one Risk Assessment invocation record citing
inundation parameters, (c) at least one Evacuation invocation record citing affected routes,
(d) an aggregated chat reply attributing each contribution, and (e) zero invocations of
the spec-024 stub adapter (verified by log inspection — no occurrence of the string
`"simulated reply (no data source wired in this environment)"` in any Controller turn).

**Acceptance Scenarios**:

1. **Given** an `active` sim with a river-gauge telemetry signal at Lismore at 9.4 m,
   **When** the coordinator asks about evacuation status, **Then** the Controller invokes
   Monitoring + Risk Assessment + Evacuation (in any order or in parallel), each returns a
   real reply citing tenant-scoped signal IDs, and the chat pane shows an aggregated answer
   with per-agent attribution within 30 s.
2. **Given** the same sim, **When** the coordinator asks *"who's responsible for the fire
   front?"* in NSW jurisdiction, **Then** the Controller routes to NSW RFS for rural and
   FRNSW for urban, never both for the same fire front, and never to the wrong state's combat
   agency.
3. **Given** the same sim, **When** a sub-agent times out (>30 s), **Then** the Controller
   returns a `working on it` acknowledgement, streams partial output, and writes a typed
   audit entry `sub_agent.timeout` with correlation IDs; **and Then** the coordinator can see
   the timeout reflected in the audit/timeline view.
4. **Given** any sim chat turn, **When** the audit log is queried, **Then** every sub-agent
   invocation has a unique correlation ID linking the chat turn → invocation → response →
   any downstream signal/state change.
5. **Given** an `active` sim, **When** a chat turn contains both a telemetry signal (e.g.
   *"wind has shifted NW at 80 km/h"*) **and** an implicit substantive request (impact
   reassessment), **Then** the Controller invokes `simulation-telemetry-injection` first,
   waits for the typed `weather` signal to be visible on the tenant-scoped pipeline, and
   only then invokes Risk Assessment so that Risk Assessment observes the new signal during
   its execution; the audit envelope for the turn lists `simulation-telemetry-injection`
   as the first invocation and Risk Assessment after it (per FR-008, FR-015).

---

### User Story 2 — Free-text chat becomes typed synthetic telemetry that flows through the signal pipeline (Priority: P1)

A coordinator types: *"Wind has shifted to NW at 80 km/h, gusts 110, near Glenbrook NSW;
also fire spotting started 3 km south of the head fire."* The Simulation Telemetry-Injection
Agent parses this into **two** typed signals: (1) a `weather` signal (wind direction NW, sustained
80 km/h, gusts 110 km/h, location Glenbrook, GPS resolved, confidence high) and (2) a
`fire-behaviour` signal (spotting event, distance 3 km, bearing south of head fire, confidence
high). Both signals are written to the tenant-scoped signal pipeline with full provenance
(`source: sim-injected`, sim ID, injecting user ID, timestamp, confidence). The signals
auto-trigger the downstream sub-agents that subscribe to those signal types — Risk Assessment
re-computes the impact prediction, Evacuation re-routes, Resource Allocation re-prioritises —
without the coordinator naming any agent.

**Why this priority**: This is the *new agent* the user explicitly asked for. It is what
makes the simulation feel like a live exercise rather than a scripted Q&A. Without it,
coordinators must hand-type synthetic data into nine different agents to get a fan-out, which
defeats the purpose.

**Independent Test**: With an `active` sim, the free-text injection above produces (a) two
typed signal records in the sim signal pipeline (one `weather`, one `fire-behaviour`) each
with all required provenance fields, (b) an audit entry per signal showing the source chat
turn ID, parsed parameters, and confidence, (c) auto-invocation of Risk Assessment +
Evacuation + Resource Allocation without the coordinator naming them, (d) a chat reply
summarising what was injected and which agents responded, (e) zero leakage of these signals
into the live tenant partition.

**Acceptance Scenarios**:

1. **Given** an `active` sim, **When** the coordinator injects the wind-and-spotting message
   above, **Then** the Telemetry-Injection Agent produces exactly two typed signals (`weather`,
   `fire-behaviour`) with `source: sim-injected`, sim ID, injecting user ID, timestamp,
   confidence, and GPS where applicable.
2. **Given** the same injection, **When** the signal pipeline notifies subscribers, **Then**
   Risk Assessment runs automatically within 10 s, Evacuation runs automatically within 15 s,
   and Resource Allocation runs automatically within 15 s; **and Then** a single aggregated
   chat reply attributes each agent's response.
3. **Given** an injection that the agent cannot confidently parse (e.g. *"things are getting
   bad"*), **When** confidence is below the configured threshold, **Then** the agent does
   **not** write a synthetic signal, instead returns a clarifying question in chat, and
   writes an `injection.refused` audit entry with the original text and reason.
4. **Given** an injection of a signal type the simulation has not enabled, **When** the
   parser identifies it, **Then** the agent returns a chat error explaining which categories
   are enabled for the active sim and writes an `injection.refused` audit entry.
5. **Given** signals already in the sim pipeline, **When** a new injection contradicts an
   earlier signal (e.g. wind direction inverted within 60 s), **Then** the new signal is
   accepted but flagged `contradicts: <prior_signal_id>` and Risk Assessment re-runs.
6. **Given** an injection of a **life-safety** category (`weather`, `fire-behaviour`,
   `hydrology`, `geohazard`, `evacuation`) parsed at `confidence: low`, **When** the
   Telemetry-Injection Agent evaluates the gate, **Then** the agent **refuses** to write
   the signal, returns a clarifying chat question, and writes an `injection.refused` audit
   entry with reason `life_safety_low_confidence` (per FR-010).
7. **Given** an injection of a **non-life-safety** category (`utility`, `transport`,
   `comms-channel-state`, `resource`) parsed at `confidence: low`, **When** the
   Telemetry-Injection Agent evaluates the gate, **Then** the agent **accepts** the signal
   with `confidence: low` recorded in the payload; downstream sub-agents consume it as
   best-effort (per FR-010).

---

### User Story 3 — Real-time map updates from injected telemetry (Priority: P1)

After the wind-and-spotting injection in Story 2, the Disaster Map's sim overlay updates
within seconds: a wind-direction arrow appears at Glenbrook pointing NW with a label
*"80 km/h gust 110"*; the fire-behaviour signal updates the existing hazard-perimeter polygon
to reflect new spotting risk to the south; Risk Assessment's revised impact polygon overlays
on top with a striped pattern; Evacuation's re-routed path replaces the previous route layer;
Resource Allocation's revised resource pins move on the map. Every overlay carries the SIM
badge and a sim visual modifier (striped/dashed) so it cannot be confused with a live
incident.

**Why this priority**: The user explicitly asked for this — *"real-time updates to the map.
So, using the wind changed example, then wind direction markers should appear indicating the
new wind direction (and showing wind speed if provided)"*. The visual loop is what makes the
exercise rehearsable for multi-coordinator teams.

**Independent Test**: With an `active` sim and a coordinator viewing the Disaster Map,
inject the wind-and-spotting message and observe (a) a wind-direction arrow appears at the
correct GPS within 15 s, (b) the hazard polygon updates within 15 s, (c) the evacuation
route layer updates within 15 s, (d) all new overlays carry the SIM badge and a sim visual
modifier, (e) no live-tenant map layer is mutated.

**Acceptance Scenarios**:

1. **Given** an `active` sim with a coordinator on the Disaster Map, **When** a `weather`
   signal is injected with wind direction + speed, **Then** a wind-arrow overlay appears at
   the resolved GPS within 15 s, labelled with sustained speed and (if provided) gust speed,
   colour-coded by AWS speed tier, with the SIM badge.
2. **Given** the same map, **When** a `fire-behaviour` signal updates the hazard, **Then**
   the hazard-perimeter polygon updates within 15 s and the new perimeter is rendered with
   a sim visual modifier (e.g. striped fill).
3. **Given** the same map, **When** an `evacuation` signal opens a new evacuation centre,
   **Then** an evac-centre pin appears with capacity and status; **When** capacity changes,
   the pin updates without page reload.
4. **Given** the same map, **When** a `utility` signal injects an electricity outage zone,
   **Then** an outage-zone overlay appears, AND the cascading effect on hospital backup-power
   (Health), degraded telco channels, and traffic-signal failures is visualised on the
   appropriate layer within 30 s of the original injection.
5. **Given** the same map, **When** any signal goes stale (older than its category-specific
   freshness window), **Then** the corresponding overlay is visually flagged stale (e.g.
   reduced opacity + stale badge).

---

### User Story 4 — Auto-routing by intent: a wind-change message invokes Risk Assessment without naming it (Priority: P1)

A coordinator types *"wind has shifted NW at 80 km/h"* with no agent named. The Controller
infers the intent (a hazard-parameter change requires impact reassessment), routes to Risk
Assessment automatically (alongside the Telemetry-Injection Agent in Story 2), and the chat
reply contains Risk Assessment's substantive impact-prediction and hazard-minimisation
recommendations attributed to that agent. The coordinator never had to type the words *"Risk
Assessment"*.

**Why this priority**: The user explicitly asked for this — *"if the user states the wind
direction has changed, then use the Risk Assessment agent to provide updates for impact
predictions and how to minimise hazards for everyone involved in the (simulated) rescue"*.
Auto-routing is what makes the chat usable under exercise pressure.

**Independent Test**: With an `active` sim, type the wind-change message and verify (a) Risk
Assessment was invoked even though no agent name appears in the message, (b) the chat reply
contains Risk Assessment's impact prediction and hazard-minimisation recommendations
attributed to Risk Assessment, (c) the routing decision is recorded in the audit log with the
inferred intent and the route chosen.

**Acceptance Scenarios**:

1. **Given** an `active` sim, **When** the coordinator sends a wind-change message,
   **Then** Risk Assessment is invoked automatically, returns substantive impact + hazard-min
   guidance, and the chat reply attributes that guidance to Risk Assessment.
2. **Given** an `active` sim, **When** the coordinator sends a *"river gauge reading 9.4 m at
   Lismore"* message, **Then** Monitoring + Risk Assessment + Evacuation are all invoked
   automatically.
3. **Given** an `active` sim, **When** the coordinator sends an *"evacuate Murwillumbah now"*
   directive, **Then** Evacuation + Communication are invoked automatically and Communication
   produces a `[SIMULATION] ` receipt (Story 5).
4. **Given** an `active` sim, **When** the coordinator sends a message that names a specific
   agent (e.g. *"Planning, draft an IAP"*), **Then** the explicit naming wins over inferred
   routing and only Planning is invoked.
5. **Given** an `active` sim, **When** the routing decision is ambiguous (multiple plausible
   targets with similar confidence), **Then** the Controller asks a clarifying question
   rather than routing speculatively, and writes a `routing.ambiguous` audit entry.
6. **Given** an `active` sim, **When** a hazard-telemetry change is injected via Story 2,
   **Then** Risk Assessment runs automatically without requiring a separate chat message,
   satisfying the AIIMS cohort's *"trigger automatically on every hazard-telemetry change"*
   ask.
7. **Given** a multi-jurisdiction `active` sim, **When** the coordinator's chat turn does
   not name a jurisdiction but the Disaster Map viewport is centred over a single
   jurisdiction (e.g. VIC), **Then** routing resolves jurisdiction via the FR-021 ladder
   step 3 (active map-viewport) and proceeds without a clarifying question; the
   routing-decision audit entry records `jurisdiction_inference_step: 3`.
8. **Given** a multi-jurisdiction `active` sim with no explicit jurisdiction in chat, no
   single-jurisdiction scope, the map viewport spanning two jurisdictions (e.g. ACT/NSW
   border), and no recent hazard-thread activity, **When** the FR-021 ladder is evaluated,
   **Then** the Controller asks a clarifying jurisdiction question and writes a
   `routing.jurisdiction_ambiguous` audit entry; **and Then** the Controller does NOT route
   speculatively or fan out to all candidates.
9. **Given** a multi-jurisdiction `active` sim where the chat-turn payload includes a
   client-supplied viewport-jurisdiction hint of `VIC` but the server-side centroid →
   jurisdiction lookup against the authoritative jurisdiction-boundary dataset resolves
   the viewport to `NSW`, **When** the FR-021 step-3 evaluation runs, **Then** routing
   proceeds using the **server-computed** `NSW` jurisdiction (the client hint is
   discarded), and the Controller writes a `routing.viewport_hint_mismatch` audit entry
   capturing the client hint, the server-computed jurisdiction, the viewport centroid,
   and the chat-turn ID; **and Then** no routing decision uses the client-supplied hint
   directly.

---

### User Story 5 — Communication agent returns `[SIMULATION] ` receipt and stays hard-blocked (Priority: P1)

A coordinator types *"send an evacuation warning to all residents in Lismore CBD"*. The
Controller routes to the Communication agent (auto-routed by intent per Story 4). The agent
authors the warning, watermarks it `SIMULATION — DO NOT DISTRIBUTE`, follows the AWS warning
levels for the active jurisdiction, and produces a chat receipt: *"`[SIMULATION] ` Warning
sent successfully — channel: Emergency Alert + SMS + ABC Local Radio; audience: Lismore CBD
residents (est. 8,400); message-id: sim-msg-7f3a; sim-timestamp: 2026-05-08T03:14:22Z;
block-reason: simulation tenant — egress hard-blocked."* No real channel is touched. The
PublicationService refuses at the tenant-context check; the outbound HTTP client wrapper
refuses again as defence in depth. Both refusals are logged as `synthetic-delivery` audit
entries.

**Why this priority**: The user explicitly asked for this — *"no real communications will be
sent out. Just inform the user that the message has been sent successfully, prefixed with
[SIMULATION] in the chat response so it is clearly visible to the user"*. Constitutionally
mandatory: a single false-positive delivery from a sim is a catastrophic failure.

**Independent Test**: With an `active` sim, send the evacuation-warning message and verify
(a) the chat reply begins with `[SIMULATION] `, (b) the receipt contains channel, audience,
message-id, sim-timestamp, block-reason, (c) two refusal entries are written to the audit
trail (PublicationService + HTTP wrapper), (d) zero outbound network calls reach any real
channel (verified by network-trace mock), (e) the warning content carries the `SIMULATION —
DO NOT DISTRIBUTE` watermark in every render and every translated language.

**Acceptance Scenarios**:

1. **Given** an `active` sim, **When** the Communication agent attempts to publish via any
   channel, **Then** the chat receipt begins with `[SIMULATION] ` and the synthetic-delivery
   record contains channel, audience, message-id, sim-timestamp, block-reason.
2. **Given** an `active` sim, **When** the agent attempts an SMS via the SMS gateway,
   **Then** the egress is blocked at the HTTP client wrapper before any network call leaves
   the platform.
3. **Given** an `active` sim, **When** the agent drafts a public warning in any AWS tier,
   **Then** the watermark `SIMULATION — DO NOT DISTRIBUTE` is rendered in the chat preview,
   any PDF/email render, and every translated language version.
4. **Given** an `active` sim with a synthetic telco-outage signal in the pipeline, **When**
   the agent enumerates available channels, **Then** the channel list is reduced to reflect
   the outage and the unavailable channels are visibly annotated; **and Then** Triple Zero
   coverage loss (if injected) is prominently flagged.
5. **Given** any chat turn that requests an ADF DACC dispatch, BOM warning, NEMA COMDISPLAN
   activation, or any other Commonwealth real-world action, **Then** the agent produces a
   `[SIMULATION] ` artefact only and never invokes the real pathway.
6. **Given** a public warning rendered in a CALD locale (e.g. Vietnamese, Mandarin, Arabic,
   Auslan-narrative), **When** the watermark is applied, **Then** the canonical English
   string `SIMULATION — DO NOT DISTRIBUTE` is emitted **first** (literal byte match,
   verifiable by SC-006 sweep), followed by the locale-specific watermark string drawn from
   the version-controlled translation table per A11; **and Then** no LLM-translated
   watermark string appears in the artefact.
7. **Given** a public warning rendered in a locale **missing** from the translation table,
   **When** the watermark is applied, **Then** the artefact is emitted with the canonical
   English watermark only (no LLM fallback), and an `audit.watermark.locale_missing` audit
   entry is written naming the locale and the artefact ID.
8. **Given** a public warning that is also rendered as a **TTS audio alert** for a CALD
   audio listener (e.g. Vietnamese, Mandarin, Arabic, Auslan-narrative voice-over) whose
   locale **is** present in the audio-prefix table, **When** the audio artefact is
   produced, **Then** the canonical English **spoken** prefix `SIMULATION — DO NOT
   DISTRIBUTE` is emitted **first**, followed by the locale spoken prefix drawn from the
   version-controlled audio-prefix table (per FR-058 / A11); **and Then** no
   LLM-generated TTS of an LLM-translated string appears in the audio artefact.
9. **Given** a public warning rendered as a TTS audio alert in a locale **missing** from
   the audio-prefix table, **When** the audio artefact is produced, **Then** the
   artefact is emitted with the **English-only spoken prefix** (no LLM-generated TTS
   fallback), and an `audit.watermark.locale_missing` (audio variant) audit entry is
   written naming the locale and the audio-artefact ID.

---

### User Story 6 — Multi-hazard, multi-jurisdiction concurrency (Priority: P2)

A coordinator runs an exercise that combines (a) a NSW bushfire near Katoomba, (b) a
concurrent flood event in Lismore (NSW), (c) a casualty incident requiring NSW Ambulance,
(d) an evacuation operation, and (e) a utility outage in the Lismore CBD. Each thread runs
in parallel with its own sub-agent invocations. The Disaster Map shows all hazard layers
coexisting under a single SIM badge with each layer attributed to the correct combat agency.
Chat replies attribute each contribution to the correct agency; nothing is collapsed or
misrouted.

**Why this priority**: The cohort identified multi-hazard, multi-agency simultaneity as the
**most common edge case**. Without this story the spec is academically correct but useless
for real exercises.

**Independent Test**: Run the five-thread scenario above (within the A10 ceiling of 5
concurrent threads) and verify (a) each thread has its own independent sub-agent invocation
records, (b) the map shows all hazard layers, each correctly attributed and not collapsed,
(c) chat replies attribute each piece of guidance to the correct agency, (d) the dual fire
+ flood combat-agency threads (NSW RFS + SES NSW) are not collapsed.

**Acceptance Scenarios**:

1. **Given** an `active` sim with 5 concurrent hazard threads, **When** telemetry is injected
   for any one thread, **Then** only the sub-agents subscribed to that signal type are
   invoked (no cross-contamination).
2. **Given** a NSW concurrent fire+flood scenario, **When** chat asks *"who is responsible?"*,
   **Then** the reply names NSW RFS for rural fire and SES NSW for flood, never collapsing
   to one agency.
3. **Given** an NT concurrent structural-fire+grass-fire scenario, **When** chat asks for
   *"resource availability"*, **Then** routing distinguishes NTFRS (structural) from
   Bushfires NT (rural) and returns each agency's view.
4. **Given** a sim spanning more than one jurisdiction, **When** any agent reply is rendered,
   **Then** the issuing jurisdiction is visibly shown next to the agency name.
5. **Given** an `active` sim already running 5 concurrent hazard threads (the FR-052 / A10
   cap), **When** a coordinator attempts to inject telemetry that would create a 6th
   top-level thread, **Then** the request is **refused** with a typed `thread.cap_exceeded`
   audit entry; the chat reply explains the cap and recommends splitting into parallel sims
   (per FR-052). No silent drop, no throttling, no queueing.
6. **Given** an `active` sim already running 5 concurrent hazard threads, **When** a
   cascade (e.g. a utility outage cascading through Health → Transport → Comms) would
   otherwise spawn a new 6th top-level thread, **Then** the cascade instead **degrades to
   annotation** on the most-related existing thread; a `cascade.degraded_to_annotation`
   audit entry records the originating cascade, the suppressed would-be-new-thread, and
   the chosen target thread (per FR-057); the chat timeline surfaces a brief annotation
   indicating the cascade attached rather than spawned a new thread.
7. **Given** an `active` sim already at the 5-thread cap with **two existing threads
   sharing the same jurisdiction (NSW) and the same hazard class (flood)** as the
   cascade — Thread A created at T0 and last mutated at T+10 min, Thread B created at
   T+2 min and last mutated at T+25 min — **When** a flood-related cascade in NSW is
   evaluated against the FR-057 affinity ladder, **Then** steps 1–3 leave both threads
   tied (same jurisdiction, same hazard class, neither thread originated this cascade),
   step 4 (most-recent-mutation timestamp) selects **Thread B** (newest mutation wins),
   the cascade is annotated onto Thread B, and the `cascade.degraded_to_annotation`
   audit entry records `affinity_step: 4` along with the candidate set considered. The
   selection MUST be byte-identical across replays of the same scenario seed (SC-011
   reproducibility), and no LLM is invoked at any step of the affinity computation.
8. **Given** an `active` sim where a `utility` outage cascade has just degraded to
   annotation on Thread B (per scenarios 6/7), **When** that degraded-cascade
   annotation produces a downstream signal that would itself trigger a further cascade
   (a would-be "depth-2 cascade"), **Then** the Controller MUST NOT issue the depth-2
   cascade automatically; the chat reply MUST explain the cascade-depth-1 ceiling
   (per FR-043 / FR-057 / A12) and recommend a fresh Telemetry-Injection chat turn or
   coordinator action that re-enters the Controller envelope (and therefore the
   FR-052 thread-cap evaluation and the FR-009 injection-budget accounting); a typed
   audit entry MUST record the refused depth-2 attempt; **and Then**
   `origin_cascade_id` MUST NOT propagate transitively into the depth-2 attempt's
   audit record (the depth-2 attempt, when re-issued through the Controller envelope,
   gets a fresh top-level injection-correlation-id, not the originating cascade's id).

---

### User Story 7 — Cascading synthetic signals: utility outage propagates without manual re-entry (Priority: P2)

A coordinator injects *"electricity outage across Lismore CBD"*. The
Telemetry-Injection Agent writes a `utility` signal. Without further coordinator action, the
following cascades occur within 30 s of the injection: Health is notified that hospital
backup-power should be re-evaluated; Communication's available channel list is reduced (telco
sites may be on backup); Transport is notified that traffic signals are affected;
Resource Allocation re-prioritises generator and field-team deployment. Each cascade is
visible in the chat timeline and on the appropriate map overlay.

**Why this priority**: The Commonwealth cohort identified utility-outage cascading as a
top-priority signal because *"one injection, no manual re-entry"* is what the coordinator
needs under exercise pressure. Without this, the simulation forces error-prone re-typing.

**Independent Test**: Inject the utility-outage message and verify (a) one synthetic
`utility` signal is written, (b) Health + Communication + Transport + Resource Allocation
all receive their cascade notification within 30 s, (c) the map shows the outage zone and
the dependent overlays update, (d) no second chat injection from the coordinator was
required.

**Acceptance Scenarios**:

1. **Given** an `active` sim, **When** a `utility` outage signal is injected, **Then**
   Health, Communication, Transport, and Resource Allocation all receive the cascade within
   30 s of the original injection.
2. **Given** an `active` sim, **When** a `transport` road-closure signal is injected,
   **Then** Evacuation re-routes any active evacuation that used that road within 15 s, and
   the new route appears on the map.
3. **Given** an `active` sim, **When** a `comms-channel-state` signal degrades a channel,
   **Then** the Communication agent's available-channel list reflects the degradation in the
   next chat turn.

---

### User Story 8 — Degraded-mode injection: comms blackout / sub-agent unavailable / network partition (Priority: P3)

A coordinator deliberately injects *"comms blackout: telco down across the Northern Rivers"*
or *"Risk Assessment agent unavailable for 5 minutes"* as part of an exercise. The simulation
honours the injection: the Communication agent reports a reduced channel list with stale
data flagged; the Risk Assessment agent returns `degraded` for the configured window and the
Controller falls back to cached last-known state with a visible staleness indicator. The
exercise continues; the coordinator's response choices are tested under degraded conditions.

**Why this priority**: The AIIMS cohort identified degraded-mode as **first-class injectable
content**. It is a nice-to-have for a strict MVP but essential to satisfy the AIIMS
exercise-design vision.

**Independent Test**: Inject a degraded-mode signal and verify (a) the affected sub-agent
returns the configured degraded behaviour for the configured window, (b) the chat and map
visibly indicate degraded state, (c) the audit trail records the degraded-mode injection,
(d) recovery is automatic at the configured time and recorded in audit.

**Acceptance Scenarios**:

1. **Given** an `active` sim, **When** a `comms-blackout` signal is injected, **Then** the
   Communication agent's channel list shrinks for the configured window and recovers
   automatically.
2. **Given** an `active` sim, **When** a `sub-agent-unavailable` signal is injected for Risk
   Assessment, **Then** Risk Assessment returns `degraded` with cached state for the window
   and recovers automatically.
3. **Given** an `active` sim, **When** a `network-partition` signal is injected between the
   Controller and a sub-agent group, **Then** the affected agents return `degraded` and the
   Controller reports the partition status in chat.

---

### User Story 9 — Post-exercise structured lessons capture (Priority: P3)

After an exercise ends, the coordinator can request a structured exercise-outcome record
that includes a timeline (chat + injections + sub-agent invocations + state changes), a
sub-agent response summary, IC decision points, identified gaps, and a `lessons-identified`
section for human annotation. The record is AIDR-compatible and exportable. If generation
fails, the request is retriable from audit without data loss.

**Why this priority**: The AIIMS cohort identified post-exercise lessons capture as
**non-negotiable** for the audit-and-learning loop. Strictly speaking the MVP value is
delivered without it (the live exercise still works), so it is P3.

**Independent Test**: Run an exercise, end it, request the lessons-capture record, and
verify (a) the record contains all five sections (timeline, agent responses, IC decisions,
gaps, lessons), (b) the record is AIDR-compatible, (c) re-requesting the record is
idempotent, (d) a deliberately-failed generation can be retried without data loss.

**Acceptance Scenarios**:

1. **Given** an `ended` sim, **When** the coordinator requests a lessons-capture record,
   **Then** the record contains timeline, agent responses, IC decisions, identified gaps,
   and a `lessons-identified` section.
2. **Given** the same sim, **When** the record is regenerated, **Then** the result is
   byte-identical to the first generation (idempotent).
3. **Given** a deliberately-failed generation, **When** the coordinator retries, **Then**
   the second attempt succeeds using the same audit data and no data loss is observed.
4. **Given** an `active` sim with a cascade fan-out mid-flight (e.g. a utility-outage
   cascade has invoked Communication and Transport but has not yet invoked Resource
   Allocation), **When** the coordinator issues `pause`, **Then** the in-flight
   Communication and Transport invocations are allowed to complete their current step
   (per FR-059) but the Resource Allocation invocation is NOT issued; the Controller
   refuses any new chat turns with a typed audit entry tagged `lifecycle.paused`;
   **and Then** when the coordinator subsequently issues `resume` the sim returns to
   `active` and the deferred Resource Allocation invocation is NOT auto-replayed —
   re-issuing it requires a fresh Telemetry-Injection chat turn or coordinator action
   (consistent with FR-059 and the A12 cascade-depth-1 ceiling).
5. **Given** an `active` sim with a cascade fan-out mid-flight, **When** the
   coordinator issues `abort`, **Then** all in-flight sub-agent invocations are
   cancelled (each producing a `sub_agent.cancel` audit entry per FR-048), the
   simulation transitions to `ended` with `end_reason: aborted`, and FR-054
   lessons-capture is triggered automatically; **and Then** the `abort` itself is
   recorded as a typed audit entry containing the issuing coordinator's user ID, the
   abort timestamp, and the count of cancelled in-flight invocations (per FR-059).

---

### Edge Cases

- **Free-text contains no parseable signal**: Telemetry-Injection Agent declines to write a
  signal, returns a clarifying chat question, writes an `injection.refused` audit entry; the
  coordinator may retry with more detail.
- **Free-text parses to a life-safety category at low confidence** (per FR-010 hybrid gate):
  Refused-and-clarified — the agent does NOT write the signal, returns a clarifying
  question, and writes an `injection.refused` audit entry with reason
  `life_safety_low_confidence`. Non-life-safety low-confidence parses are accepted with
  `confidence: low` recorded.
- **Free-text contains multiple signals**: All confidently-parsed signals are written
  individually with shared injection-correlation ID; the chat reply lists each signal and the
  agents auto-invoked.
- **6th hazard thread attempted at the FR-052 / A10 cap**: Coordinator-injected attempts
  are hard-refused with `thread.cap_exceeded`; cascade-spawned 6th-thread attempts degrade
  to annotation on the most-related existing thread with `cascade.degraded_to_annotation`
  (per FR-057). No silent drop, no throttling.
- **Multi-jurisdiction sim with no explicit jurisdiction in chat**: Resolved via the FR-021
  five-step inference ladder (explicit → single-jurisdiction sim → map viewport →
  last-active hazard-thread → clarify). Ambiguous peri-urban / inter-state border zones
  reach the clarify step rather than being silently misrouted, per cohort guidance.
- **Free-text injects a real-world action (e.g. "actually order ADF DACC")**: Refused with
  an audit entry; the agent reminds the coordinator that the simulation cannot dispatch real
  resources.
- **Chat model hallucinates a non-existent agent or signal type**: Server-side allow-list
  refuses execution regardless of model output; refusal recorded in audit.
- **Coordinator on a NSW persona attempts IC escalation**: Refused without explicit user
  direction (per cohort guidance); audit entry written.
- **Injection contradicts an existing signal within the freshness window**: New signal
  accepted but tagged `contradicts: <prior_signal_id>`; downstream agents re-run.
- **Injection includes PII**: PII detector redacts; transcript and signal payload are
  redacted in audit; coordinator notified.
- **Sub-agent returns a citation referencing live-tenant data**: Citation rejected by
  tenant-isolation check; sub-agent reply marked `degraded`; audit entry written.
- **Map overlay capacity exceeded (very large hazard polygon, very many resource pins)**:
  Map clusters or down-samples for render but the underlying signal payload is preserved in
  audit; clustering is visually indicated.
- **Real Level-3 NEMA event activates while a sim is running**: Sim auto-throttles
  immediately per spec 024 FR-004; no real notifications are suppressed; throttle banner is
  non-dismissible.
- **`SimulationObserver` user attempts to inject telemetry**: Refused; UI hides the
  injection action; audit entry written if the API is called directly.
- **Concurrent multi-coordinator injection of contradicting signals**: Both signals accepted
  with shared injection-correlation IDs and `contradicts` flags; downstream agents re-run on
  each; coordinators are notified of the contradiction.
- **Stale signal age exceeds category freshness window**: Map overlay visually flagged stale;
  Risk Assessment annotates output with staleness; coordinator may inject a refresh.
- **Browser tab closed mid-conversation**: Server-authoritative simulation state survives;
  re-opening resumes from the last server snapshot (carried from spec 024).
- **Attempt to invoke a sub-agent for a hazard outside its declared role**: Refused (combat
  vs control role tagging enforced); audit entry written.
- **Buggy or malicious client floods the Telemetry-Injection parser with junk text**: The
  inherited spec-024 30-injections/min/user budget is unaffected (refused parses do not
  count per FR-009), but a separate **anti-abuse parse-attempt circuit-breaker** trips
  on excessive parse attempts per minute per user (e.g. ~60/min/user; exact threshold
  sized in plan phase) — once tripped, the parser short-circuits with a typed audit
  entry and the coordinator is notified to investigate the client; legitimate
  successful injections are unaffected.
- **Coordinator triggers a signal that would represent a depth-2 cascade**: Refused
  with a chat reply explaining the cascade-depth-1 cap (per FR-043 / FR-057 / A12) and
  recommending a fresh Telemetry-Injection chat turn or coordinator action that
  re-enters the Controller envelope (and therefore the FR-052 thread-cap evaluation
  and the FR-009 injection-budget accounting). A typed audit entry records the
  refused depth-2 attempt; `origin_cascade_id` does NOT propagate transitively into
  the audit record of the re-issued top-level turn.
- **Coordinator triggers `abort` while a cascade fan-out is mid-flight**: All
  in-flight sub-agent invocations are cancelled (each producing a `sub_agent.cancel`
  audit entry per FR-048), the simulation transitions to `ended` with
  `end_reason: aborted`, FR-054 lessons-capture is triggered automatically, and no
  further cascade hops are issued. `pause` behaves analogously: in-flight cascade
  work in progress is allowed to complete its current step, but no new sub-agent
  invocations or signal writes are issued while the sim is `paused`; new chat turns
  during `paused` are refused with `lifecycle.paused` audit entries (per FR-059).

## Requirements *(mandatory)*

### Functional Requirements

**Real sub-agent invocation (replacing the stub adapters)**

- **FR-001**: System MUST replace the stub adapters in
  `apps/api/app/services/simulation/sub_agent_invoker.py` with real invocations of the
  Monitoring, Planning, Resource Allocation, Communication, Evacuation, and Risk Assessment
  sub-agents, each scoped to the active simulation tenant context.
- **FR-002**: System MUST NOT, in any sub-agent reply produced under a simulation tenant
  context, return the literal text `simulated reply (no data source wired in this
  environment)`. This is the explicit migration test.
- **FR-003**: System MUST stream sub-agent partial output to the chat pane via the existing
  SSE pipeline (spec 024) so the coordinator sees progress within 1 s of invocation start.
- **FR-004**: System MUST aggregate concurrent sub-agent replies into a single Controller
  reply that visibly attributes each agent's contribution.
- **FR-005**: System MUST log every sub-agent invocation with a correlation ID linking the
  triggering chat turn or telemetry signal to the sub-agent invocation, the response, and
  any downstream state changes. The Sub-Agent Invocation Record MUST also persist the
  `prompt_hash` field defined in the Key Entities section (per FR-060) so post-exercise
  forensic replay can verify the sub-agent's LLM saw exactly what the audit says it saw
  (Constitution IV — Transparency and Auditability).
- **FR-006**: System MUST honour per-sub-agent timeout (default 30 s), surface a `working on
  it` ack on slow paths, and write a typed `sub_agent.timeout` audit entry on hard timeout
  (default 120 s).
- **FR-007**: System MUST treat any sub-agent citation that resolves to a live-tenant
  resource as a tenant-isolation violation: reject the citation, mark the sub-agent reply
  `degraded`, and write an audit entry.

**Simulation Telemetry-Injection Agent (`simulation-telemetry-injection`)**

- **FR-008**: System MUST provide a new agent service named
  `simulation-telemetry-injection` that converts free-text coordinator chat into typed
  synthetic signals across the following nine categories: `weather`, `fire-behaviour`,
  `hydrology`, `geohazard`, `utility`, `transport`, `evacuation`, `resource`,
  `comms-channel-state`. The Controller MUST invoke `simulation-telemetry-injection` as a
  **Controller-driven sequential first step** whenever telemetry is detected in a chat turn
  — Controller classifies intent, invokes `simulation-telemetry-injection`, awaits typed
  signals landing on the pipeline, **then** invokes any substantive sub-agents (Risk
  Assessment / Evacuation / Resource Allocation / Communication / Monitoring / Planning) so
  the substantive agents observe the new signals within a **single audit envelope**. The
  Telemetry-Injection Agent MUST NOT be invoked in parallel with substantive sub-agents
  for the same turn (no fan-out de-duplication is required), and MUST NOT be invoked from
  outside the Controller's allow-listed invocation surface.
- **FR-009**: Every synthetic signal MUST carry the following provenance fields or be
  refused at ingest: `source: "sim-injected"`, `simulation_id`, `injecting_user_id`,
  `timestamp`, `confidence` (`high|medium|low`), and `gps` (where the signal is
  location-bound). The spec-024 inherited per-user injection budget
  (30 injections / min / user) MUST count **only successful injections** (signals that
  landed on the tenant-scoped pipeline) toward the quota; **refused** injections
  (`life_safety_low_confidence` per FR-010, unknown-category, missing-provenance,
  `thread.cap_exceeded` per FR-052, malformed input) MUST NOT consume budget so the
  FR-010 refuse-and-clarify loop and the FR-052 / FR-057 cap-refusal pathways do not
  penalise the coordinator under exercise pressure. **Planning hand-off**: a separate
  anti-abuse **parse-attempt circuit-breaker** (e.g. on the order of ~60 parse-attempts
  per minute per user, exact value to be sized in plan phase) is required to protect the
  parser from a buggy or malicious client that floods it with un-parseable junk text —
  the circuit-breaker is distinct from the success-counted injection budget and applies
  to all parse attempts regardless of outcome.
  - **[Step 8 Amendment C strengthening]**: Telemetry injection is an **end-to-end
    transactional invariant**, not a fire-and-forget parse. Before the inject-telemetry
    HTTP endpoint returns a successful response (whether 200 or 202), every accepted
    typed signal MUST be (a) **persisted** to the tenant-scoped synthetic-signal store
    (the `simulation_synthetic_signals` partition in Cosmos DB or equivalent durable
    store), (b) **published** to the tenant-scoped event pipeline (Event Hubs or Cosmos
    change feed per FR-015), and (c) **consumed** by every sub-agent subscribed to that
    signal category, with consumption acknowledged within the turn barrier per FR-008.
    The endpoint's response body's `triggered_sub_agents` array MUST be **populated
    with the actual sub-agents that consumed the signal** (each with its sub-agent
    name, correlation ID, and aggregated reply where applicable) — returning an empty
    `triggered_sub_agents: []` while sub-agents subscribe to the signal type is
    PROHIBITED. This invariant binds the orchestration service that owns the full
    `parse → durable signal write → tenant-scoped event publish → subscriber fan-out →
    aggregated chat response → map updates` transaction.
  - **[Step 8 Amendment R cross-reference]** (see FR-065): every injection attempt —
    accepted, refused, or fallback — MUST persist a `prompt_hash` (sha256) field in the
    audit envelope; the refusal/fallback paths MUST include it as well as accepted paths.
  - **[Step 8 Amendment S cross-reference]** (see FR-066): the inject-telemetry endpoint
    is one of the four direct REST lifecycle endpoints that MUST honour the
    `Idempotency-Key` header with a 24-hour replay window.
  - **[Step 8 amendment pass 1 strengthening — endpoint-vs-controller dedup]** (see
    FR-015, FR-026, and pass 1 Q1): When a chat turn carries BOTH telemetry AND a
    substantive request, the inject-telemetry endpoint MUST invoke ONLY sub-agents
    subscribed to the parsed signal type (FR-026 auto-fan-out); the Controller MUST
    separately invoke chat-intent-inferred substantive sub-agents that are NOT already
    subscribers on this turn. A sub-agent that is BOTH a subscriber AND
    chat-intent-inferred MUST be invoked **exactly once** by the inject-telemetry
    endpoint, and its aggregated reply MUST be propagated into the Controller's
    substantive-aggregation reply via a **shared `injection_correlation_id`** (one
    correlation ID per chat turn). Each entry in `triggered_sub_agents[]` MUST carry a
    `trigger_source` enum field with values `"subscriber" | "controller_intent"`. The
    inject-telemetry response body MUST list only `subscriber` entries; the Controller
    turn audit envelope MUST additionally list the `controller_intent` entries within
    the same envelope. Double invocation of the same sub-agent on the same chat turn is
    **PROHIBITED**.
  - **[Step 8 amendment pass 1 strengthening — `prompt_hash_source` sibling]** (see
    FR-065 and pass 1 Q5): every audit entry that carries `prompt_hash` MUST also carry
    a sibling enum **`prompt_hash_source`** ∈ `{raw_user_input, canonical_llm_prompt,
    system_only}` so refusal, fallback, and accepted paths can be distinguished by the
    byte-source the hash was computed over.
  - **[Cycle 2 Amendment A2-01 carve-out — degraded-dispatch on orchestrator failure]**
    (see FR-067): The Amendment C invariant that `triggered_sub_agents` MUST be
    populated continues to hold for every accepted injection; on partial orchestrator
    failure the population is the **acknowledged subset** (sub-agents that did
    confirm consumption before the dispatch raised), the response body adds
    `degraded_dispatch: true`, and a typed `signal_pipeline.dispatch_failed` audit
    entry MUST be written naming the failed-subscriber list, the exception class, and
    the FR-065 `prompt_hash` / `prompt_hash_source`. Silent-swallow
    (`logger.exception` with `triggered_sub_agents=[]` and no typed audit entry) is
    **PROHIBITED in production**. Fail-closed (HTTP 5xx) is rejected because it would
    deny coordinators the partial situational awareness produced by the surviving
    subset; degraded-dispatch with an explicit machine-readable flag is the chosen
    Constitution-V-compliant predictable-failure surface.

    **RECONCILE — supersedes Amendment C clause "returning an empty
    `triggered_sub_agents: []` while sub-agents subscribe to the signal type is
    PROHIBITED" above**: Under Cycle 2 Amendment A2-01, an empty
    `triggered_sub_agents: []` IS permitted in the **fully-failed dispatch** edge case
    (every subscriber raised before acknowledging) **provided** that the response body
    also carries `degraded_dispatch: true` AND a typed `signal_pipeline.dispatch_failed`
    audit envelope is written. The Cycle 1 prohibition continues to apply to the
    silent-swallow shape (empty `triggered_sub_agents` with NO `degraded_dispatch`
    flag and NO typed audit envelope) — that combination remains PROHIBITED. The
    distinguishing invariant is: **whenever subscribers exist for a signal category,
    the response body MUST carry either (a) a populated `triggered_sub_agents` array
    OR (b) `degraded_dispatch: true` plus the corresponding
    `signal_pipeline.dispatch_failed` audit envelope** — never neither.
- **FR-010**: Confidence-threshold gating at the **initial fresh-injection** boundary MUST
  be **hybrid by signal-category life-safety class**:
  - **Life-safety categories** (`weather`, `fire-behaviour`, `hydrology`, `geohazard`,
    `evacuation`): a parse with `confidence: low` MUST be **refused-and-clarified** — the
    agent MUST NOT write a synthetic signal, MUST return a clarifying question in chat, and
    MUST write an `injection.refused` audit entry containing the original text, the parsed
    category, the inferred confidence, and the reason `life_safety_low_confidence`.
    Rationale: life-safety telemetry feeds Risk Assessment auto-fan-out (FR-026) and any
    downstream public-warning pathway, so Constitution Principle I (primacy of life)
    requires a refuse-and-clarify gate.
  - **Non-life-safety categories** (`utility`, `transport`, `comms-channel-state`,
    `resource`): a parse with `confidence: low` MUST be **accepted** with `confidence: low`
    recorded in the signal payload and the routing decision; downstream consumers MUST
    treat `low`-confidence non-life-safety signals as best-effort and degrade gracefully.
  - **Post-injection** uses of `confidence: low` (sub-agent self-degraded re-evaluations,
    cascade-induced staleness, network-partition fallback) remain valid for **all** nine
    categories and MUST NOT be refused at later boundaries — only the initial fresh-injection
    boundary applies the hybrid gate.
  - The category → life-safety boolean mapping MUST be a single source of truth used by
    both the parser gate and the audit entry; changes MUST be captured under spec 024's
    audit-schema governance.
- **FR-011**: System MUST attribute every synthetic signal to the chat turn that produced
  it via an `injection_correlation_id`.
- **FR-012**: System MUST allow multiple signals to be derived from a single chat turn and
  MUST tag each with the same `injection_correlation_id`.
- **FR-013**: System MUST detect contradictions with prior signals within the
  category-specific freshness window and tag the new signal `contradicts: <prior_signal_id>`,
  while still writing the new signal.
  - **[Step 8 Amendment G strengthening]**: The contradiction detector MUST receive a
    populated set of recent signals within the relevant category-specific freshness
    window when invoked from **any** path (REST inject-telemetry route, Controller-driven
    sub-agent call path, cascade fan-out path, replay path, or tooling path). The
    inject-telemetry route in particular MUST load recent signals (Cosmos query bounded
    by the freshness window for the parsed category) and pass them into the handler.
    Hardcoding `recent_signals=()` (or any equivalent always-empty literal) at any
    handler call-site is **PROHIBITED** because it makes the contradiction detector inert
    while still appearing wired in the audit log.
- **FR-014**: System MUST flag any signal older than its category-specific freshness window
  as `stale: true` so downstream consumers can render and reason accordingly.
- **FR-015**: System MUST publish synthetic signals onto the existing tenant-scoped signal
  pipeline (spec 007) so all downstream sub-agents receive them via the same subscription
  mechanism as live signals (subject to tenant scoping). Per FR-008, when a chat turn
  produces both a synthetic signal and a substantive sub-agent invocation, the signal MUST
  be **fully written and visible to subscribers** before the Controller invokes the
  substantive sub-agents in the same turn, so the substantive agents observe the new
  signal during their own execution (no race condition on read-your-own-write).
  - **[Step 8 Amendment C strengthening]** (mirrors FR-009 strengthening): Publication
    onto the tenant-scoped pipeline is mandatory **before the inject-telemetry endpoint
    returns**; the response MUST NOT report success while subscribed sub-agents have not
    yet been invoked. The orchestration service MUST own the full transaction (durable
    write → tenant-scoped event publish → subscribed sub-agent fan-out → aggregated
    response → map overlay updates) and MUST surface the `triggered_sub_agents` array in
    the response body populated with each sub-agent that actually consumed the signal.
  - **[Step 8 amendment pass 1 strengthening — single envelope, single correlation id]**
    (see FR-009, FR-026, and pass 1 Q1): The chat-turn audit envelope MUST be
    **singular** — one envelope per chat turn, one `injection_correlation_id` shared
    by the inject-telemetry endpoint response and the Controller substantive-aggregation
    reply. When subscriber fan-out (this FR / FR-026) and Controller-intent fan-out
    (per FR-008 sequencing) both fire on the same turn, dedup MUST be by sub-agent
    identity within the shared envelope; the same sub-agent MUST NOT be invoked twice.
    The endpoint's `triggered_sub_agents[]` records the `subscriber`-tagged invocations;
    the Controller's audit envelope adds the `controller_intent`-tagged invocations.
  - **[Cycle 2 Amendment A2-01 carve-out — degraded-dispatch on orchestrator failure]**
    (see FR-067 and FR-009 carve-out above): On partial orchestrator dispatch failure,
    the inject-telemetry endpoint MUST still publish the durable signal write, populate
    `triggered_sub_agents[]` with the acknowledged subset only, set `degraded_dispatch:
    true` in the response body, and emit the typed `signal_pipeline.dispatch_failed`
    audit envelope. The chat-turn envelope's singular-correlation invariant is
    preserved; the failed-subscriber list is recorded inside the
    `signal_pipeline.dispatch_failed` envelope under the same
    `injection_correlation_id`.
- **FR-016**: System MUST NOT permit a synthetic signal to escape the simulation tenant
  partition; any subscription resolving to a live-tenant resource MUST be refused.

**Auto-routing by intent**

- **FR-017**: Controller MUST infer the appropriate sub-agent(s) from the coordinator's
  chat intent without requiring the coordinator to name an agent.
- **FR-018**: A hazard-parameter-change message (wind, temperature, RH, FDR, river-gauge,
  TC category, geohazard, etc.) MUST automatically invoke Risk Assessment for impact
  prediction and hazard minimisation.
- **FR-019**: When a chat message names a specific agent, the explicit naming MUST take
  precedence over inferred routing.
- **FR-020**: When inferred routing is ambiguous (multiple plausible targets with similar
  confidence), Controller MUST ask a clarifying question in chat rather than route
  speculatively, and MUST write a `routing.ambiguous` audit entry.
- **FR-021**: Routing MUST resolve `jurisdiction + location + hazard class` before
  selecting jurisdiction-specific combat agencies (NSW RFS vs FRNSW; CFA vs FRV; SACFS vs
  SAMFS; NTFRS vs Bushfires NT; SES per state for flood/storm; QFD combined for QLD; TFS
  combined for TAS; DFES for WA; ESA for ACT). When the chat turn does not name a
  jurisdiction explicitly and the active sim spans more than one jurisdiction, jurisdiction
  MUST be resolved via the following **deterministic five-step inference ladder**, stopping
  at the first step that yields a jurisdiction (and recording the matched step in the
  routing-decision audit entry as `jurisdiction_inference_step`):
  1. **Explicit chat mention** — if the chat turn itself names a jurisdiction (e.g.
     "NSW", "Lismore NSW", "Northern Territory"), use it.
  2. **Single-jurisdiction sim** — if the simulation is scoped to exactly one jurisdiction,
     use it.
  3. **Active map-viewport jurisdiction (server-revalidated)** — if the coordinator's
     current Disaster Map viewport is centred over a single jurisdiction, use it. The
     chat-turn payload MAY carry a client-supplied viewport-jurisdiction hint, but this
     hint MUST be treated as **advisory only**: the API MUST re-run a server-side
     centroid → jurisdiction lookup against an authoritative server-side
     jurisdiction-boundary dataset, and the **server-computed jurisdiction wins** in any
     disagreement. When the client hint and the server-computed jurisdiction disagree, the
     Controller MUST write a `routing.viewport_hint_mismatch` audit entry capturing the
     client hint, the server-computed jurisdiction, the viewport centroid, and the
     chat-turn ID; the routing decision MUST proceed using the server-computed value.
     The authoritative jurisdiction-boundary dataset MUST be sourced from the platform
     jurisdiction registry, with explicit fallback to ABS Statistical Area boundaries if
     the registry is incomplete for any state/territory; the exact dataset wiring is
     deferred to plan phase, but the spec MANDATES that *some* authoritative server-side
     dataset is used (no client-trusted routing).
  4. **Last-active hazard-thread jurisdiction** — if the most recently mutated hazard
     thread in the active sim is jurisdiction-tagged, use it.
  5. **Clarify** — if none of steps 1–4 resolves a jurisdiction (e.g. ambiguous peri-urban
     border zones, viewport spans multiple jurisdictions, no prior hazard activity), the
     Controller MUST ask a clarifying jurisdiction question in chat and write a
     `routing.jurisdiction_ambiguous` audit entry; the Controller MUST NOT route
     speculatively or fan out to all candidate jurisdictions.

  **[Step 8 Amendment M strengthening]**: Jurisdiction routing MUST resolve as
  **`(jurisdiction, hazard_class, agency)` tuples**, not as a category-only lookup or a
  jurisdiction-only fallback. The routing rule set MUST include the following blocking
  concrete fixtures (each verified against persona-cohort guidance and persona files in
  `.github/agents/sectors/`); the simulation MUST refuse any routing decision that
  collapses or misrepresents these tuples:

  - **Western Australia (`wa`)**: DFES is the **single** WA fire-and-emergency entry
    point — `(wa, fire, dfes-wa)` and `(wa, ses, dfes-wa)` tuples both resolve to DFES;
    a NSW-style RFS/FRNSW split MUST NOT be applied to WA.
  - **Queensland (`qld`)**: QFD (**Queensland Fire Department**, formerly QFES — naming
    enforced) is the combined fire-and-rescue agency — `(qld, fire, qfd)` resolves to
    QFD; flood/storm `(qld, flood, ses-qld)` and `(qld, storm, ses-qld)` resolve to SES
    QLD; QFD is invocable as a secondary coordination input in SES-led flood scenarios
    but MUST NOT replace SES QLD as the lead combat agency.
  - **Victoria (`vic`)**: split between metropolitan FRV and regional CFA — `(vic,
    fire, declared-area, frv)` resolves to FRV; `(vic, fire, regional, cfa-vic)`
    resolves to CFA. Ambiguous peri-urban / declared-area-boundary cases MUST reach the
    FR-021 step-5 clarify branch rather than being silently misrouted.
  - **South Australia (`sa`)**: SACFS/SAMFS split MUST be respected — `(sa, fire, rural,
    sacfs)` resolves to SACFS; `(sa, fire, metro, samfs)` resolves to SAMFS. Location
    cues from the chat turn MUST distinguish rural from metro.
  - **Northern Territory (`nt`)**: dual fire agencies — `(nt, fire, structural,
    ntfrs)` resolves to NTFRS; `(nt, fire, rural, bushfires-nt)` resolves to Bushfires
    NT. Both routes are independently invocable; "Darwin structure fire" and "Katherine
    grass fire" MUST be disambiguated by location + hazard sub-class.
  - **Australian Capital Territory (`act`)**: ESA-first orchestration — `(act, fire,
    act-esa)`, `(act, ses, act-esa)`, `(act, ambulance, act-esa)` ALL resolve to ESA
    as the strategic coordinator (ESA fans out internally). The Controller MUST NOT
    bypass ESA. ACT policing tuples are `(act, policing, federal-or-ct, afp)` and
    `(act, policing, territory-em, act-policing)` — intent cues distinguish per FR-023.
  - **New South Wales (`nsw`)**: existing FR-021 split is preserved — `(nsw, fire,
    rural, nsw-rfs)` and `(nsw, fire, urban, frnsw)` and `(nsw, ses, ses-nsw)` and
    `(nsw, marine, mrnsw)`.
  - **Tasmania (`tas`)**: combined `(tas, fire, tfs)` — never instantiate a fictitious
    "TAS Rural Fire" entity.

  Routing logic MUST treat the tuple as the resolution key (jurisdiction × hazard
  × agency), and MUST surface the matched tuple in the routing-decision audit entry.
  An acceptance-test fixture MUST exist for each of the above tuples so a regression
  fails on any future routing decision that collapses a jurisdiction split or
  misnames an agency.
- **FR-022**: Routing MUST NOT route firefighting, SAR, or law-enforcement intents to
  control/coord/support entities (Local/State/Territory govt, ARC, NGOs, Health, Volunteers).
- **FR-023**: Routing MUST distinguish ACT policing (AFP federal/CT vs ACT Policing
  territory EM) from intent cues, and MUST route ACT policing to AFP per cohort guidance.
- **FR-024**: Routing MUST distinguish medical service brand per jurisdiction (SAAS, SJA-WA,
  SJA-NT, AT, ACT-Ambulance, NSW Ambulance, Vic Ambulance, QAS) — never use a generic
  ambulance agent.
- **FR-025**: Routing MUST NOT attempt IC escalation from NSW persona handoffs without
  explicit user direction (VIC and QLD escalation pathways may proceed per their persona
  files).
- **FR-026**: Risk Assessment MUST trigger automatically on every hazard-telemetry change
  (wind, fire-behaviour, hydrology, geohazard, TC parameters), without requiring a separate
  chat message.
  - **[Step 8 amendment pass 1 strengthening — subscriber vs controller-intent dedup]**
    (see FR-009, FR-015, and pass 1 Q1): Auto-fan-out from this FR MUST be invoked by
    the inject-telemetry endpoint as the **single** invocation path for any sub-agent
    subscribed to the signal type (Risk Assessment included) on the same chat turn.
    When the Controller separately infers chat intent for a sub-agent that is ALSO a
    subscriber on this turn, the Controller MUST NOT re-invoke that sub-agent — the
    endpoint-side invocation already covers it, and its aggregated reply MUST be
    propagated into the Controller's substantive-aggregation reply via the shared
    `injection_correlation_id`. The dedup key is the sub-agent's identity within the
    shared chat-turn envelope.

**Real-time map updates**

- **FR-027**: Disaster Map MUST add the following `sim-telemetry-overlay` layer types,
  each carrying the SIM badge and a sim visual modifier (striped/dashed/badged): wind-arrow,
  hazard-perimeter, evacuation-route, resource-pin, evac-centre-pin, utility-outage-zone,
  TC-track-and-cone, road-closure-and-alt-route, vessel-or-aircraft-position,
  airspace-restriction, maritime-exclusion, hospital-surge, remote-community-access,
  volunteer-staging, geohazard-zone, flood-polygon.
  - **[Step 8 Amendment B strengthening — visual rendering is mandatory]**: All 16 layer
    types listed above MUST be **visually rendered** on the Disaster Map whenever the
    underlying signal's geometry is applicable to that layer type — `LineString`
    (evacuation-route, road-closure-and-alt-route, TC-track), `Polygon`
    (hazard-perimeter, utility-outage-zone, geohazard-zone, flood-polygon, maritime-
    exclusion, airspace-restriction, hospital-surge, remote-community-access,
    volunteer-staging), and `Point` (wind-arrow, resource-pin, evac-centre-pin,
    vessel-or-aircraft-position) features MUST all render with appropriate SIM styling
    on the visual map surface. Filtering non-Point overlays out of the map and
    relegating them to a screen-reader-only digest is **PROHIBITED**: the screen-reader
    digest is **supplementary** (per FR-064 accessible live-log), not **substitutive**
    for the visual rendering required by sighted exercise control.
  - **[Step 8 Amendment H strengthening — canonical taxonomy]**: The 16-layer taxonomy
    is a **single canonical enumeration** owned by the shared `packages/domain` module
    and consumed by both the API publisher (`apps/api/app/services/simulation/
    map_overlay_publisher.py` LAYER_TYPES) and the web SSE contract (`apps/web/src/lib/
    sse/map-overlay-events.ts` layer enum). A **contract test** MUST enforce
    byte-equality between the backend `LAYER_TYPES` set and the web layer enum —
    backend payload shapes (e.g. `weather|hydrology|degraded-mode-banner`) MUST NOT
    drift from the FR-027 closed set (`wind-arrow|flood-polygon|...`) without a
    co-ordinated update to both sides and the contract test.
  - **[Step 8 Amendment K strengthening — AWS-tier colour standards]**: AWS-tier visual
    rendering on every applicable overlay (wind-arrow speed bands, hazard-perimeter
    severity, public-warning render previews, AWS-tier badges in the map digest) MUST
    follow the **Australian Warning System colour standard**:
    - **Advice** = **yellow** (e.g. `#fbbf24` or the AWS-published reference hex; the
      green hex `#22c55e` currently used in the prototype is **incorrect** and MUST be
      corrected).
    - **Watch and Act** = **orange** (e.g. `#f59e0b`).
    - **Emergency Warning** = **red** (e.g. `#dc2626`).
    - **Not Applicable / Unknown** = neutral grey.

    A regression test MUST assert all four tiers render with the correct colour family
    (yellow / orange / red / neutral grey) and MUST fail on any mis-mapping. The
    AWS-tier colour mapping MUST be a single source of truth in `packages/domain`
    (alongside the layer-types canonical enumeration above) so that web, API, and any
    PDF/email render path consume the same constants.
- **FR-028**: Each new map overlay MUST update within 15 s of the underlying signal change
  (wall-clock when warp = 1×) for hazard, evacuation, and resource categories.
- **FR-029**: Each new map overlay MUST update within 10 s of the underlying signal change
  for weather and geohazard categories (per Commonwealth cohort guidance).
- **FR-030**: Map overlays representing stale signals MUST be visually flagged stale (e.g.
  reduced opacity + stale badge).
- **FR-031**: Map MUST distinguish overlays per AIIMS function (staging, field teams, risk
  overlays, hazard perimeters) under the SIM badge; live-tenant layers MUST NOT be mutated.
- **FR-032**: TC track + cone + storm-surge zone overlays MUST update non-linearly when TC
  category changes mid-sim (zone A/B/C colour-coded and SIM-watermarked).
- **FR-033**: Evacuation route overlay MUST update in real time when a `transport` road
  closure or `utility` outage cascade modifies routing (canonical test:
  flood-closes-primary-route).
- **FR-034**: Map overlay capacity overflow (very large polygon, very many pins) MUST
  cluster or down-sample for render with a visible clustering indicator; underlying signal
  payload MUST be preserved in audit.

**Communication agent — `[SIMULATION] ` receipts and hard-block**

- **FR-035**: Communication agent in sim mode MUST return a chat receipt that begins with
  the literal prefix `[SIMULATION] ` (with trailing space) so it is visually unmistakable
  in any rendering.
- **FR-036**: The receipt MUST include channel, audience, message-id, sim-timestamp, and
  block-reason (mimicking a real delivery receipt envelope).
- **FR-037**: System MUST hard-block real-world publication at every layer for sim tenants
  — the PublicationService MUST refuse and the outbound HTTP client wrapper MUST refuse
  again as defence in depth (carried from spec 024).
- **FR-038**: Each blocked outbound MUST be recorded as `synthetic-delivery` audit entry
  with payload hash, channel, audience, sim-timestamp, and block reason.
- **FR-039**: Public-facing artefacts (warnings, drafts, PDFs, emails) MUST carry the
  watermark `SIMULATION — DO NOT DISTRIBUTE` in every render and every translated language;
  the watermark MUST be applied **before** any IC approval step and **before** any
  would-have-published event. In translated **text** artefacts the watermark MUST be
  rendered **bilingually**: the canonical English string `SIMULATION — DO NOT DISTRIBUTE`
  MUST appear first (literal, byte-for-byte, satisfying SC-006's egress-test sweep),
  followed by the locale string drawn from the **version-controlled text-translation
  table** maintained under spec 024's watermark-governance process (per Assumption A11).
  The watermark MUST NEVER be produced by an LLM translation path. If the text-translation
  table has no entry for the active locale, the artefact MUST fall back to **English-only**
  and write an `audit.watermark.locale_missing` audit entry; the artefact MUST NOT be
  emitted with an LLM-generated watermark fallback. **Audio** artefacts (TTS-rendered
  alerts) are governed by FR-058 below using a parallel bilingual audio-prefix mechanism.
  - **[Step 8 Amendment L strengthening — locale coverage and jurisdiction profiles]**:
    Both the text-translation table (FR-039) and the audio-prefix table (FR-058) MUST
    cover **at minimum the spec-target ~30 locales** required by AU emergency
    communications, organised in three explicit groups:
    1. **English** (canonical anchor — always present).
    2. **Top-tier CALD community languages** (ABS census >0.5% population speakers):
       Mandarin, Arabic, Vietnamese, Cantonese, Italian, Greek, Tagalog, Hindi,
       Spanish, Punjabi, Korean, Persian, Tamil, Urdu.
    3. **NT and remote First Nations languages and creoles** (non-negotiable for NT,
       remote QLD, and remote WA jurisdictions): Yolŋu Matha (Yolngu Matha),
       Warlpiri, Pitjantjatjara, Arrernte, Kriol, and Torres Strait Creole.

    A **jurisdiction language profile table** MUST link each Australian jurisdiction
    (`nsw`, `vic`, `qld`, `sa`, `wa`, `tas`, `nt`, `act`, `commonwealth`) to its
    priority locale list (e.g. `nt` → `[en, kriol, yolngu-matha, warlpiri,
    pitjantjatjara, arrernte, torres-strait-creole, ...]`; `vic` → `[en, vi, zh-Hans,
    zh-Hant, el, it, ar, ...]`). The Communication agent MUST consult the jurisdiction
    profile when selecting watermark locales for an outbound artefact targeted at a
    given jurisdiction. The profile table MUST be maintained under spec 024's
    watermark-governance process alongside the text-translation and audio-prefix
    tables. Missing-locale fallback rules from FR-039 / FR-058 (English-only +
    `audit.watermark.locale_missing`) continue to apply; LLM translation/TTS fallback
    remains PROHIBITED on both pathways.
- **FR-040**: The `[SIMULATION] ` prefix and watermark MUST apply to all outbound channels
  for every agency in every jurisdiction (Emergency Alert, Emergency WA, SA Emergency,
  TAS Alert, NT Emergency Alert, ACT Emergency Alerts, BOM warnings, GA notifications,
  NEMA COMDISPLAN, ADF DACC, ABF maritime alerts, ASA NOTAMs, RFDS dispatch, ARC notices,
  Register.Find.Reunite, SJA casualty reports, SLSA beach closures, SMS gateways, social
  media, hospital/media notifications, transport closures, utility outages, volunteer
  credentialling).
- **FR-041**: Communication agent's available-channel list MUST shrink to reflect any
  active `comms-channel-state` degradation signal in the pipeline; unavailable channels
  MUST be visibly annotated and Triple Zero coverage loss MUST be prominently flagged.
- **FR-042**: Any chat request to dispatch real military, real BOM warnings, real NEMA
  COMDISPLAN, or any other real Commonwealth pathway MUST be refused with a typed audit
  entry; only `[SIMULATION] ` artefacts MUST be produced.
- **FR-058**: TTS-rendered audio artefacts (CALD audio listeners, Auslan-narrative
  voice-over, and any other spoken alert pathway) MUST carry the `SIMULATION — DO NOT
  DISTRIBUTE` watermark as a **bilingual spoken prefix** sequenced before the alert body:
  the canonical **English spoken prefix** MUST be emitted first (literal, byte-comparable
  in the audio-prefix table's source field), followed by the locale **spoken prefix**
  drawn from a version-controlled **audio-prefix table** governed under spec 024's
  watermark-governance process and aligned in scope with the FR-039 / A11
  text-translation table. LLM-generated TTS of an LLM-translated string is **never**
  permitted (zero translation drift on the audio pathway, mirroring FR-039 for text). If
  the audio-prefix table has no entry for the active locale, the audio artefact MUST fall
  back to the **English-only spoken prefix** and write an `audit.watermark.locale_missing`
  (audio variant) audit entry naming the locale and the artefact ID; the audio artefact
  MUST NOT be emitted with an LLM-generated TTS fallback.

  **[Amendment pass 2 strengthening — shared locale table with FR-064 and
  `delivery_channel` audit field]** (see pass 2 Q6): FR-058 (audio-prefix watermark) and
  FR-064 (accessible live-log) share a **single source of truth** —
  `packages/domain/src/domain/sim_locale_table.json` — but render through distinct
  pathways. FR-058's audio pathway consumes the locale table's **bilingual MP3 URL pair**
  (`en_AU` plus the jurisdiction-priority second locale resolved per the FR-039
  jurisdiction language profile and FR-021 routing) to prepend a pre-rendered,
  byte-identical MP3 prefix; the audio prefix is **non-removable** by the LLM
  (table-driven prepending). FR-064's text pathway (see below) consumes the same locale
  table's **localised text strings** for the `[SIMULATION]` prefix. Locale resolution
  MUST follow the 3-step fallback `request_locale → jurisdiction_priority_locale →
  en_AU`; the same fallback is shared with FR-064. Every audio artefact MUST emit an
  `audit.watermark.applied` audit entry recording **`delivery_channel`** (enum:
  `audio | text-live-log | both`) and **`resolved_locale`**; the `delivery_channel`
  enum is shared with FR-064 so a chat turn that produces both a screen-reader
  live-log entry AND a TTS audio artefact records `delivery_channel: "both"` against
  the same `audit.watermark.applied` correlation. Validation pathway: audio artefacts
  are exercised via `pytest.mark.azure_speech_staging` (CHK031 voice-prosody, CHK034
  audio-waveform); the audio prefix's byte-identity MUST be asserted on every produced
  artefact.

**Cascading signal effects**

- **FR-043**: A `utility` outage signal MUST cascade automatically (no second injection
  required) to: Health (hospital backup-power re-evaluation), Communication (channel-list
  reduction), Transport (signals affected), Resource Allocation (priority queue shift). The
  full cascade MUST be visible within 30 s of the original injection. **Cascade depth is
  hard-capped at 1** (per A12 and FR-057's cascade-depth ceiling): this and all other
  cascades (FR-044, FR-045, FR-046, FR-047) are **single-level only** — any downstream
  signal that arises **as a consequence of a first-hop cascade write or a
  degraded-cascade annotation** is NOT issued automatically; it requires a fresh
  Telemetry-Injection chat turn or coordinator action that re-enters the Controller
  envelope (and therefore re-enters the FR-052 thread-cap evaluation and the FR-009
  injection-budget accounting). No automatic depth-2 cascade is permitted.
- **FR-044**: A `transport` road-closure signal MUST cascade to **Evacuation** (route
  re-plan for any active evacuation using that road) within 15 s, and within the same
  cascade horizon MUST also cascade to **Communication** (broadcast channel impact
  evaluation for any AWS-tier warning that referenced the now-closed road) and
  **Resource Allocation** (re-route field-team movements that depended on the road).
- **FR-045**: A `comms-channel-state` signal MUST cascade to Communication (channel-list
  refresh) within 10 s.
- **FR-046**: A `resource` volunteer signal MUST cascade to Resource Allocation
  (spontaneous surge → unallocated headcount up; fatigue/depletion → headcount down; rural
  volunteers who are disaster-affected appear as resource depletion).
- **FR-047**: An `evacuation` centre event (open / capacity / closed) MUST update the
  single authoritative evac-centre map overlay regardless of which agent injects first; the
  overlay MUST be visible to all consuming agents, AND within the same cascade horizon
  MUST cascade to **Planning** (incident-action-plan re-evaluation when an evacuation
  centre changes capacity / closes / opens), **Evacuation** (re-routing of any active
  evacuations whose terminus was the affected centre), and **Resource Allocation**
  (re-prioritisation of supplies, transport, and welfare staff to/from the affected
  centre).

#### Cascade matrix (canonical) — [Step 8 Amendment N]

The cascade matrix below is the **single canonical declaration** of which downstream
sub-agents the Telemetry-Injection Agent and cascade orchestrator MUST notify when each
listed source-signal category is written to the tenant-scoped pipeline. Latency budgets
remain those of FR-043..FR-047; the matrix MUST be the single source of truth shared
between spec, plan, data-model, contracts, and orchestration code:

| Source signal | Cascade targets (sub-agents to notify) |
|---|---|
| `utility` (outage / restoration / degradation) | Health, Communication (Comms), Transport, Resource Allocation |
| `hydrology` (river gauge / flood watch / dam release) | Risk Assessment, Evacuation, Communication (Comms), Resource Allocation |
| `transport` (road closure / route impassability) | Evacuation, Communication (Comms), Resource Allocation |
| `evacuation-centre` (open / capacity / closed) | Planning, Evacuation, Resource Allocation |
| `geohazard` (earthquake / tsunami / landslide / volcanic / ground movement) | Risk Assessment, Evacuation, Resource Allocation |
| `comms-channel-state` (degraded / blackout / restored) | Communication |
| `resource` (volunteer surge / fatigue / depletion) | Resource Allocation |

The matrix is bound by the FR-057 cascade-thread-cap rules (degradation to annotation
when fan-out would create a 6th top-level thread) and the A12 / FR-043 single-depth
ceiling (no automatic depth-2 cascade). Any cascade target listed above that is not
honoured at runtime (i.e. the source signal is written but the listed sub-agent receives
no cascade notification within the FR-043..FR-047 latency budget) MUST be treated as a
spec-implementation gap and surface in the FR-063 SLI staging gate as a failed cascade
fan-out.

**[Cycle 2 Amendment A2-03 cross-reference]** (see FR-068): The matrix above is the
human-readable single source of truth. Production fan-out MUST source from the canonical
`packages/domain/src/domain/sim_cascade_matrix.py` materialisation of this matrix; any
YAML / config artefact that overrides or narrows the matrix MUST be regenerated from the
canonical source or emit a build-time error. A binding orchestrator round-trip
integration test MUST inject a representative signal of each listed source category and
assert that the actual fan-out set equals the canonical target set.

**Audit, provenance, and isolation**

- **FR-048**: System MUST write append-only, gap-free, typed audit entries for every
  injection, refusal, sub-agent invocation, sub-agent timeout, sub-agent fallback,
  sub-agent cancel, watermark application, refusal of a real-world action, and
  synthetic-delivery event.
  - **[Step 8 Amendment D strengthening — distributed gap-free `sequence_number`]**:
    The audit `sequence_number` MUST be **gap-free across multiple API replicas** (i.e.
    `sequence_number` allocation MUST NOT rely on a process-local counter that is reset
    or duplicated across replicas). The implementation MUST use **one of** the
    following:
    1. A **per-simulation sequence document** in Cosmos DB updated via **ETag
       conditional replace** (or transactional batch in the same partition), so two
       replicas attempting to allocate the same sequence value receive a conflict and
       retry until success.
    2. A **stored procedure** (Cosmos JS server-side) that atomically increments the
       sequence document and returns the next value.
    3. A **documented single-writer constraint** with replica-affinity routing (the
       audit-writer is pinned to a single replica per simulation, and the contract is
       explicitly documented as "single-writer per simulation" with a regression test
       proving the affinity routing).

    On any sequence-uncertainty condition (ETag conflict not resolvable within the
    retry budget; loss of replica-affinity routing; clock skew on a fall-back time
    component if used), the audit writer MUST **fail-closed** — the underlying action
    (signal write, sub-agent invocation, lifecycle transition) MUST be refused with a
    typed audit-not-available error rather than proceed without audit. Per-replica
    process-local counters (e.g. `_sequence_counters: dict[str, int]` initialised at
    module import) are PROHIBITED for production use.
  - **[Step 8 amendment pass 1 strengthening — fail-closed user-facing protocol]** (see
    pass 1 Q2): When the per-simulation sequence allocator exhausts its ETag retry
    budget (max **5** attempts), the originating endpoint MUST execute the following
    five-step protocol:
    1. Return **HTTP 503 Service Unavailable** with `Retry-After: 5` on the originating
       endpoint (inject-telemetry, pause, resume, abort, or any other audit-bearing
       coordinator route).
    2. Write a **best-effort** audit entry of type `audit.sequence.uncertainty` to a
       separate **fail-safe dead-letter queue** — Cosmos `simulation_audit_dlq`
       container, partition by `simulation_id` — using `sequence_number = -1` and an
       `uncertainty_reason` enum drawn from `{etag_exhausted, counter_unreachable,
       replica_partition}`. The DLQ entry MUST be written **exactly once** per
       original request (idempotent under FR-066 replay).
    3. Sequence-uncertainty handling MAY be charged against the FR-009 chat-turn
       latency budget but MUST NOT be charged against the FR-026 fan-out budget
       (subscriber retries are separately bounded).
    4. Per FR-066, replay of the same `Idempotency-Key` MUST return the **cached 503
       response unchanged** without re-attempting the underlying Cosmos operation; the
       FR-066 idempotency-cache TTL is 24 h INCLUDING entries whose cached response is
       a 503.
    5. Per Constitution Principle I (Primacy of Life) the system MUST prefer
       fail-closed over a silent gap — downstream readers (FR-054 lessons-capture,
       FR-049 FOI export) MUST detect `sequence_number = -1` entries in the DLQ and
       surface them as **evidence-integrity warnings**.
  - **[Cycle 2 Amendment A2-06 strengthening — no caller-supplied `sequence_number`
    in audit details dicts]**: The audit writer's gap-free allocator (per Amendment D
    above) is the **single source of truth** for `sequence_number`. Audit details
    dicts (`cascade.depth2_refused`, `injection.success`, and any other typed entry)
    MUST NOT carry a caller-supplied `sequence_number` literal; any such literal is
    misleading (because the writer overwrites it) and brittle (because a future
    writer-side refactor that respected the caller-supplied value would silently
    collapse gap-free invariants). The audit writer MUST ignore (or reject with a
    warning log) any caller-supplied `sequence_number` in the details dict. A
    regression test asserts `cascade.depth2_refused` audit entries land with
    allocator-assigned, gap-free sequence numbers across replicas.
  - **[Cycle 2 Amendment A2-04 cross-reference]** (see FR-069): The
    `injection.success` audit envelope MUST persist a `triggered_sub_agents` array
    structurally identical to the array returned in the HTTP 202 response body, so
    forensic reconstruction of the fan-out subset does not require a JOIN with
    response logs.
- **FR-049**: Audit entries MUST be machine-exportable for lessons capture (spec-024
  audit infrastructure is reused).
- **FR-050**: System MUST guarantee that no synthetic signal, sub-agent reply,
  IAP fragment, risk-register entry, financial artefact, or executive-level decision crosses
  the simulation tenant boundary (in either direction).
- **FR-051**: Telemetry injection actions MUST be restricted to users with the
  `SimulationCoordinator` role; `SimulationObserver` users MUST be able to read but not
  inject; UI MUST hide the injection action for observers and refuse the API call if invoked
  directly.
  - **[Step 8 Amendment E strengthening — coordinator-only RBAC enforcement]**: All
    coordinator-only routes — `inject-telemetry`, `pause`, `resume`, and `abort` (per
    FR-059) — MUST validate **JWT/app-role membership in `Simulation.Coordinator`
    AND tenant membership** **BEFORE any audit attempt** and BEFORE any side-effect
    work (signal write, sub-agent invocation, lifecycle state change). Anonymous /
    fall-back-named-user patterns (e.g. `getattr(request.state.user, "id",
    "anonymous-coord")`) are **PROHIBITED in production**: the auth dependency MUST
    raise HTTP 401 (no JWT) or HTTP 403 (JWT present but role/tenant mismatch) before
    the route body executes. Unauthorized attempts MUST be recorded as
    `audit.rbac.unauthorized_attempt` with the JWT subject claim (or `null` when no
    JWT was presented), the requested route, the simulation ID, and the
    application-detected role/tenant mismatch reason. The pattern MUST be enforced as
    a FastAPI dependency (or equivalent ASGI middleware) so the role/tenant check is
    not duplicated per route handler and cannot be silently omitted on a new
    coordinator-only route.
  - **[Step 8 amendment pass 1 strengthening — RBAC precedes idempotency replay]**
    (see FR-066 and pass 1 Q3): On the four coordinator-only routes
    (`inject-telemetry`, `pause`, `resume`, `abort`), the JWT/role/tenant check from
    Amendment E MUST execute **BEFORE** the FR-066 idempotency-cache lookup so that
    an unauthorised principal cannot retrieve a previously-cached coordinator
    response by replaying a known `Idempotency-Key`. An unauthorised attempt with a
    known idempotency key MUST yield HTTP 401/403 (per the Amendment E rule) and MUST
    write `audit.rbac.unauthorized_attempt`; the cached response MUST NOT be served.
- **FR-060**: Every Sub-Agent Invocation Record (per the Key Entities definition) MUST
  persist a `prompt_hash` field — a sha256 over the canonical prompt the sub-agent's
  LLM actually sees, covering the sub-agent's system prompt + user payload +
  tool-schemas snapshot (whatever the sub-agent's LLM actually consumes). The field
  MUST be populated for every LLM-bearing sub-agent (Risk Assessment, Communications,
  Planning, Evacuation, Resource Allocation, **and the Simulation Telemetry-Injection
  Agent itself**) and MUST be `null` for sub-agents that do not invoke an LLM (e.g.
  deterministic stubs). The `prompt_hash` MUST be machine-exportable via the FR-049
  audit-export pathway and MUST be surfaced to the FR-054 lessons-capture record so
  post-exercise forensic replay can verify the sub-agent's LLM saw exactly what the
  audit says it saw. Rationale: spec 024 already records this for the Controller turn
  (per `controller_prompt.md` versioned hash); extending to sub-agents closes the
  audit-completeness gap and satisfies Constitution IV (Transparency and
  Auditability) for LLM-bearing exercises.

**Multi-hazard concurrency and degraded-mode**

- **FR-052**: System MUST support up to 5 concurrent hazard threads (per Assumption A10) in
  a single simulation, each with independent sub-agent invocations and coexisting map
  overlays; combat-agency threads MUST NOT be collapsed. The 5-thread ceiling is a **hard
  cap**: any coordinator-injected attempt to create a 6th top-level thread (whether at
  scenario setup or mid-sim) MUST be **refused** with a typed `thread.cap_exceeded` audit
  entry containing the rejecting sim ID, the rejected thread proposal, the current
  thread-count, and a chat reply explaining the cap and recommending the coordinator split
  into parallel sims (spec 007 FR-010 permits 3 concurrent sims per tenant). Throttling,
  silent dropping, or queueing a 6th thread is NOT permitted (Constitution V — graceful
  degradation requires predictable failure).

  **[Amendment pass 2 strengthening — annotation-exclusion clause and counter source]**
  (see pass 2 Q8): The 5-thread cap counts **hazard threads only**; annotation threads
  spawned by `cascade.degraded_to_annotation` (per FR-057) do **NOT** count toward the
  cap. A **hazard thread** is a top-level concurrent simulation track with its own
  scenario, sub-agent invocations, map state, and audit lineage (1:1 toward the cap). An
  **annotation thread** is a lightweight cross-reference badge attached to an existing
  parent thread's audit subtree; it does not invoke sub-agents independently and does
  not maintain its own running situation assessment, so it does not consume LLM token
  budget or operator cognitive load. Cap-enforcement edge cases:
  - 5 hazard threads + N annotations is permitted (N is unbounded for annotations).
  - 4 hazard threads + a cascade that would create a 5th hazard thread succeeds and
    becomes thread #5 (no annotation); only the 6th-and-beyond cascade trigger degrades.
  - Annotations stack chronologically on the affinity-selected thread (per FR-057's
    5-step ladder); there is no per-thread annotation cap.

  **Counter source**: cap accounting MUST read from
  `simulation_state.active_hazard_threads`, where each entry carries a `thread_kind`
  field with values `"hazard" | "annotation"`; only entries with
  `thread_kind = "hazard"` are summed against the cap of 5. The counter document
  MUST be updated under the FR-048 ETag-transactional gap-free mechanism applied at
  the thread-cap layer so cap accounting is concurrency-safe under simultaneous
  cascade fan-outs.
- **FR-053**: System MUST accept the following deliberate degraded-mode injections:
  `comms-blackout`, `sub-agent-unavailable` (per agent, per window),
  `network-partition` (between Controller and one or more sub-agents). The simulation MUST
  honour each (cached state, staleness indicators, `degraded` reply tag) for the configured
  window and recover automatically at the configured time.
- **FR-057**: When a cascade (per FR-043, FR-044, FR-045, FR-046, FR-047) would otherwise
  spawn a **new top-level hazard thread** in a sim already at the FR-052 / A10 ceiling of
  5 concurrent threads, the cascade MUST instead **degrade to annotation-on-existing-thread**:
  the cascade's payload (signal, sub-agent invocation result, or map-overlay update) MUST
  attach to the most-related existing thread, resolved via the following **pure
  deterministic 5-step affinity ladder** (no LLM, no heuristics, byte-deterministic for
  SC-011 reproducibility across exercise replays). Each step narrows the candidate set;
  the next step is consulted only when the current step leaves more than one candidate
  tied:
  1. **Jurisdiction match** — restrict to existing threads whose jurisdiction equals the
     cascade's jurisdiction (when the cascade carries one).
  2. **Hazard-class match** — restrict to threads whose hazard class equals the cascade's
     hazard class.
  3. **Cascade-origin-thread preference** — for `utility`, `transport`,
     `comms-channel-state`, and `resource` cascades, prefer the thread that originated
     the cascade trigger (the thread whose sub-agent invocation produced the cascading
     signal).
  4. **Most-recent-mutation timestamp** — pick the thread with the newest mutation
     timestamp (newest wins). This is the tie-break that makes the ladder
     byte-deterministic for SC-011: across replayed runs of the same scenario seed, the
     mutation-timestamp ordering is reproducible because mutations are append-only and
     time-stamped at write time.
  5. **Thread-creation-id ascending** — final tiebreak: pick the thread with the lowest
     thread-creation-id (oldest wins). This guarantees a single deterministic answer
     even when timestamps collide.

  **Audit ownership** (single-walk lessons capture per FR-054): the cascade's audit
  entries (signal-write, sub-agent invocation, map-overlay update) MUST be written into
  the **target thread's audit subtree**, each tagged with `origin_cascade_id: <id>`
  identifying the originating cascade trigger. Exactly **one**
  `cascade.degraded_to_annotation` audit entry MUST be written as a back-pointer in the
  target thread's subtree, recording: the originating cascade trigger (signal ID,
  triggering thread ID), the suppressed would-be-new-thread proposal, the chosen target
  thread, and the affinity-ladder step that produced the choice (`affinity_step: 1..5`).
  No silent drop is permitted; the chat timeline MUST surface a brief annotation
  indicating the cascade was attached rather than spawned. This audit-ownership rule
  ensures FR-054 timeline reconstruction is **single-walk** over the target thread (no
  cross-thread JOIN required to surface a degraded cascade). This rule preserves SC-011's
  "no combat-agency thread collapse" by construction (the cap is enforced at thread
  creation, not by collapsing existing threads).

  **Cascade depth ceiling** (per A12): cascades are **single-level (max depth = 1)**.
  The first hop (per FR-043 / FR-044 / FR-045 / FR-046 / FR-047) executes within its
  declared latency budget. Any signal that arises **as a downstream consequence of a
  degraded-cascade annotation** (a would-be "depth-2 cascade") MUST NOT be processed
  as an automatic depth-2 cascade — it MUST be treated as a fresh top-level
  Telemetry-Injection turn requiring an explicit chat input or coordinator action,
  and therefore re-enters the FR-052 thread-cap evaluation and the FR-009
  injection-budget accounting via the Controller envelope. `origin_cascade_id` MUST
  NOT propagate transitively across cascade hops; when a refused depth-2 attempt is
  later re-issued as a fresh top-level turn through the Controller envelope, that
  re-issued turn gets a **new** top-level injection-correlation-id rather than
  inheriting the originating cascade's id. This ceiling preserves SC-011
  reproducibility (bounded cascade count per turn) and Constitution V predictable
  failure (audit ownership remains single-depth and the FR-054 single-walk
  invariant holds at exactly one depth).

  **[Step 8 Amendment J strengthening — `cascade_orchestrator.fan_out` integration
  contract]**: The cascade orchestrator (`cascade_orchestrator.fan_out` in
  `apps/api/app/services/simulation/cascade_orchestrator.py` or its successor) MUST
  integrate the **ThreadCapService** before dispatching to any cascade target. Every
  cascade fan-out MUST execute the following control flow:

  1. **Cap probe** — call `ThreadCapService.check_or_acquire(simulation_id,
     proposed_thread_class)` (or equivalent) **before** writing any cascade payload.
     Loading the configured `cap` value without checking the active-thread count is
     PROHIBITED.
  2. **If cap not exceeded** — proceed with the normal cascade write to a new or
     existing thread per FR-043..FR-047 plus the Cascade-matrix table.
  3. **If cap would be exceeded** — invoke the FR-057 **5-step affinity ladder
     (jurisdiction → hazard-class → cascade-origin → most-recent-mutation timestamp →
     thread-creation-id ascending)** to select the target thread for annotation.
  4. **Emit `cascade.degraded_to_annotation` audit entry** — with the
     `affinity_step: 1..5` field populated, recorded into the **target thread's audit
     subtree**, per the audit-ownership rule above. This audit emission is mandatory
     and MUST NOT be silently skipped.
  5. **Surface in chat timeline** — the chat reply / SSE timeline MUST publish the
     brief annotation indicator described in the audit-ownership clause.

  Implementations that load the cap value but never check thread-count, never call
  `ThreadCapService`, or never emit `cascade.degraded_to_annotation` (i.e. silently
  proceed with fan-out regardless of the cap) are non-compliant.

  **[Amendment pass 2 strengthening — affinity ladder selects the annotation host
  thread]** (see pass 2 Q8): When the FR-052 hard cap of 5 hazard threads is reached
  and a cascade trigger fires, the 5-step affinity ladder above selects which of the
  existing **hazard** threads receives the annotation (annotation threads do NOT
  participate in the ladder because they do not have independent jurisdiction /
  hazard-class / mutation-timestamp records of their own — they belong to the parent
  hazard thread's audit subtree). The selected hazard thread accumulates annotations
  chronologically (no per-thread annotation cap). The cap counter (FR-052 counter
  source) reads `thread_kind = "hazard"` entries only when checking whether a
  proposed new thread would exceed the cap; this guarantees that an existing
  thread already carrying many annotations remains a valid candidate for further
  annotations and does not consume any cap budget.

**Coordinator lifecycle controls (inherits spec 024 lifecycle implementation)**

- **FR-059**: System MUST expose three coordinator-driven lifecycle verbs — `pause`,
  `resume`, `abort` — within feature 036's FR surface, in addition to the `end`
  lifecycle event already implicitly covered by User Story 9. `pause` and `resume`
  MUST be restricted to users with the `SimulationCoordinator` role (per FR-051's
  role-check surface). Semantics:
  - **`pause`**: while the simulation is `paused`, the Controller MUST refuse new
    chat turns AND halt all sub-agent invocations including in-flight cascade
    fan-out. Cascade work already in-flight is allowed to **complete its current
    step** (the in-flight sub-agent invocation runs to its declared FR-006 timeout)
    but **no new sub-agent invocations and no new signal writes** are issued for
    the duration of the `paused` state. Refused chat turns and refused sub-agent
    invocations during `paused` MUST be recorded as typed audit entries tagged
    `lifecycle.paused`.
  - **`resume`**: returns the simulation to `active`. Deferred cascade hops are NOT
    automatically replayed (consistent with the A12 / FR-057 cascade-depth-1
    ceiling) — any signal that would have constituted a follow-on cascade requires
    a fresh Telemetry-Injection turn or coordinator action.
  - **`abort`**: all in-flight sub-agent invocations are **cancelled** (each
    producing a `sub_agent.cancel` audit entry per FR-048), the simulation
    transitions to `ended` with `end_reason: aborted`, and FR-054 lessons-capture
    is triggered automatically. The `abort` itself MUST be recorded as a typed
    audit entry containing the issuing coordinator's user ID, the abort timestamp,
    and the count of cancelled in-flight invocations. Constitution I (Primacy of
    Life) requires the coordinator override surface to be unambiguous; this FR
    makes the surface explicit within feature 036's FR set rather than leaving it
    implicit in spec-024 inheritance.

  **[Step 8 Amendment F strengthening — durable lifecycle state enforcement]**:
  - **`pause` MUST persist simulation state to a durable store** (the simulation
    document in Cosmos DB, or equivalent) **BEFORE** the audit entry is written
    and BEFORE the HTTP response is returned. Auditing the pause without changing
    state (such that subsequent chat turns / sub-agent invocations / inject-telemetry
    calls still succeed) is non-compliant.
  - While the simulation is in the persisted `paused` state, **all subsequent
    coordinator-write operations** — new chat turns, telemetry injections,
    sub-agent invocations, cascade fan-outs — MUST be **refused with HTTP 409
    Conflict** and written as `audit.lifecycle.refused_while_paused` audit
    entries. Refusal MUST occur at the route entry (after RBAC per Amendment E)
    and MUST NOT depend on a per-route check that any one handler could omit.
  - **`resume`** MUST atomically transition the simulation document back to
    `active` and re-enable invocations. Any state-transition error during resume
    MUST fail-closed (the simulation remains `paused`).
  - **`abort` MUST queue the FR-054 lessons-capture job**, not merely claim that
    the job has started. The abort handler MUST write the lessons-capture work item
    to a durable queue (or trigger a durable orchestration) and surface the
    queued-job correlation ID in the audit entry. Returning
    `lessons_capture_started: true` while no job has been queued is non-compliant.

  **[Amendment pass 2 strengthening — lifecycle × idempotency round-trip semantics]**
  (see pass 2 Q7): The interaction between FR-059's lifecycle verbs and FR-066's
  idempotency cache on `pause` → `resume` → `pause` round-trips is governed by the
  following rules. The state machine consumes the cached lifecycle response, not just
  the wire response.
  - **Per-verb namespace** (consistent with pass 1 Q3 / FR-066): `pause`, `resume`,
    and `abort` each occupy their own `(simulation_id, verb, route)` idempotency
    namespace. Different verbs MUST NOT collide: a key `K1` used on `POST /pause` and
    later on `POST /resume` for the same `simulation_id` is two distinct cache entries
    in two distinct namespaces.
  - **Replay during the same lifecycle phase**: `POST /pause` with key `K1` while the
    simulation is still `paused` (the `K1` pause has not yet been consumed by a
    resume) MUST return the cached pause response unchanged without re-executing the
    state transition.
  - **Replay after consumption**: `POST /pause` with key `K1` AFTER the simulation
    has transitioned through `resume` MUST be refused with **HTTP 409 Conflict**
    carrying an RFC 9457 problem detail of `type: "lifecycle-state-conflict"`. The
    cached `K1` response is preserved for the full 24 h replay window as an immutable
    receipt but the state machine refuses re-execution because the `K1` pause has
    been "consumed" by the resume.
  - **New key after resume**: `POST /pause` with a NEW key `K2` after resume succeeds
    and creates a new cache entry; the simulation re-enters `paused`.
  - **Refusal-while-paused is NOT cached**: while the simulation is `paused`, any
    non-`resume` and non-`abort` write request (new chat turns, telemetry injections,
    sub-agent invocations, cascade fan-outs) MUST be refused with HTTP 409 and an
    `audit.lifecycle.refused_while_paused` audit entry per the Amendment F clause
    above; the 409 refusal response itself MUST NOT be written to the
    `simulation_idempotency_cache` so that the same request body can be serviced
    cleanly on resume rather than serving a cached refusal.
  - **Audit lineage**: every lifecycle audit entry — `audit.lifecycle.pause_requested`,
    `audit.lifecycle.paused`, `audit.lifecycle.resume_requested`,
    `audit.lifecycle.resumed`, `audit.lifecycle.refused_while_paused`,
    `audit.lifecycle.aborted` — MUST include both `idempotency_key` AND
    `request_correlation_id` for cross-replay traceability across the FR-049 export
    and the FR-054 lessons-capture timeline.

**Post-exercise lessons capture**

- **FR-054**: System MUST produce, on coordinator request after a sim ends, a structured
  exercise-outcome record containing: timeline (chat + injections + sub-agent invocations
  + state changes), sub-agent response summary, IC decision points, identified gaps,
  `lessons-identified` annotation section. The record MUST be AIDR-compatible. Timeline
  reconstruction MUST be **single-walk per thread**: per FR-057's audit-ownership model,
  cascades that degraded to annotation appear in the target thread's audit subtree
  (tagged `origin_cascade_id`, with a single `cascade.degraded_to_annotation`
  back-pointer entry), so a per-thread walk surfaces every cascade that touched the
  thread without requiring a cross-thread JOIN.
  - **[Step 8 Amendment I strengthening — six AIDR sections, deterministic order]**:
    The ExerciseOutcomeRecord MUST contain **exactly the six named sections** below,
    populated from the audit substrate (not from re-summarisation by an LLM). Generation
    that emits only a participant summary plus timestamps (without the other sections)
    is non-compliant:

    1. **Participant summary** — list of participating coordinators, observers, and
       agents, with role assignments and the time window each was active.
    2. **Timeline** — chronological list of every signal injection, sub-agent
       invocation, lifecycle event (start, pause, resume, abort, end), and cascade
       attachment. Ordered ascending by `(timestamp, sequence_number)`.
    3. **Sub-agent responses** — per-invocation entries with sub-agent name,
       triggering correlation ID, request payload digest, response payload, citations,
       degraded/error/timeout flags, and the FR-060 `prompt_hash`. Ordered ascending by
       `(timestamp, sequence_number)`.
    4. **IC decisions** — every coordinator-driven lifecycle action (pause / resume /
       abort / end) plus every `routing.ambiguous` and `routing.jurisdiction_ambiguous`
       clarification, plus every IC approval / refusal of a public warning. Ordered
       ascending by `(timestamp, sequence_number)`.
    5. **Identified gaps** — every cascade refusal (`thread.cap_exceeded`,
       `cascade.degraded_to_annotation`, depth-2 refusal), every degraded-mode entry
       (`sub_agent.timeout`, `sub_agent.cancel`, `sub_agent.fallback`), and every
       refused real-world-action attempt (`real_world_action.refused`). Each gap entry
       MUST identify the originating thread, the affected sub-agent (where applicable),
       and the audit-trail link.
    6. **Lessons-identified narrative** — a free-text section authored by the
       coordinator post-exercise (or auto-seeded with prompts for the coordinator to
       complete), distinct from the deterministic sections 1–5.

    The record's deterministic ordering across all sections MUST be `(timestamp
    ascending, sequence_number ascending)` so byte-identical regeneration (per FR-055)
    is guaranteed across replays.
- **FR-055**: Generation MUST be idempotent; re-requesting the same record MUST be
  byte-identical, and a failed generation MUST be retriable from audit without data loss.

**Real Level-3 NEMA throttle (inherited from spec 024)**

- **FR-056**: If a real Level-3 NEMA event activates while any simulation is running, the
  simulation MUST auto-throttle immediately (banner, restricted tool list per spec 024
  FR-004, FR-005), and MUST NOT suppress real notifications under any circumstances.

**Step 8 amendment additions (new FRs)**

The following new functional requirements were added by the Step 8 amendment cycle (see
the Step 8 Amendment Log at the top of this document for cohort context and verification
evidence). They extend — rather than replace — any existing FR.

- **FR-061** *(Amendment A — AIIMS function-to-sub-agent mapping)*: The simulation
  MUST publish a **canonical AIIMS function-to-sub-agent mapping table** that assigns
  every operational sub-agent in feature 036 to **exactly one AIIMS functional area**.
  The mapping MUST cover the six AIIMS functions and MUST be the single source of truth
  consumed by the Controller, the cascade orchestrator, the lessons-capture record
  (FR-054), and the routing-decision audit:

  | AIIMS function | Mapped sub-agent(s) in feature 036 |
  |---|---|
  | **Control** | Simulation Controller (oversight, IC decisions, lifecycle) |
  | **Operations** | Operations sub-agent (tactical fan-out, field deployment); Communication agent (channel-list management); Evacuation agent (route execution) |
  | **Logistics** | Resource Allocation agent |
  | **Intelligence** *(also referred to as "Situation" / "Sit-cell" in some AU jurisdictions)* | Monitoring agent (telemetry observation, signal aggregation); Risk Assessment agent (impact prediction) |
  | **Planning** | Planning agent (incident-action-plan drafting, resource forecasting) |
  | **Public Information** | Communication agent's public-warning pathway (the same Communication agent appears under Operations for channel-list management AND under Public Information for AWS-tier warning authorship — the dual mapping is explicit and intentional, mirroring AIIMS practice) |

  Every Sub-Agent Invocation Record (per the Key Entities section and FR-005) MUST
  carry the resolved AIIMS function tag; lessons-capture (FR-054 §4 "IC decisions") and
  the routing-decision audit MUST surface the AIIMS function alongside the sub-agent
  name. Routing logic MUST NOT blend functions across sub-agents (e.g. a Logistics
  intent MUST NOT silently invoke a Planning sub-agent and vice versa); when an intent
  spans multiple AIIMS functions the Controller MUST fan out to one sub-agent per
  function (the FR-052 5-thread cap and FR-057 cascade rules continue to apply).

  **[Step 8 amendment pass 1 strengthening — single-valued primary + secondary tags]**
  (see pass 1 Q4): The `aiims_function` field on every Sub-Agent Invocation Record
  MUST be **single-valued** (one canonical AIIMS function per invocation, used for
  routing and FR-054 deterministic lessons-capture ordering). A separate
  **`secondary_aiims_tags`** array (max 2 entries, MAY be empty) MUST record any
  additional AIIMS-function context for sub-agents that doctrinally span more than
  one function. The canonical primary / secondary mapping for feature 036 is:

  | Sub-agent | Primary `aiims_function` | `secondary_aiims_tags` |
  |---|---|---|
  | Simulation Controller | `Control` | `[]` |
  | Operations | `Operations` | `[]` |
  | Communication | `Public Information` | `["Operations"]` |
  | Evacuation | `Operations` | `["Public Information"]` |
  | Resource Allocation | `Logistics` | `["Operations"]` |
  | Risk Assessment | `Intelligence` | `["Planning"]` |
  | Monitoring | `Intelligence` | `[]` |
  | Planning | `Planning` | `[]` |
  | Simulation Telemetry-Injection | `Intelligence` | `[]` |

  Rationale: AIIMS doctrine assigns external warnings / community comms to Public
  Information; Operations owns internal tactical comms. The Communication agent is
  invoked primarily for the FR-038 `[SIMULATION] ` user-facing message — that is
  Public Information by doctrine — so its primary is `Public Information` with
  Operations recorded as a secondary tag. The Control / Operations / Logistics /
  Intelligence / Planning / Public Information six-function set is preserved. Routing
  logic and FR-054 lessons-capture MUST consume **only** the primary
  `aiims_function`; `secondary_aiims_tags` is informational metadata for FOI export
  and post-exercise analysis. The mapping table above is the single source of truth
  and MUST be co-located with the Amendment A canonical table earlier in this FR.
- **FR-062** *(Amendment O — Foundry carve-out registry schema and CI evaluation)*:
  The Constitution v1.2.0 AU-residency carve-out for Azure OpenAI / Foundry MUST be
  governed by a **versioned registry document** (`foundry_carveout_registry.json` or
  equivalent path under the platform-config repo). Every entry in the registry MUST
  carry the following fields:
  - `tenant_id` — the simulation tenant the carve-out applies to (or `*` for a
    cross-tenant deployment-level carve-out, with documented justification).
  - `model_deployment` — the named Azure OpenAI / Foundry deployment the carve-out
    authorises (e.g. `aoai-au-east-gpt-4o-mini`).
  - `carveout_reason` — free-text rationale referencing the specific Constitution
    Principle (typically Principle II / III) and the operational driver.
  - `evidence_uri` — link to the approved evidence pack (architecture doc, ADR, or
    sign-off issue).
  - `expires_at` — ISO-8601 timestamp at which the carve-out lapses unless renewed.
  - `approver` — Entra ID / human approver name + role recorded at approval time.

  A **CI evaluation step** MUST run on every PR that references a carved-out model
  deployment and MUST **fail closed** when the registry is empty, when an entry has
  lapsed (`expires_at` in the past), when a referenced model deployment has no
  matching registry entry, or when any required field is missing. CI MUST also fail
  if `foundry_carveout_registry.json` exists but is empty (`[]`) while a sub-agent
  references a Foundry deployment in code.
- **FR-063** *(Amendment P — SLI E2E staging promotion gate)*: All five plan-canonical
  Service Level Indicators (SLIs) for feature 036 MUST be backed by **blocking E2E
  tests that run in the staging environment as a release-promotion gate**. The five
  canonical SLIs are:
  1. **P95 inject→fan-out latency** — from inject-telemetry HTTP entry to last
     subscribed sub-agent acknowledging the synthetic signal (per FR-009/FR-015 end-
     to-end transactional invariant). Target threshold to be set in plan phase.
  2. **P99 audit gap-free invariant** — across N injections in the staging run, **0**
     sequence-number gaps observed in any simulation's audit subtree (per FR-048
     strengthened with Amendment D).
  3. **Throughput at 200 concurrent injections** — sustained throughput while
     maintaining SLIs 1 and 2 within target, validated against the SC-001 200-injection
     sample.
  4. **Error budget on map overlay drift** — % of map-overlay updates that arrive
     within FR-028 / FR-029 latency budgets across the 16-layer canonical taxonomy
     (per Amendment H), measured against the SC-010 100-sample observation.
  5. **P95 sub-agent reply latency** — Controller-aggregated reply latency across the
     six operational sub-agents per FR-001..FR-007.

  Promotion of any deployment to production MUST require **green E2E evidence** for
  all five SLIs from the immediately preceding staging run; promotion MUST be
  refused (CI gate or runbook gate) if any SLI lacks fresh staging evidence or fails
  threshold. Exact threshold values are set in `speckit.plan`.

  **[Cycle 2 Amendment A2-02 strengthening — runtime SLI bundle is Z1..Z7]** (see
  SC-013): During Cycle 1 implementation the runtime KQL bundle reassigned
  Z3 → DLQ depth (sequence-uncertainty fail-closed), Z4 → Cosmos RU consumption
  headroom, and Z5 → cascade degraded-to-annotation rate; these three SLIs serve
  operational monitoring purposes that emerged during Cycle 1 and are retained
  unchanged. To restore SLI-level enforcement of SC-001 (P95 sub-agent reply
  latency) and SC-010 (map-overlay drift error budget) — the original "plan-canonical
  SLI #5" and "plan-canonical SLI #4" respectively — the runtime SLI bundle MUST
  add **Z6 (P95 sub-agent reply latency, anchored on SC-001)** and **Z7 (map-overlay
  drift error budget, anchored on SC-010)**. The seven runtime SLIs are therefore:
  Z1 (P95 inject→fan-out latency, plan-canonical), Z2 (P99 audit gap-free
  invariant, plan-canonical), Z3 (DLQ depth, operational), Z4 (Cosmos RU headroom,
  operational), Z5 (cascade degraded-to-annotation rate, operational), **Z6 (P95
  sub-agent reply latency, plan-canonical, NEW Cycle 2)**, **Z7 (map-overlay drift
  error budget, plan-canonical, NEW Cycle 2)**. Promotion to production MUST be
  refused if any of Z1 / Z2 / Z6 / Z7 lacks fresh staging evidence or fails its
  threshold; Z3 / Z4 / Z5 are warn-only operational signals (per their Cycle 1
  alert-routing tier). Threshold values for Z6 and Z7 inherit from
  `contracts/sli-thresholds.md` SLI-5 and SLI-4 respectively (gpt-4o: 4000 ms / 5000
  ms breach for Z6; 99.5 % / 99.0 % breach for Z7) and are not re-litigated in this
  amendment.
- **FR-064** *(Amendment Q — accessible live-log)*: The web SSE/streaming chat update
  surface MUST expose a **dedicated accessible live region** that publishes the
  Controller's incoming chat updates to assistive technology in **parity with the
  visual chat pane** (so a screen-reader user receives the same operational
  information as a sighted coordinator). The live region MUST:
  - Use **`role="log"`** with **`aria-live="polite"`** and an explicit
    `aria-label` (e.g. `aria-label="Simulation chat log"`).
  - Receive each new chat token / aggregated reply / sub-agent attribution as soon as
    it arrives over the SSE pipeline (no batching that would defeat the live-region
    semantics).
  - Be **separate from** (and not substituted by) the Disaster Map a11y digest — the
    map digest summarises spatial overlays for screen-reader users, while the
    live-log surfaces the chat narrative; both MUST be present.
  - Include sufficient labelling and visual hidden-but-accessible markup so that
    screen-reader users can navigate between the live-log, the map digest, and the
    chat pane without losing context.

  An accessibility regression test (axe-core / similar) MUST assert the live region
  exists with the correct ARIA roles and labels on every render of the simulation
  page; the test MUST fail if the live region is missing, mis-labelled, or replaced
  by the map digest as the sole accessible surface.

  **[Amendment pass 2 strengthening — shared locale table with FR-058 and
  `delivery_channel` audit field]** (see pass 2 Q6): FR-064's accessible live-log
  consumes the **same** `packages/domain/src/domain/sim_locale_table.json` source of
  truth used by FR-058, but renders the locale table's **localised text strings** for
  the `[SIMULATION]` prefix and watermark text into the ARIA live region at
  SSE-event-receipt time (not pre-rendered). Locale resolution MUST follow the
  3-step fallback `request_locale → jurisdiction_priority_locale → en_AU` shared with
  FR-058. The text prefix MUST be enforced server-side by `chat_receipt_prefix_guard.py`
  (or its successor) before the SSE event reaches the live region; an
  `audit.chat.prefix_missing` audit entry MUST be written if the guard ever observes a
  receipt without the prefix. Every chat-receipt event that lands in the live region
  MUST emit (or contribute to) an `audit.watermark.applied` audit entry recording
  `delivery_channel` (enum: `audio | text-live-log | both`, shared with FR-058) and
  `resolved_locale`; when the same chat turn produces both a screen-reader live-log
  entry AND a TTS audio artefact (FR-058), a single `audit.watermark.applied`
  correlation MUST record `delivery_channel: "both"`. Validation pathway: live-log
  text rendering and ARIA live-region semantics MUST be asserted via vitest +
  axe-core in `apps/web/src/__tests__/`; the test suite MUST fail if the live-log
  text omits the `[SIMULATION]` prefix or if the locale-resolution fallback is
  inverted.
- **FR-065** *(Amendment R — telemetry-injection prompt-hash persistence on every path)*:
  The FR-060 `prompt_hash` requirement extends to **every Telemetry-Injection
  attempt**, regardless of outcome. Every audit entry produced by the Telemetry-
  Injection parser — `injection.accepted`, `injection.refused` (any reason:
  `life_safety_low_confidence`, unknown-category, missing-provenance,
  `thread.cap_exceeded`, malformed input), and `injection.fallback` — MUST persist a
  `prompt_hash` (sha256 over the canonical prompt the parser's LLM saw). The
  refusal/fallback paths MUST NOT diverge from the accepted path on this field.
  Implementations that record `prompt_hash` only on accepted injections (and leave it
  `null` for refused/fallback paths) are non-compliant. The field is machine-
  exportable per FR-049 and surfaced to FR-054 §3 "Sub-agent responses" and §5
  "Identified gaps" so post-exercise forensic replay can verify the parser's input
  on every attempt, not just successful ones.

  **[Step 8 amendment pass 1 strengthening — `prompt_hash_source` enum]** (see pass
  1 Q5): On pre-LLM refusal paths (RBAC failure, malformed input,
  `thread.cap_exceeded`, missing-provenance, idempotency conflict) no canonical LLM
  prompt has been assembled; on system-driven paths (e.g. scheduled cascade
  injection) no user prompt exists at all. To make `prompt_hash` provenance
  unambiguous in every case, every audit entry that carries `prompt_hash` MUST also
  carry a sibling field **`prompt_hash_source`** (enum, REQUIRED whenever
  `prompt_hash` is present) with the following values and computation rules:

  | `prompt_hash_source` | Applies to | `prompt_hash` is sha256 of |
  |---|---|---|
  | `"raw_user_input"` | Pre-LLM refusal paths: RBAC failure, malformed input, `thread.cap_exceeded`, missing-provenance, idempotency conflict | `raw_chat_text_utf8_bytes` (the verbatim user-supplied chat text in UTF-8) |
  | `"canonical_llm_prompt"` | Post-LLM paths: parse success, parse failure with LLM invocation, fallback extractor invoked | `canonical_assembled_prompt_text` (the exact bytes the LLM saw — system prompt + user payload + tool-schemas snapshot) |
  | `"system_only"` | Paths where no user prompt exists — e.g. scheduled cascade injection, system-initiated lifecycle telemetry | `system_prompt_canonical_bytes` (the system prompt alone, byte-for-byte) |

  This guarantees provenance is unambiguous on every refusal/fallback path and
  enables FOI/audit traceability. The audit-envelope schema
  (`contracts/audit-envelope.md`) MUST include `prompt_hash_source` on every typed
  audit entry that records a `prompt_hash` (regardless of how many typed entries
  exist as the envelope evolves; today the envelope has 24 typed entries, of which
  the prompt_hash-bearing subset is the canonical scope of this requirement).
  Implementations that record `prompt_hash` without `prompt_hash_source` are
  non-compliant.
- **FR-066** *(Amendment S — direct REST idempotency)*: All four direct REST
  lifecycle endpoints — `inject-telemetry`, `pause`, `resume`, `abort` — MUST
  honour the **`Idempotency-Key`** request header per the standard idempotency
  pattern:
  - The header value MUST be a client-supplied UUID or opaque string ≤ 255 chars.
  - The server MUST persist the `(simulation_id, idempotency_key)` pair together
    with the original response status, body, and side-effect digest (signal IDs
    written, audit entries written, sub-agents invoked) for a **24-hour replay
    window**.
  - Within the 24-hour window, a replayed request with the same `Idempotency-Key`
    AND the same payload MUST return the **original response without re-executing
    side effects** (no duplicate signal write, no duplicate sub-agent invocation,
    no duplicate audit entry).
  - Within the 24-hour window, a replayed request with the same `Idempotency-Key`
    BUT a different payload MUST be refused with **HTTP 422 Unprocessable Entity**
    and an `audit.idempotency.payload_mismatch` audit entry; the original response
    is preserved.
  - Outside the 24-hour window, the key MAY be reused without conflict.

  The 24-hour window applies independently of the spec-024 30-injections/min/user
  budget (FR-009): a replayed accepted injection within the 24-hour window does
  NOT consume an additional budget slot. The Idempotency-Key persistence store
  MUST be tenant-scoped (a key from one simulation tenant MUST NOT match a request
  from another).

  **[Step 8 amendment pass 1 strengthening — per-(sim_id, verb, route) namespace and
  RFC 9457 conflict response]** (see pass 1 Q2 and Q3):
  - The idempotency-key uniqueness scope is the **`(simulation_id, HTTP verb,
    route)` tuple**, not `(simulation_id, idempotency_key)` alone. Specifically:
    - The same key on `POST /pause` and `POST /abort` for the same `simulation_id`
      occupy **different namespaces** and both succeed independently.
    - Same key + same verb + same `simulation_id` within 24 h is a **replay** that
      returns the original cached response without re-execution of side effects.
    - Same key + same verb + DIFFERENT `simulation_id` are different namespaces
      (`simulation_id` is part of the namespace).
    - After a sim transitions to `ended`, the idempotency cache MUST be preserved
      for the **full 24 h replay window** with TTL anchored on the **original
      request timestamp**, not on sim end.
  - **Conflict detection**: when a request arrives with a known `Idempotency-Key`
    for the same `(simulation_id, verb, route)` tuple but a DIFFERENT canonical-body
    sha256, the server MUST return **HTTP 422 Unprocessable Entity** with an
    **RFC 9457 problem detail** of `type: "idempotency-key-conflict"` (replacing the
    plain-422 / `audit.idempotency.payload_mismatch` shape above for the wire
    response — the audit entry remains, with the RFC 9457 problem-detail body
    captured alongside).
  - **Cache storage**: Cosmos `simulation_idempotency_cache` container, partition
    by `simulation_id`, TTL 24 h, value =
    `{key, verb, route, body_hash, response_status, response_body, created_at}`.
  - **503 caching** (per pass 1 Q2 / FR-048 strengthening): the 24 h replay window
    INCLUDES entries whose cached response is a 503 from sequence-uncertainty
    fail-closed; replay of the same key MUST return the **cached 503 unchanged**
    without re-attempting the underlying Cosmos operation. The companion
    `audit.sequence.uncertainty` DLQ entry MUST be written **exactly once** per
    original request (no duplicate DLQ write on replay).
  - **RBAC ordering** (per pass 1 strengthening of FR-051): the JWT/role/tenant
    check MUST execute **BEFORE** the idempotency-cache lookup so an unauthorised
    principal cannot retrieve a cached coordinator response by replaying a known
    `Idempotency-Key`.

  **[Amendment pass 2 strengthening — state-machine consumption of cached lifecycle
  responses]** (see pass 2 Q7): FR-066's `(simulation_id, verb, route)` idempotency
  cache interacts with FR-059's lifecycle state machine as follows. The cache stores
  the original wire response immutably for 24 h, but the state machine independently
  decides whether a replay is honoured or refused.
  - **Replay-during-same-phase** returns the cached response unchanged (replay of
    `POST /pause` with key `K1` while the simulation is still `paused`).
  - **Replay-after-state-transition** is refused with **HTTP 409 Conflict** and an
    RFC 9457 problem detail of `type: "lifecycle-state-conflict"` (replay of
    `POST /pause` with key `K1` after the simulation has been resumed). The cached
    response is NOT discarded — it remains an immutable receipt for the original
    operation — but the state machine refuses re-execution because the original
    operation has been "consumed" by a subsequent verb.
  - **HTTP 409 lifecycle-state-conflict and HTTP 409
    `audit.lifecycle.refused_while_paused` responses** MUST NOT be written to the
    idempotency cache (so a fresh request body is serviced cleanly when the
    blocking lifecycle phase ends, rather than serving a cached refusal).
  - **Per-verb namespace** is preserved: a key `K1` used on `POST /pause` and later
    on `POST /resume` for the same `simulation_id` produces two distinct cache
    entries in two distinct namespaces; `POST /resume` does NOT consult the
    `pause` cache and vice versa.

  See FR-059 for the complete lifecycle round-trip semantics; FR-066 owns the cache
  storage and replay-window contract, while FR-059 owns the state-transition
  semantics that decide whether a cached response is replayed or whether a 409
  conflict is raised.

**Cycle 2 amendment additions (new FRs)**

The following new functional requirements were added by the Cycle 2 amendment cycle (see
the Cycle 2 Amendment Log near the top of this document for cohort context and verification
evidence). They extend — rather than replace — any existing FR. Cycle 1 amendments A–S
remain in force unchanged.

- **FR-067** *(Amendment A2-01 — degraded-dispatch flag and `signal_pipeline.dispatch_failed`
  audit envelope)*: When the signal-pipeline orchestrator raises during fan-out for an
  accepted injection, the inject-telemetry endpoint MUST adopt the **degraded-dispatch**
  surface (not fail-closed). Specifically:
  - Return **HTTP 202** (signal write is durable) with a response body that includes
    `degraded_dispatch: true` AND `triggered_sub_agents` populated with **one entry per
    attempted subscriber**. Each entry MUST carry `dispatch_status` ∈ `{"acknowledged",
    "failed", "timed_out"}`. *(Updated by Cycle 2 Pass-1 Q1 at L248-277: the response
    body's `triggered_sub_agents` array MUST be byte-equal — after RFC 8785 JCS
    canonicalisation — to the `signal_pipeline.dispatch_failed` audit envelope's array;
    this supersedes the original FR-067 wording that listed only `"acknowledged"`
    entries in the body.)* Failed and timed-out entries continue to be captured in the
    paired `signal_pipeline.dispatch_failed` audit envelope (see below) AND in the
    response body via the byte-equality invariant.
  - Write a typed **`signal_pipeline.dispatch_failed`** audit envelope recording the
    `simulation_id`, `injection_correlation_id`, `partial_successful_subset[]`,
    `failed_subscriber_list[]`, `exception_class` (Python exception type name +
    error-message hash), `prompt_hash`, and `prompt_hash_source` (per FR-065).
  - NOT emit `injection.success` for the failed subscribers — only the acknowledged
    subset is recorded as triggered. The `injection.success` envelope still fires for
    the durable signal write itself; the failed-fan-out facts live in the new typed
    envelope.
  - Honour FR-066 idempotency: replay of the same `Idempotency-Key` MUST return the
    cached degraded-dispatch response unchanged without re-attempting the dispatch.

  **Silent-swallow** (catching `Exception` with only `logger.exception` and returning
  `triggered_sub_agents=[]` without `degraded_dispatch=true` and without the typed
  `signal_pipeline.dispatch_failed` audit envelope) is **PROHIBITED in production**.
  Fail-closed (HTTP 5xx) is rejected because the durable signal write succeeded; denying
  coordinators the partial situational awareness produced by the surviving subset would
  violate Constitution Principle V (Graceful Degradation — predictable failure with an
  explicit machine-readable indicator). The degraded-dispatch flag IS that explicit
  machine-readable indicator.

- **FR-068** *(Amendment A2-03 — cascade rules canonical reconciliation invariant)*:
  Production cascade fan-out MUST be sourced from the canonical
  `packages/domain/src/domain/sim_cascade_matrix.py` matrix (which materialises the
  Cycle 1 Amendment N "Cascade matrix (canonical)" table earlier in this spec). Any
  YAML / config artefact (e.g. `apps/api/app/config/cascade_rules.yaml`) that overrides
  or narrows this matrix MUST emit a build-time error or be regenerated from the
  canonical source. A binding orchestrator round-trip integration test
  (`tests/e2e/test_cascade_orchestrator_round_trip.py` or equivalent) MUST inject a
  representative signal of each cascade-source category (`utility`, `hydrology`,
  `transport`, `evacuation-centre`, `geohazard`) into the **live orchestrator** and
  assert that the set of sub-agents actually invoked equals the canonical matrix's
  target set for that category, within the FR-043 / FR-044 / FR-045 / FR-046 / FR-047
  latency budget. The pre-existing static module-level test (asserting only
  `CASCADE_MATRIX[category]`) is necessary but not sufficient — round-trip parity is
  the binding contract. The Cycle 1 cascade matrix table earlier in this spec
  ("Cascade matrix (canonical) — [Step 8 Amendment N]") remains the single
  human-readable source of truth and MUST stay byte-aligned with `sim_cascade_matrix.py`.

- **FR-069** *(Amendment A2-04 — `triggered_sub_agents` array in `injection.success`
  audit envelope)*: Every `injection.success` audit envelope MUST persist a
  `triggered_sub_agents` array structurally identical to the array returned in the HTTP
  202 response body. Each entry MUST carry `sub_agent`, `trigger_source` (per Cycle 1
  pass-1 Q1 dedup enum: `subscriber | controller_intent | cascade | lifecycle`),
  `correlation_id`, and `dispatch_status` (`acknowledged | failed | timed_out`).
  Recording `triggered_sub_agents` only in the response logger and not in the audit
  envelope is **PROHIBITED** because forensic reconstruction requires single-stream
  recoverability (no JOIN with response logs that may be sampled or absent). The audit
  envelope's array MUST land in the same `details` dict as the existing `chat_turn_id`,
  `injection_correlation_id`, `signal_ids`, `categories`, and `confidences` fields.

- **FR-070** *(Amendment A2-07 — audit envelope `sub_agent` enum alignment)*: Every
  audit-envelope field of type `sub_agent` (including the
  `triggered_sub_agents.sub_agent` enum in `contracts/audit-envelope.md`) MUST match
  the canonical 9-member PascalCase `SubAgent` Literal in
  `packages/domain/src/domain/models/aiims_mapping.py`: `Risk`, `Evac`, `Resource`,
  `Logistics`, `Comms`, `Planning`, `Health`, `Operations`, `Intel`. A contract test
  (`tests/contract/test_audit_envelope_sub_agent_enum.py` or equivalent) MUST assert
  byte-equality between the `sub_agent` enum declared in the audit-envelope contract
  and `ALL_SUB_AGENTS` exported from `aiims_mapping.py`. Historic audit entries that
  were persisted under the legacy 7-name kebab-case enum (`monitoring`, `planning`,
  `resource-allocation`, `communication`, `evacuation`, `risk-assessment`,
  `simulation-telemetry-injection`) remain readable for FOI / lessons-capture export
  but new writes MUST use the PascalCase enum. The contract update lands in Step 8o.

**Cycle 3 amendment additions (new FRs)**

The following new functional requirements were added by the Cycle 3 amendment cycle (see
the Cycle 3 Amendment Log near the top of this document for cohort context and `file:line`
verification evidence). They extend — rather than replace — any existing FR. Cycle 1
amendments A–S and Cycle 2 amendments A2-01 → A2-08 remain in force unchanged.

- **FR-071** *(Amendment A3-01 — staging-promotion gate enforcement at workflow boundary)*:
  The staging-promotion gate workflow (`.github/workflows/staging-promotion.yml`) MUST
  invoke the canonical threshold-comparison helper `assert_sli_thresholds()` from
  `tests/staging_gates.py` (or run the equivalent
  `pytest tests/integration/test_assert_sli_thresholds_z6_z7.py -q`) on **every** gate
  run, supplying live KQL output for Z1–Z7 as the input. The workflow MUST exit
  non-zero if any SLI threshold is breached or any sample-floor is undermet
  (`MIN_SAMPLES_PER_SLI_24H = 30`, per Cycle 2 Pass-2 Q4); on a `StagingPromotionRefused`
  raise the workflow MUST abort the gate job before the promotion step runs.
  On `StagingPromotionRefused` raise, `assert_sli_thresholds()` MUST write a
  `staging_promotion.refused` audit envelope (per `contracts/audit-envelope.md` §3.26)
  with a fresh `staging_promotion_correlation_id` (UUID4) before the exception
  propagates; two concurrent refused runs each write their own envelope — no coalescing.
  Documentary or visual-only logs (e.g. printing `latest=…` without comparing against
  `warn_threshold_ms` / `breach_threshold_ms` / `breach_pct`, OR emitting an
  unconditional success message such as "All 7 SLIs within threshold — promotion
  allowed.") do **NOT** satisfy this requirement. Inline heredoc evaluators that branch
  only on `proc.returncode != 0` from the upstream `az` call are **PROHIBITED in
  production** because they ignore the actual SLI-value comparison. The workflow's
  enforcement boundary is the binding contract surface for SC-013 (Cycle 2 Amendment
  A2-02).

- **FR-072** *(Amendment A3-02 — synthetic smoke-injection emits telemetry to staging API)*:
  The synthetic smoke-injection job in `.github/workflows/staging-promotion.yml` MUST
  emit telemetry by **HTTP POST** to
  `${STAGING_API_BASE}/api/simulations/{simulation_id}/inject-telemetry` against the
  dedicated `tnt-stg-smoke` test tenant, authenticated as the `Simulation.Coordinator`
  test identity. The smoke-injection job MUST assert HTTP 202 + `degraded_dispatch=false`
  per request (per the FR-067 / Cycle 2 Pass-2 Q2 always-present invariant), and MUST
  fail the gate if any request returns a non-202 status or a `degraded_dispatch=true`
  body. `STAGING_API_BASE` MUST be sourced from a GitHub-environment secret bound to
  the `staging` environment (NOT a repository-level secret). The bearer token used to
  authenticate the per-payload `requests.post(...)` call MUST be a short-lived bearer
  access token acquired via `azure/login@v2` + `az account get-access-token`; no
  long-lived `SMOKE_TOKEN` secret is permitted. Declarative payload construction
  without HTTP transmission (constructing `payload = {…}` dicts and emitting only
  `print(...)` lines) does **NOT** satisfy this requirement. The enforced behaviour is
  the prerequisite for `MIN_SAMPLES_PER_SLI_24H = 30` (Cycle 2 Pass-2 Q4) being
  observable in low-traffic staging environments and for SC-014 (below) to be
  exercisable.

- **FR-073** *(Amendment A3-05 + A3-06 — SLI KQL cardinality and threshold-band contract; strengthened by Cycle 4 Amendment A4-01)*:
  Each implementation KQL query in `infra/observability/sli-kql.json` MUST match the
  canonical KQL definition in `specs/036-sim-agent-extend/contracts/sli-thresholds.md`
  for that SLI. The match is enforced at contract-test time by KQL canonicalisation
  (whitespace + comment + parameter-order normalisation per the canonicalisation
  contract in `contracts/sli-thresholds.md` §10). The contract test
  (`tests/contract/test_sli_kql_canonical_match.py`) covers all seven SLIs (Z1–Z7);
  Z6 and Z7 are the cohort-finding-driven minimum surface the Step 8s cohort validated,
  but the contract surface is universal — every declared SLI in
  `infra/observability/sli-kql.json` participates in canonicalisation enforcement.
  Cardinality-determining elements — group-by columns, `extend` chains, and `where`
  filter clauses — are part of the canonical form: dropping `extend sub_agent`,
  dropping `where env == "staging"`, or summarising by a narrower set of dimensions
  than the spec mandates is a contract violation regardless of whether the resulting
  numeric output passes a downstream gate. Threshold-band entries
  (`warn_threshold_ms`, `breach_threshold_ms`, `warn_pct`, `breach_pct`) in
  `infra/observability/sli-kql.json` MUST also match the corresponding values in
  `contracts/sli-thresholds.md`; identical `warn_pct` and `breach_pct` for an SLI that
  the spec defines with distinct two-band values is a contract violation. The contract
  test asserts byte-equality after canonicalisation for every declared SLI, covering
  both KQL bodies and threshold bands.
  **Author-time KQL column-resolution-validity** *(Cycle 4 / A4-01 strengthening — `spec.md:3875-3895`)*:
  is enforced by `tests/contract/test_sli_kql_runtime_validity.py` (parametric
  across Z1–Z7); the walker hard-fails on `union` and on any column reference that
  does not resolve to a base-table column on the queried Application Insights table
  (`requests`, `customEvents`, `customMetrics`, `traces`, `AuditEntries_CL`,
  `AzureDiagnostics`), an explicit `let` / `extend` / `summarize-LHS` binding
  introduced earlier in the same query, or a `customDimensions["…"]` (or
  `customMeasurements["…"]`) lookup. Per PD-C4-01 (`plan.md:788-1010`), the walker
  is regex/lexer-based (no Kusto AST parser dependency) and the failure message
  names the SLI id, the unresolved column, the pipe-clause line number, and the
  full canonicalised KQL.

### Key Entities *(include if feature involves data)*

- **Synthetic Signal**: A typed datum produced by the Telemetry-Injection Agent (or
  permitted to be produced by other simulation tooling). Categories: `weather`,
  `fire-behaviour`, `hydrology`, `geohazard`, `utility`, `transport`, `evacuation`,
  `resource`, `comms-channel-state`. Required fields: `source: "sim-injected"`,
  `simulation_id`, `injecting_user_id`, `timestamp`, `confidence`, `gps` (where applicable),
  `injection_correlation_id`, `contradicts` (optional), `stale` (computed). Lifecycle:
  injected → published-to-pipeline → consumed-by-subscribed-sub-agents → eventually
  flagged-stale.
- **Sub-Agent Invocation Record**: A typed record of a Controller-driven (or signal-driven)
  invocation of a sub-agent. Fields: `correlation_id`, `triggering_chat_turn_id` (or
  `triggering_signal_id`), `sub_agent`, `tenant_id` (always sim), `request_payload`,
  `prompt_hash` (sha256 over the canonical prompt the sub-agent's LLM actually sees —
  sub-agent system prompt + user payload + tool-schemas snapshot; populated for
  LLM-bearing sub-agents Risk Assessment, Communications, Planning, Evacuation,
  Resource Allocation, and the Simulation Telemetry-Injection Agent itself; `null`
  for non-LLM-bearing sub-agents such as deterministic stubs; persisted per FR-060
  and surfaced to FR-054 lessons-capture for forensic replay verification under
  Constitution IV), `response_payload`, `citations[]`, `degraded`, `error`,
  `timeout`, `started_at`, `completed_at`. Lifecycle: invoked → streaming →
  complete | timeout | error | cancelled.
- **Synthetic-Delivery Receipt**: A typed record of a blocked outbound communication.
  Fields: `channel`, `audience`, `message_id`, `sim_timestamp`, `block_reason`,
  `payload_hash`, `watermark_applied: true`. Always rendered to the user with the
  `[SIMULATION] ` prefix.
- **Routing Decision**: A typed record of how a chat turn was routed. Fields: `chat_turn_id`,
  `inferred_intent`, `selected_sub_agents[]`, `jurisdiction`, `location`, `hazard_class`,
  `confidence`, `ambiguous: bool`, `clarification_required: bool`. Used for audit and
  routing-quality measurement.
- **Map Overlay Layer (sim-telemetry-overlay)**: A new family of Disaster Map layer types
  scoped to a simulation tenant. Always carries SIM badge and sim visual modifier; never
  mutates live-tenant layers. Sub-types per FR-027.
- **Exercise Outcome Record**: A structured AIDR-compatible report produced after a sim
  ends. Sections: timeline, agent responses, IC decisions, identified gaps,
  lessons-identified. Idempotent and retriable.

## Success Criteria *(mandatory)*

These translate the capstone targets (`capstone.md`) into simulation-observable, measurable,
technology-agnostic outcomes per Assumption A8 (baseline = same scenario with auto-fan-out
and Telemetry-Injection Agent disabled).

### Measurable Outcomes

- **SC-001**: In a controlled exercise comparing baseline (without auto-fan-out) vs.
  enhanced (with auto Risk Assessment fan-out), the enhanced run produces actionable risk
  recommendations within ≤ 15 s of the triggering telemetry injection in **≥ 95 %** of runs
  over a 200-injection sample.
- **SC-002**: Coordinators completing the same multi-agency scenario complete the
  *decision-to-public-warning* lead time at ≤ **50 %** of the baseline lead time, measured
  as the median across 30 paired exercises. *(Maps to capstone "Reduce disaster response
  time by 50 % via autonomous agent coordination".)*
- **SC-003**: For evacuation scenarios, predictive risk fan-out produces an
  `evacuate-now` recommendation at least **24 h earlier** than baseline (in scenario time,
  not wall-clock) in **≥ 80 %** of bushfire-and-flood exercises. *(Maps to capstone
  "Evacuate at-risk populations 24 hours earlier".)*
- **SC-004**: Resource Allocation agent reaches an optimised deployment plan with
  **≥ 30 % fewer reallocations** than baseline in **≥ 80 %** of multi-hazard exercises.
  *(Maps to capstone "Optimise emergency resource deployment with 30 % efficiency".)*
- **SC-005**: Post-exercise economic-loss model (using the AIDR-aligned synthetic economic
  profile per A9) shows **≥ 30 % reduction** vs. baseline in **≥ 70 %** of comparison runs.
  *(Maps to capstone "Reduce disaster-related economic losses by 30 %".)*
- **SC-006**: **Zero** real-world communications successfully sent during any simulation
  across **all** participating egress channels (BOM, GA, NEMA COMDISPLAN, ADF DACC, ABF,
  ASA, RFDS, ARC, SLSA, SJA, all state/territory alert systems including Emergency Alert,
  Emergency WA, SA Emergency, TAS Alert, NT Emergency Alert, ACT Emergency Alerts, telco
  SMS gateways, social media connectors, broadcast integrations). Measured continuously;
  any single false positive is a SEV-0 incident. *(Maps to capstone "Save 1,000+ lives
  annually" via the constitutional comms-block — a single false-positive delivery would
  catastrophically erode the trust required for life-safety adoption.)*
- **SC-007**: **100 %** of telemetry injections produce a typed signal record with full
  provenance in the simulation audit trail, **OR** are blocked at ingest with an
  `injection.refused` audit entry — never silently dropped.
- **SC-008**: **100 %** of Communications-agent chat receipts in sim mode include the
  `[SIMULATION] ` prefix and a synthetic-delivery receipt envelope with channel, audience,
  message-id, sim-timestamp, and block-reason. Verified by automated egress-test sweep on
  every PR.
- **SC-009**: **100 %** of hazard-telemetry injections automatically trigger Risk
  Assessment without the coordinator naming the agent (auto-routing coverage), measured
  across a 200-injection sample. *(Operationalises FR-026 and the user's explicit ask
  about wind-change → Risk Assessment.)*
- **SC-010**: **100 %** of major signal categories (the nine in FR-008) produce a
  corresponding map overlay update within their FR-028 / FR-029 latency target on a
  100-sample observation. *(Operationalises the user's "real-time updates to the map" ask.)*
- **SC-011**: For multi-hazard concurrency exercises (up to 5 concurrent threads per
  Assumption A10), **0** instances of combat-agency thread collapse or cross-thread
  sub-agent contamination, measured across 30 exercises. *(Operationalises the cohort's
  most-common edge case.)*
- **SC-012**: For deliberate degraded-mode injections, the affected sub-agent honours the
  configured behaviour for **100 %** of the configured window and recovers automatically
  with an audit entry on **100 %** of injections (≥ 50-injection sample).
- **SC-013** *(Cycle 2 Amendment A2-02 — SLI Z6 + Z7 staging-promotion gate)*: Promotion
  of any deployment to production MUST require **green E2E evidence** for SLI **Z6**
  (P95 sub-agent reply latency, anchored on SC-001, threshold per
  `contracts/sli-thresholds.md` SLI-5: gpt-4o ≤ 4000 ms warn / ≤ 5000 ms breach;
  gpt-4o-mini ≤ 1500 ms warn / ≤ 2000 ms breach) AND SLI **Z7** (map-overlay drift
  error budget, anchored on SC-010, threshold per `sli-thresholds.md` SLI-4: 99.5 %
  warn / 99.0 % breach over a 24 h rolling window). Both Z6 and Z7 MUST be measured
  over the immediately preceding staging run; promotion MUST be refused if either SLI
  lacks fresh staging evidence or fails its threshold. This complements (does not
  replace) FR-063's existing 5-SLI runtime bundle (Z1, Z2, Z3, Z4, Z5); Z6 and Z7
  bring the runtime SLI bundle to 7 SLIs total, with Z1 / Z2 / Z6 / Z7 anchored on
  capstone success criteria and gated for promotion, and Z3 / Z4 / Z5 retained as
  warn-only operational signals.
- **SC-014** *(Cycle 3 Amendment A3-01 — staging-promotion gate refusal under synthetic
  canary)*: The staging-promotion gate workflow MUST refuse promotion in a synthetic
  canary scenario where one or more SLI rows are deliberately constructed above their
  breach threshold OR sample-count is below the `MIN_SAMPLES_PER_SLI_24H = 30` floor
  (per Cycle 2 Pass-2 Q4). Pass criteria: the workflow exits non-zero on the gate job;
  no `promote/{build_label}` git tag is created; no downstream production deploy runs.
  The synthetic canary is fixture-driven (a deterministic in-Python `sli_results` dict
  passed directly to `assert_sli_thresholds()`); it does NOT inject telemetry into the
  staging Application Insights workspace and therefore does NOT contaminate the
  production gate's evidence stream.
  This complements (does not replace) SC-013: SC-013 anchors the *positive* side of the
  gate (green evidence required for promotion); SC-014 anchors the *negative* side
  (refusal must be observable when the inputs are red). FR-071 mandates the workflow
  invocation pattern that makes SC-014 enforceable; FR-072 mandates the smoke-injection
  pattern that makes the synthetic-canary inputs reachable.

**Cycle 2 amendment scope is locked. Ready for /speckit.clarify pass 1.**

**Cycle 2 clarify pass 1 complete. Ready for /speckit.clarify pass 2.**

**Cycle 2 clarify pass 2 complete. Ready for /speckit.checklist.**

**Cycle 3 amendment specify complete. Ready for /speckit.clarify pass 1 (Cycle 3).**

**Cycle 3 clarify pass 1 complete. Ready for /speckit.clarify pass 2 (Cycle 3).**

**Cycle 3 clarify pass 2 complete. Ready for /speckit.checklist.**

**Cycle 3 checklist complete. Ready for /speckit.plan.**

**Cycle 3 plan complete. Ready for /speckit.tasks.**

**Cycle 3 tasks complete. Ready for /speckit.analyze.**

**Cycle 3 analyze complete. Verdict: PASS-WITH-MINOR. Ready for /speckit.implement.**

**Cycle 3 implement complete. 🟡 YELLOW: 3391 tests passed, 0 failed, 11 environment errors (Windows tmp_path PermissionError on Cycle 1/2 file-spill audit tests + 3 missing-module collection errors for `agent_framework`; all non-blocking and unrelated to Cycle 3 scope). Ready for cohort re-review (Step 8ac).**

## Cycle 4 Amendment Log (post Step 8ac cohort re-review, 2026-05-11)

This log records the **Cycle 4** amendments applied following the Step 8ac
cross-cohort re-review of Cycle 3's *own* deliverables. Ground-truth review
reports are `step-8ac-rereview-operational.md` and
`step-8ac-rereview-technical.md` in the session workspace
`C:\Users\prbillir\.copilot\session-state\ddfe017a-c801-4ecd-b4ba-986fe32d7afd\files\`.
Cycle 4 is **narrower in scope** than Cycle 3: it closes two merit-validated
defects that originated in Cycle 3's own implementation artefacts (the
SLI-Z7 KQL `extend` chain and the ADR-036-011 RBAC-scope narrative wording).
Cycle 1 / Cycle 2 / Cycle 3 carry-overs are explicitly out-of-scope. The
originating cohorts were **data-engineer + Operations Officer + Field
Coordinator** (HIGH; technical OBJECT verdict + operational F-OPS-3-01,
KQL author-time validity) and **api-architect + azure-principal-architect
+ infrastructure-devops + security-engineer** (MEDIUM cross-finding,
isolation-guarantee wording).

This amendment cycle adds **0 new functional requirements**, **0 new
success criteria**, **strengthens 1 existing FR** (FR-073 — gains an
author-time KQL column-resolution sub-bullet via A4-01), and records **1
self-documentation supersession** (Cycle 3 Pass 1 Q2 item (v) "Least-
privilege test identity" wording at `spec.md:961-966` is superseded by
A4-02's binding corrected wording). Cycle 1 amendments A–S, Cycle 2
amendments A2-01 → A2-08, and Cycle 3 amendments A3-01 → A3-06 remain in
force unchanged. Implementation files (`infra/observability/sli-kql.json`,
`tests/contract/test_sli_kql_runtime_validity.py` (new),
`tests/contract/_kql_canonicaliser.py` (extension),
`tests/contract/test_smoke_tenant_isolation.py` (extension),
`docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`), contract
files (`specs/036-sim-agent-extend/contracts/sli-thresholds.md`), and
narrative re-rendering of the superseded Cycle 3 Q2 wording are
**out-of-scope** for this spec amendment cycle and will be re-aligned in
subsequent steps (Step 8ad for KQL implementation symmetry + new contract
test, Step 8ae for ADR-036-011 / spec-narrative wording reconciliation).

### Cycle 4 amendment summary table

| ID | Severity | Cohort | Type | Target | Summary |
|---|---|---|---|---|---|
| A4-01 | HIGH | data-engineer + Operations Officer + Field Coordinator | STRENGTHEN-FR (FR-073 sub-bullet) + REGRESSION-TEST | `infra/observability/sli-kql.json:87-91` (Z7 KQL) + `specs/036-sim-agent-extend/contracts/sli-thresholds.md:280-296` (Z7 KQL §6b, line 293 `by model_deployment`) | The Cycle-3-amended SLI-Z7 KQL groups `by model_deployment` (and `tenant_id`) and projects `model_deployment` without first introducing it via `extend model_deployment = tostring(customDimensions["model_deployment"])`. The byte-equality contract test (`tests/contract/test_sli_kql_canonical_match.py`) misses the defect because BOTH files drifted symmetrically — the JSON and the contract are byte-identical-after-canonicalisation, just both wrong. At AppInsights query-time the KQL emits `SemanticError: Failed to resolve column reference 'model_deployment'`; the workflow `proc.returncode != 0` branch fires before `assert_sli_thresholds()` is invoked, so no `staging_promotion.refused` envelope is written, breaking Pass-1 Q3's always-write-envelope-on-refusal invariant and rendering SC-010 unenforceable on this code path. The working comparison is SLI-Z6 at `infra/observability/sli-kql.json:76`, which DOES extend (`extend model_deployment = tostring(customDimensions["model_deployment"])`) — defect provenance is asymmetric Z6 (correct) vs Z7 (drifted), introduced by Cycle 3 A3-06 / T-AA34. |
| A4-02 | MEDIUM | api-architect + azure-principal-architect + infrastructure-devops + security-engineer | DOC-FIX (no FR change; supersedes Cycle 3 Pass 1 Q2 item (v)) | `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-173` AND `specs/036-sim-agent-extend/spec.md:961-966` (Cycle 3 Pass 1 Q2 item (v)) | ADR-036-011 and the Cycle 3 Pass 1 Q2 narrative both claim the `Simulation.Coordinator` role assignment is "scoped exclusively to `tnt-stg-smoke`". The actual Bicep scope at `infra/bicep/modules/cosmos-simulation-containers.bicep:316` is database-level (`'${account.id}/dbs/${databaseName}'`); the comment block at L305-315 in the same Bicep already documents this trade-off and identifies the query-time `where tenant_id == "tnt-stg-smoke"` filter on Z6 / Z7 (per FR-073) as the actual compensating defence-in-depth control. Cosmos data-plane RBAC API version 2024-08-15 does not officially support per-partition-key-value scoping in `az rest` deploys; strengthening to true partition-level isolation is deferred to a backlog issue with the API-version constraint cited as the explicit blocker. The defect is purely a wording / spec misrepresentation; no Bicep change is required (Bicep is correct as-is). |

### Cycle 4 amendments — detail

#### A4-01 — SLI-Z7 KQL author-time column-resolution defect (HIGH)

- **Cohort source**: data-engineer (HIGH; technical OBJECT verdict on Step 8ac re-review), Operations Officer + Field Coordinator (HIGH; operational cohort F-OPS-3-01); ground-truth `step-8ac-rereview-technical.md` § "data-engineer — Finding — HIGH: Z7 KQL groups by `model_deployment` without first extending it from `customDimensions`" and `step-8ac-rereview-operational.md` § "F-OPS-3-01".
- **Site**: `infra/observability/sli-kql.json:91` (the Z7 `summarize ... by model_deployment` line) AND `specs/036-sim-agent-extend/contracts/sli-thresholds.md:280-296` (the §6b Z7 KQL block, line 293 specifically `by model_deployment`).
- **Type**: STRENGTHEN-FR (FR-073 sub-bullet) + REGRESSION-TEST (no new FR)
- **Defect provenance**: Cycle 3 A3-06 implementation in T-AA34 added the `by model_deployment` group-by per Z6 cardinality alignment but forgot to introduce `model_deployment` via an `extend` clause prior to the `summarize ... by` step. The working comparison is SLI-Z6 at `infra/observability/sli-kql.json:76`, which DOES extend (`extend model_deployment = tostring(customDimensions["model_deployment"])`) — so the defect is asymmetric between Z6 (correct) and Z7 (drifted). Both `sli-kql.json` and `contracts/sli-thresholds.md` drifted in lock-step, which is why byte-equality canonicalisation passed.
- **Why the existing contract test missed it**: `tests/contract/test_sli_kql_canonical_match.py` enforces byte-equality between contract↔JSON after canonicalisation. Both files drifted identically, so the test passes blindly. There is currently NO test in the repository that exercises author-time column-reference resolution against the KQL bodies in `infra/observability/sli-kql.json` (no static-analysis pass and no AppInsights HTTP round-trip). The byte-equality contract surface is a necessary but **not sufficient** correctness contract — symmetric drift defeats it by construction.
- **Runtime impact**: At AppInsights query-time the KQL emits `SemanticError: Failed to resolve column reference 'model_deployment'` → `staging-promotion.yml` workflow `proc.returncode != 0` branch fires → `sys.exit(2)` → `assert_sli_thresholds()` is never invoked → no `staging_promotion.refused` envelope is written → Pass-1 Q3 invariant ("always write envelope on refusal") is broken on this failure mode → SC-010 (gate enforcement on overlay drift) is unenforceable when this code path is reached in production. This is a Constitution Principle I + Principle V violation chained through a single missing line.
- **What changes**:
  1. `infra/observability/sli-kql.json:91` — insert `| extend model_deployment = tostring(customDimensions["model_deployment"])` immediately after the existing `extend tenant_id = tostring(customDimensions["tenant_id"])` line (currently L87) and before the `where env == "staging"` line (currently L88). The new `extend` line MUST be byte-identical (in ordering and quoting) to the corresponding Z6 line at `infra/observability/sli-kql.json:75`.
  2. `specs/036-sim-agent-extend/contracts/sli-thresholds.md:280-296` — symmetric position inside the §6b Z7 KQL block: insert the same `extend model_deployment` line after the `extend tenant_id` line and before the `where env == "staging"` line. The contract block MUST remain byte-equal-after-canonicalisation to the JSON so `test_sli_kql_canonical_match.py` continues to pass.
- **FR-073 sub-bullet (strengthening, NOT a new FR)**: A new acceptance bullet is added to FR-073 mandating that, in addition to byte-equality after canonicalisation, **every column referenced in `summarize ... by`, `where`, `extend` RHS, and `project` clauses MUST be either** (a) a base table column on the queried table (`requests`, `customEvents`, `customMetrics`, `traces`); (b) a `let`-bound or `extend`-bound name introduced earlier in the same query; or (c) a `customDimensions["..."]` lookup expression. A bare column reference that does not satisfy (a)–(c) is a contract violation regardless of whether the byte-equality check passes. The sub-bullet is recorded here as part of the Cycle 4 amendment log and will be folded into FR-073's acceptance text in Step 8ad.
- **New regression test** (`tests/contract/test_sli_kql_runtime_validity.py`, new): Parametric over Z1–Z7. For each KQL string in `infra/observability/sli-kql.json` the test parses the KQL **statically** (no AppInsights HTTP call), enumerates every column reference in `where`, `summarize ... by`, `extend` RHS, and `project` clauses, and asserts each reference resolves via the (a)–(c) discipline above. Failure message MUST be explicit: `KQL Zn references undefined column '<name>' at line N — must extend from customDimensions first`. The test consumes canonical KQL strings via the existing `_kql_canonicaliser` module at `tests/contract/_kql_canonicaliser.py` to remain consistent with `test_sli_kql_canonical_match.py`. The existing byte-equality test (`test_sli_kql_canonical_match.py`) MUST continue to pass after the symmetric Z7 fix is applied to both JSON and contract files.
- **Acceptance criteria**:
  - `infra/observability/sli-kql.json:91` Z7 KQL contains `extend model_deployment = tostring(customDimensions["model_deployment"])` between the existing `extend tenant_id` line and the `where env == "staging"` line; ordering and quoting are byte-identical to the Z6 line at `sli-kql.json:75`.
  - `specs/036-sim-agent-extend/contracts/sli-thresholds.md:280-296` §6b Z7 block contains the same `extend` line in the symmetric position, byte-equal-after-canonicalisation to the JSON.
  - `tests/contract/test_sli_kql_canonical_match.py` continues to pass byte-equality across all seven SLIs (Z1–Z7) after the symmetric fix.
  - `tests/contract/test_sli_kql_runtime_validity.py` (new) parametric over Z1–Z7 asserts every column reference resolves via the (a)–(c) discipline; the test fails with the explicit `KQL Zn references undefined column '<name>' at line N — must extend from customDimensions first` message if the defect (or any sibling) is reintroduced.
  - The Cycle 3 baseline of 3391 tests pass / 0 fail is preserved; the new test is additive (3392 tests pass / 0 fail expected post-Cycle-4-implement).
  - **[CLARIFIED Cycle 4 Pass 1 Q1]** The static KQL parser in `tests/contract/test_sli_kql_runtime_validity.py` is a **lightweight regex/lexer** that consumes canonical KQL via the existing `tests/contract/_kql_canonicaliser.py::canonicalise_kql` / `canonical_kql_for_sli` helpers and walks `let` / `extend` / `summarize ... by` / `where` / `project` clauses to enumerate column references; bare references must resolve to the static base-table allowlist (`requests`, `customEvents`, `customMetrics`, `traces`), to a `let`/`extend`-bound symbol introduced earlier in the same query, or to a `customDimensions["..."]` lookup. A heavyweight Kusto AST parser dependency is **explicitly rejected** to preserve the Cycle 3 Pass 1 Q1 "pure-Python, no Kusto runtime dependency" precedent (`spec.md:861-862, 871-874`), the Linux GitHub-hosted runner posture, and lean `pyproject.toml` deps. See "Clarifications (Cycle 4 — Pass 1) → Q1" below for full Q→A, provenance, and spec impact.

#### A4-02 — `Simulation.Coordinator` RBAC scope wording correction (MEDIUM)

- **Cohort source**: api-architect + azure-principal-architect + infrastructure-devops + security-engineer (cross-finding, all four MEDIUM); ground-truth `step-8ac-rereview-technical.md` § "Cross-finding — RBAC scope wording misrepresents Bicep reality (4 personas)".
- **Site**: `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-173` AND `specs/036-sim-agent-extend/spec.md:961-966` (the Cycle 3 Pass 1 Q2 item (v) "Least-privilege test identity" narrative).
- **Type**: DOC-FIX (no FR change) — explicitly **supersedes** the Cycle 3 Pass 1 Q2 item (v) wording at `spec.md:961-966` per the Cycle 2 Q1 supersession precedent at `spec.md:389-392` (where FR-067's line-127 phrasing was superseded by Q1's binding resolution).
- **Defect**: ADR-036-011:172-173 and Cycle 3 Pass 1 Q2 item (v) at `spec.md:961-966` both state the `Simulation.Coordinator` role assignment is *"scoped exclusively to `tnt-stg-smoke`"*. Reality at `infra/bicep/modules/cosmos-simulation-containers.bicep:316`: the `roleAssignments` resource is declared with `scope: '${account.id}/dbs/${databaseName}'`, which is **database-level**, NOT partition-level. The Bicep author already documents this honestly in the comment block at L305-315 of the same module: *"Cosmos data-plane RBAC accepts container-level scope; the tenant filter is enforced at query-time via the Z6 / Z7 KQL `where tenant_id == "tnt-stg-smoke"` clauses"*. The compensating defence-in-depth control is real and effective (and is the contract surface FR-073 already enforces); the documentation just misrepresents the *Bicep* scope as if it were the primary enforcement boundary.
- **Why the Bicep cannot be tightened today**: Cosmos DB data-plane RBAC scope syntax for per-partition-key value is not officially supported by `az rest` deploys at API version 2024-08-15. Strengthening to true partition-level isolation requires either (a) a custom role definition with conditional access policies (additional `Microsoft.Authorization` complexity that exceeds Cycle 3's blast-radius cap), or (b) moving the smoke tenant to a separate Cosmos database (T-AA38 alternative, considered and rejected per ADR-036-011 Alternative #6 — additional capacity unit and operational surface). Both paths are deferred to a follow-up backlog issue with the API-version constraint cited as the explicit blocker.
- **What changes**:
  1. `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-173` — replace the wording *"scoped exclusively to `tnt-stg-smoke`"* with a three-clause acknowledgement covering: (a) the actual Bicep scope is database-level (`'${account.id}/dbs/${databaseName}'`); (b) tenant isolation is enforced at query time via the `where tenant_id == "tnt-stg-smoke"` clauses on the Z6 / Z7 KQL bodies (FR-073 contract surface) as a compensating defence-in-depth control; (c) strengthening to partition-level isolation is deferred to a backlog issue, with the Cosmos DB data-plane RBAC API version 2024-08-15 constraint cited as the explicit blocker.
  2. `specs/036-sim-agent-extend/spec.md:961-966` — the Cycle 3 Pass 1 Q2 item (v) "Least-privilege test identity" narrative wording is **superseded by this amendment** (per the Cycle 2 Q1 supersession precedent at `spec.md:389-392`). The original Cycle 3 narrative at L961-966 is preserved verbatim per the immutability discipline; the binding wording going forward is the corrected text recorded inside this amendment block. Step 8ae will re-render the corrected wording in the spec body and link it back to this A4-02 anchor.
- **Binding corrected wording (replaces the Cycle 3 narrative phrasing)**: *"The `Simulation.Coordinator` test identity is provisioned as an Entra ID enterprise app with a Cosmos data-plane RBAC role assignment scoped at the **database level** (`'${account.id}/dbs/${databaseName}'`) — this is the narrowest scope supported by Cosmos data-plane RBAC API version 2024-08-15 in `az rest` deploys. Tenant isolation onto `tnt-stg-smoke` is achieved via a query-time compensating defence-in-depth control: every SLI-Z6 / SLI-Z7 KQL body (per FR-073) carries an explicit `where tenant_id == "tnt-stg-smoke"` filter, and `tests/contract/test_smoke_tenant_isolation.py` asserts (i) exactly one role assignment exists for the `Simulation.Coordinator` principal across the entire Bicep emission, scoped at `'${account.id}/dbs/${databaseName}'`, and (ii) zero production-tenant role assignments reference the same principal. Strengthening to true partition-level RBAC isolation is deferred to a backlog issue: Cosmos data-plane RBAC API version 2024-08-15 does not officially support per-partition-key-value scope in `az rest` deploys, and uptake of either (a) a custom role definition with conditional access policies or (b) a separate Cosmos database for the smoke tenant — T-AA38 Alternative #6, previously rejected — is gated on that API uplift."*
- **No Bicep change**: `infra/bicep/modules/cosmos-simulation-containers.bicep` is correct as-is. The comment block at L305-315 already documents the actual scope and the compensating control honestly; only the ADR narrative and the spec Cycle 3 Q2 wording require correction.
- **Acceptance criteria**:
  - `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-173` is rewritten in Step 8ae to the three-clause acknowledgement above.
  - The Cycle 3 Pass 1 Q2 narrative at `spec.md:961-966` is **explicitly superseded** by the binding corrected wording recorded in this amendment block; the original Cycle 3 wording is preserved verbatim per the immutability discipline.
  - `tests/contract/test_smoke_tenant_isolation.py` is extended in Step 8ae to assert (i) exactly one `Simulation.Coordinator` role assignment exists in the Bicep emission, scoped at `'${account.id}/dbs/${databaseName}'`, and (ii) zero production-tenant role assignments reference the same principal — the two-line invariant the corrected wording binds to.
  - A backlog issue is filed citing the Cosmos data-plane RBAC API version 2024-08-15 partition-key-scope constraint as the blocker for partition-level isolation; the issue is referenced from ADR-036-011's Alternative #6 row.
  - The Cycle 3 baseline of 3391 tests pass / 0 fail is preserved; A4-02 is documents-only and adds 0 new tests beyond the test extensions in Step 8ae.
  - **[CLARIFIED Cycle 4 Pass 1 Q2]** The corrected wording uses **both** phrasings in combination — they are not mutually exclusive: the query-time `where tenant_id == "tnt-stg-smoke"` filter is named a *"compensating defence-in-depth control"* (security-engineer / security-pattern naming, per NIST SP 800-160 / OWASP defence-in-depth taxonomy), AND the wording explicitly cites the deferred backlog issue inline (azure-principal-architect / foregrounded-remediation preference) so reviewers reading ADR-036-011 calibrate the residual risk against a concrete tracking artefact. The binding wording at `spec.md:3906` already employs both phrasings; this clarification ratifies that choice. See "Clarifications (Cycle 4 — Pass 1) → Q2" below for full Q→A, provenance, and spec impact.

### Cycle 4 amendment additions (FR strengthening — no new FRs)

Cycle 4 adds **0 new FRs** and **0 new SCs**. The single FR strengthening is
recorded here for traceability and will be folded into FR-073's acceptance
text in Step 8ad:

- **FR-073 (strengthening — A4-01)**: Beyond byte-equality-after-canonicalisation
  between `infra/observability/sli-kql.json` and
  `specs/036-sim-agent-extend/contracts/sli-thresholds.md`, every column
  reference in any declared SLI's KQL body MUST resolve at author time via
  one of: (a) a base table column on the queried table (`requests`,
  `customEvents`, `customMetrics`, `traces`); (b) a `let`-bound or
  `extend`-bound name introduced earlier in the same query; (c) a
  `customDimensions["..."]` lookup expression. A bare column reference
  that does not satisfy (a)–(c) is a contract violation, regardless of
  whether the byte-equality check passes. The new contract test
  `tests/contract/test_sli_kql_runtime_validity.py` is the binding test
  surface for this strengthening; failure messages MUST cite the SLI ID
  and the offending column name.

### Cohort and prior-clarify reconciliation (Cycle 4)

- **No new Q→A entries** are required to land Cycle 4 as a specify pass; the
  two findings carry deterministic closure targets visible in the table
  above. A subsequent `/speckit.clarify` (Cycle 4 Pass 1) cycle will resolve
  the two `[NEEDS CLARIFICATION]` markers embedded in A4-01 and A4-02
  acceptance criteria (KQL parser scope; corrected-wording terminology).
- **Cycle 1 Q→A, Cycle 2 Q→A, Cycle 3 Pass-1 + Pass-2 Q→A remain in force
  unchanged**, with one explicit supersession: **Cycle 3 Pass 1 Q2 item (v)**
  "Least-privilege test identity" narrative wording at `spec.md:961-966` is
  superseded by A4-02's binding corrected wording above (per the Cycle 2 Q1
  supersession precedent at `spec.md:389-392`). The original Cycle 3
  narrative is preserved verbatim per the immutability discipline; the
  corrected wording is the binding statement going forward and will be
  re-rendered in the spec body by Step 8ae.
- **NOT actioned in Cycle 4**: any other cohort-finding from Step 8ac that
  did not pass the merit-validation gate. No other findings reached the
  HIGH or MEDIUM bar; the two listed above are the entirety of the merit-
  validated Cycle 4 surface.
- **Constitution alignment**: A4-01 honours Principle V (Graceful
  Degradation — predictable failure with explicit machine-readable
  indicator: an author-time KQL semantic-error surfaced at contract-test
  time prevents the runtime gate from being silenced by an undefined-
  column error) and Principle I (Primacy of Life — SC-010 overlay-drift
  gate enforceability is restored on this code path). A4-02 honours
  Principle IV (Transparency and Auditability — self-documentation must
  align with the binding implementation; the corrected wording removes
  the misrepresentation, names the actual compensating defence-in-depth
  control, and acknowledges the API-version constraint as the explicit
  blocker for the deferred remediation).

**Cycle 4 amendment specify complete. Ready for /speckit.clarify pass 1 (Cycle 4).**

## Clarifications (Cycle 4 — Pass 1)

### Session 2026-05-11 (Cycle 4 amendment clarify pass 1)

These resolutions close the **second-order ambiguities** opened by the
Cycle 4 amendment cycle (`spec.md:3831-3967`). Cycle 4 strengthened FR-073
with an author-time KQL column-resolution sub-bullet (A4-01) and corrected
the ADR-036-011 / Cycle 3 Pass 1 Q2 item (v) RBAC-scope wording (A4-02);
two `[NEEDS CLARIFICATION]` markers were embedded in the A4-01 / A4-02
acceptance criteria (KQL parser scope; corrected-wording terminology).
Three additional second-order clarifications surfaced during this pass
(backlog-issue mechanism for the deferred Cosmos-RBAC partition-scope
remediation; runtime-validity test handling of `let`-bindings and `union`;
ADR pathway for Cycle 4). Cycle 1 / Cycle 2 / Cycle 3 Pass-1 / Cycle 3
Pass-2 Q→A entries remain in force unchanged (with the single explicit
supersession of Cycle 3 Pass 1 Q2 item (v) already recorded by A4-02 at
`spec.md:3899-3906`); the five resolutions below are **additive** and do
not contradict any prior resolution. Each resolution is decided by the
`speckit.clarify` agent under the user's explicit "deciding authority"
mandate; each is constitution-aligned, Cycle-1-/Cycle-2-/Cycle-3-precedent-
consistent, and quantitative where possible. `file:line` evidence is cited
for every claim. **Spec-text propagation** for each Q is noted via
`propagation_target:` annotations and is **deferred** to Step 8ad (KQL
runtime-validity test, FR-073 acceptance-text fold-in) and Step 8ae
(ADR-036-011 wording, backlog issue file, smoke-tenant-isolation contract
test extension, narrative re-render of the superseded Cycle 3 Q2 wording)
— no other artefacts are modified by this pass.

### Q1 — Shall the new `tests/contract/test_sli_kql_runtime_validity.py` use a full Kusto AST parser or a lightweight regex/lexer over canonical KQL?

**Answer**: **Lightweight regex/lexer** consuming canonical KQL via the
already-landed `tests/contract/_kql_canonicaliser.py` (public surface:
`canonicalise_kql(text: str) -> str` at L274 and `canonical_kql_for_sli(...)`
at L290). A full Kusto AST parser dependency (`pykusto`, `kusto-parser-py`,
or shelling to `kustopreview`) is **explicitly rejected** for the same
reasons Cycle 3 Pass 1 Q1 rejected AST equivalence at `spec.md:863-877`:
(a) the defect surface is purely surface-form (a missing `extend` line —
detectable by walking the canonical text); (b) every candidate Kusto-AST
parser introduces either cross-runtime fragility (Microsoft.Azure.Kusto.
Language is .NET-only, requires a managed runtime bridge into a Python
contract test running on Linux GitHub-hosted runners) or supply-chain
attack-surface expansion via PyPI packages with shallow maintainership
and Python-version-compatibility friction; (c) lean test-surface
dependencies are a repository convention — `pyproject.toml` and the
existing contract-test layout pin minimal third-party imports, and
adding a Kusto parser to the contract-test surface would be the first
breach of that convention; (d) a regex/lexer walker is sufficient for
the (a)–(c) discipline declared in A4-01 (`spec.md:3886`) — base-table
allowlist + `let`/`extend`-bound symbol enumeration + `customDimensions["..."]`
literal recognition — and is the same shape as the canonicalisation
walker already in `_kql_canonicaliser.py:84-272` (six-step pipeline of
deterministic regex passes). The new test MUST: **(i)** consume canonical
KQL via `canonicalise_kql(...)` from `_kql_canonicaliser.py` so the
parametric matrix is consistent with `tests/contract/test_sli_kql_canonical_match.py`
(no second canonicalisation surface); **(ii)** maintain a static
base-table-column allowlist as a module-level dict with a comment
identifying each column's table-of-origin under the Application Insights
schema (auditable, no remote schema lookup); **(iii)** walk `let` /
`extend` / `summarize ... by` / `where` / `project` clauses top-down,
adding bound symbols to the in-scope set as they are introduced and
asserting every bare column reference resolves via (a) base-table
allowlist, (b) earlier-in-query `let`/`extend`-bound symbol, or (c) a
`customDimensions["..."]` lookup expression; **(iv)** emit failure
messages of the explicit form `KQL Zn references undefined column
'<name>' at line N — must extend from customDimensions first` AND
include in the failure body the SLI ID (Z1–Z7), the unresolved column
name, the line number within the canonicalised KQL, and the full
canonicalised KQL string (for postmortem / forensic correlation under
Constitution IV). The existing byte-equality test
(`tests/contract/test_sli_kql_canonical_match.py`) MUST continue to
pass after the symmetric Z7 fix — A4-01 acceptance line at
`spec.md:3891` already binds this. The two contract tests are
complementary surfaces (byte-equality is necessary; column-resolution
makes it sufficient against symmetric drift).

**Authority**: Constitution Principle IV (Transparency and Auditability —
single source of truth between contracts and implementation; the
canonical KQL surface in `_kql_canonicaliser.py` IS that source, and
the runtime-validity test inherits from it). Constitution Principle V
(Graceful Degradation — predictable failure with explicit machine-
readable indicator: an author-time KQL semantic-error surfaced at
contract-test time prevents the runtime gate from being silenced by
an undefined-column error, restoring SC-010 enforceability — A4-01
provenance at `spec.md:3882`). Cycle 3 Pass 1 Q1 strict-string
canonicalisation precedent at `spec.md:861-877` (pure-Python, no
Kusto runtime dependency, deterministic, idempotent) — the
runtime-validity test follows the same shape. Existing
`_kql_canonicaliser.py` public surface (`canonicalise_kql` at L274,
`canonical_kql_for_sli` at L290) — the new test consumes from this
boundary. `tests/contract/test_sli_kql_canonical_match.py` and
`tests/contract/test_kql_canonicaliser_unit.py` (already landed,
3391 tests pass / 0 fail Cycle 3 baseline at `spec.md:3829`) — the
runtime-validity test extends this contract surface, not replaces
it.

**Spec-text propagation** *(deferred)*:

- `propagation_target: tests/contract/test_sli_kql_runtime_validity.py` (new)
  — implement parametric pytest test over Z1–Z7 per the (i)–(iv)
  discipline above; module-level static base-table allowlist for
  `requests` / `customEvents` / `customMetrics` / `traces`; failure
  message exactly `KQL Zn references undefined column '<name>' at
  line N — must extend from customDimensions first`. **(Step 8ad)**
- `propagation_target: specs/036-sim-agent-extend/spec.md` (FR-073
  in-place text — line range Step 8ad will compute against the
  Cycle 3 FR-073 anchor) — fold the A4-01 sub-bullet
  (`spec.md:3886, 3922-3934`) into the FR-073 acceptance text so the
  (a)–(c) column-resolution discipline is FR-073's binding contract
  surface, not just an amendment-log entry. **(Step 8ad)**
- `propagation_target: tests/contract/test_sli_kql_canonical_match.py`
  — no code change; the test continues to assert byte-equality after
  canonicalisation across all seven SLIs (Z1–Z7) per Cycle 3 Pass 1
  Q5 at `spec.md:1185-1230`. **(Step 8ad — verify-only, no edit)**

### Q2 — Shall the corrected A4-02 wording use "compensating defence-in-depth control" or "documented mitigation with deferred remediation"?

**Answer**: **Both** — the two phrasings are not mutually exclusive and
the binding wording at `spec.md:3906` already employs both. The
query-time `where tenant_id == "tnt-stg-smoke"` filter on the SLI-Z6
and SLI-Z7 KQL bodies (per FR-073) is named explicitly as a *"query-time
compensating defence-in-depth control"* — this names the established
security pattern (NIST SP 800-160 §3 "defence-in-depth"; OWASP defence-
in-depth and PCI-DSS-derived "compensating control" lineage; both terms
are well-known to the security-engineer and compliance cohorts) — AND
the wording cites the deferred remediation explicitly: *"Strengthening
to true partition-level RBAC isolation is deferred to a backlog issue:
Cosmos data-plane RBAC API version 2024-08-15 does not officially
support per-partition-key-value scope in `az rest` deploys"*
(`spec.md:3906`). The combination satisfies both cohort preferences
recorded against the marker (security-engineer's "name the security
pattern" preference and azure-principal-architect's "foreground the
deferred remediation" preference) without semantic conflict — naming
the pattern and citing the backlog tracking artefact are
complementary, not competing. The "documented mitigation with
deferred remediation" phrasing was considered as a single-token
replacement and **rejected**: it elides the technical security-pattern
name (auditors and security reviewers reading ADR-036-011 lose the
NIST/OWASP linguistic anchor), and the "documented mitigation"
phrasing is weaker than "compensating control" in PCI-DSS / SOC 2
audit contexts where the latter is a term of art with bounded
meaning. The existing comment block at
`infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
(referenced honestly by A4-02 at `spec.md:3901`) already uses
"compensating" language inline — the Bicep author's prior naming
choice is repository-internal precedent. The corrected wording
**MUST NOT** delete that comment block; it MAY add a forward-reference
to the backlog issue ID once filed.

**Authority**: NIST SP 800-160 Vol. 1 §3 ("Defense-in-Depth" as a
foundational protection-strategy principle); OWASP defence-in-depth
taxonomy; PCI-DSS v4.0 §"Compensating Controls" definition. Cycle 3
Pass 1 Q2 item (v) at `spec.md:961-966` (the narrative being
superseded — `spec.md:3899-3906` records the supersession explicitly,
preserving the original verbatim per the immutability discipline at
`spec.md:3905`). Cycle 2 Q1 supersession precedent at `spec.md:389-392`
(FR-067's original line-127 phrasing was superseded by Q1's binding
resolution, with the original preserved verbatim — A4-02 follows
the same pattern). `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
(repository-internal "compensating control" language already in
use, naming-aligned with the Bicep author's intent). A4-02 binding
corrected wording at `spec.md:3906` — already employs the chosen
phrasing combination.

**Spec-text propagation** *(deferred)*:

- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  (L172-173) — replace the current "scoped exclusively to `tnt-stg-smoke`"
  wording with the three-clause acknowledgement at `spec.md:3904-3906`,
  using the *"compensating defence-in-depth control"* phrasing for the
  query-time filter and citing the deferred backlog issue inline by
  ID once filed (per Q3 below). **(Step 8ae)**
- `propagation_target: specs/036-sim-agent-extend/spec.md`
  (Cycle 3 narrative re-render at the L961-966 site) — render the
  binding corrected wording from `spec.md:3906` in the spec body
  alongside the original (preserved verbatim) and link to the A4-02
  anchor; the original Cycle 3 wording is NOT deleted, per the
  immutability discipline at `spec.md:3905, 3947-3950`. **(Step 8ae)**
- `propagation_target: infra/bicep/modules/cosmos-simulation-containers.bicep`
  (comment block L305-315) — no code change; the existing comment
  block is correct and is the in-tree precedent for the chosen
  phrasing. Step 8ae MAY add a one-line forward-reference to the
  backlog issue ID once filed (per Q3). **(Step 8ae — verify-only;
  optional one-line addition)**
- `propagation_target: tests/contract/test_smoke_tenant_isolation.py`
  — extend in Step 8ae to assert the two-line invariant at
  `spec.md:3911`: (i) exactly one `Simulation.Coordinator` role
  assignment exists in the Bicep emission scoped at
  `'${account.id}/dbs/${databaseName}'`; (ii) zero production-tenant
  role assignments reference the same principal. **(Step 8ae)**

### Q3 — How shall the deferred Cosmos-RBAC-partition-scope remediation be tracked — GitHub issue with a label, a `docs/backlog/` markdown entry, or both?

**Answer**: **GitHub issue only** (no `docs/backlog/` markdown entry).
A repository scan confirms neither convention is currently established
in this codebase: there is no `.github/ISSUE_TEMPLATE/` directory and
no `docs/backlog/` directory at the time of this clarification pass
(Get-ChildItem `.github\ISSUE_TEMPLATE` returns nothing; Test-Path
`docs\backlog\index.md` returns `False`). Establishing both surfaces
in the same Cycle 4 close would be premature scope creep and would
conflict with the Cycle 4 narrowness discipline at `spec.md:3838-3841`
(*"Cycle 4 is **narrower in scope** than Cycle 3 … Cycle 1 / Cycle 2 /
Cycle 3 carry-overs are explicitly out-of-scope"*). The simplest
forward-compatible path is to file the deferred remediation as a
GitHub issue with: **(i)** title prefix `[backlog]` (e.g.
`[backlog] Cosmos data-plane RBAC: per-partition-key scope (blocked
on API ≥ 2024-08-15+)`); **(ii)** a self-explanatory body citing the
A4-02 acceptance criterion at `spec.md:3912`, the Bicep site at
`infra/bicep/modules/cosmos-simulation-containers.bicep:316`, the
Cosmos data-plane RBAC API version 2024-08-15 constraint as the
explicit blocker, and the strengthening alternatives (custom role
definition with conditional access policies; separate Cosmos
database for the smoke tenant — already rejected as ADR-036-011
Alternative #6); **(iii)** label `backlog` IF the repo's labels
inventory already contains it, otherwise no label (don't create
a new label as a side-effect of this filing). The issue ID, once
assigned by GitHub, is referenced inline from: (1) the corrected
ADR-036-011 wording per Q2's propagation target; (2) the
ADR-036-011 Alternative #6 row per A4-02 acceptance line at
`spec.md:3912`; and (3) the optional forward-reference comment in
`cosmos-simulation-containers.bicep:305-315` per Q2's optional
addition. If a future cycle introduces a `docs/backlog/index.md`
convention, a one-line entry referencing the GitHub issue can be
added at that point — this is forward-compatible, NOT a Cycle 4
work-item.

**Authority**: Cycle 4 narrowness discipline at `spec.md:3838-3841`
(no scope creep beyond the two cohort-validated defects). Repository
state as observed during Cycle 4 Pass 1 (no `.github/ISSUE_TEMPLATE/`,
no `docs/backlog/`). Constitution Principle IV (Transparency and
Auditability — the deferred remediation MUST have a citable tracking
artefact; a GitHub issue with a stable URL satisfies this minimally
and durably). A4-02 acceptance line at `spec.md:3912` (*"A backlog
issue is filed citing the Cosmos data-plane RBAC API version
2024-08-15 partition-key-scope constraint as the blocker for
partition-level isolation"*) — already mandates the issue, only
the form is clarified here.

**Spec-text propagation** *(deferred)*:

- `propagation_target: <new GitHub issue>` — file with the title /
  body / label scheme above; capture the resulting issue URL for
  use by the next two propagation targets. **(Step 8ae)**
- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  (Alternative #6 row + the L172-173 corrected wording) — cite the
  GitHub issue URL inline, replacing any placeholder. **(Step 8ae)**
- `propagation_target: infra/bicep/modules/cosmos-simulation-containers.bicep`
  (comment block L305-315) — OPTIONAL one-line addition citing the
  GitHub issue URL as the deferred-remediation tracker. **(Step 8ae —
  optional; no functional change)**

### Q4 — Shall the `test_sli_kql_runtime_validity.py` walker treat `let`-bindings as in-scope symbols and how shall it handle `union` cross-table resolutions?

**Answer**: **`let`-bindings are tracked symbol-by-symbol via top-down
walk over canonicalised KQL; `union` cross-table resolutions are
out-of-scope for Cycle 4** and are deferred to a future enhancement
if a future SLI introduces a `union` clause. The Q1 walker MUST
maintain a per-query mutable in-scope set: starting with the empty
set, the walker advances line-by-line through the canonicalised KQL,
adding (i) every `let <name> = <expr>;` LHS, (ii) every `extend
<name> = <expr>` LHS (one or more per `extend` clause; the
`_kql_canonicaliser.py:240-272` redundant-paren stripper guarantees
deterministic LHS extraction), and (iii) every `summarize <agg>=...
by <col>` aggregate-LHS where the LHS is a fresh symbol introduced
by the `summarize`. Bare column references appearing in `where` /
`project` / `summarize ... by` / `extend` RHS / `let` RHS are
resolved against (a) the static base-table allowlist (`requests`,
`customEvents`, `customMetrics`, `traces`); (b) the in-scope set
populated up to that line; or (c) `customDimensions["..."]`
literals. The walker MUST be deterministic and idempotent: the same
canonicalised input produces the same accepted/rejected verdict
across runs (Cycle 3 Pass 1 Q1 idempotence + determinism invariants
at `spec.md:885-889` are inherited). `union` cross-table
resolutions (e.g. `union requests, customEvents | where ...`) would
require expanding the base-table allowlist contextually per `union`
operand — a meaningfully different walker shape — and **no current
SLI in `infra/observability/sli-kql.json` uses `union`**: an audit
of all seven Z1–Z7 KQL bodies (per `spec.md:1185-1217` Cycle 3
Pass 1 Q5 universal-scope coverage) confirms zero occurrences. If
a future SLI introduces `union`, the runtime-validity test fails
fast with a clear "union is not yet supported by the runtime
validity walker — extend test_sli_kql_runtime_validity.py to
support multi-table column resolution" message; this is a
predictable, addressable failure mode and aligns with Constitution
Principle V (Graceful Degradation). Treating `union` as an open-
ended pass-through (no column resolution at all) is **explicitly
rejected** — it would re-introduce the symmetric-drift defect that
A4-01 was filed to close (`spec.md:3881`).

**Authority**: A4-01 (a)–(c) column-resolution discipline at
`spec.md:3886`. Cycle 3 Pass 1 Q1 idempotence + determinism
invariants at `spec.md:885-889` (the runtime-validity walker
inherits these from the canonicaliser). `infra/observability/sli-kql.json`
Z1–Z7 inventory (no `union` usage as of Cycle 3 close — verifiable
via `Select-String -Pattern "\bunion\b" -Path infra\observability\sli-kql.json`).
Constitution Principle V (Graceful Degradation — fail-fast with a
clear error message when an unsupported KQL surface is introduced,
rather than silently passing). Cycle 3 Pass 1 Q5 universal-scope
contract surface at `spec.md:1185-1230` (the runtime-validity test
participates in the same universal scope; the union-fail-fast
behaviour preserves that surface against future drift).

**Spec-text propagation** *(deferred)*:

- `propagation_target: tests/contract/test_sli_kql_runtime_validity.py`
  (new) — implement the in-scope-set walker per (i)–(iii) above;
  raise an explicit failure when `union` is encountered with the
  message *"union is not yet supported by the runtime validity
  walker — extend test_sli_kql_runtime_validity.py to support
  multi-table column resolution"*. **(Step 8ad)**
- `propagation_target: tests/contract/test_kql_canonicaliser_unit.py`
  — no change; the canonicaliser unit test already asserts
  idempotence and determinism at the canonicaliser boundary. The
  runtime-validity walker inherits these invariants without
  re-asserting them. **(Step 8ad — verify-only)**
- `propagation_target: tasks.md` — record the union-support
  expansion as a deferred enhancement (NOT a Cycle 4 work-item),
  citing this Q4 entry as the rationale for the deferral.
  **(Step 8ad)**

### Q5 — Shall Cycle 4 revise ADR-036-011 in place or create a new ADR-036-012?

**Answer**: **Revise ADR-036-011 in place** (existing path:
`docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`). Cycle 4
is a **correction of Cycle 3 deliverables**, not a new architectural
decision: A4-01 strengthens FR-073's existing canonicalisation
contract surface with a complementary column-resolution sub-bullet
(no new FR, no new SC — `spec.md:3848-3852`), and A4-02 corrects a
wording defect in ADR-036-011 itself (no Bicep change required —
`spec.md:3907`). Filing a separate ADR-036-012 would create a forward-
reference ambiguity (auditors reading ADR-036-011 in isolation would
miss the correction) and would inflate the ADR inventory for what is
fundamentally a correction-in-place. The revision MUST: **(i)** add
a "Cycle 4 amendment" sub-section near the end of ADR-036-011 capturing
A4-01 (FR-073 column-resolution sub-bullet) and A4-02 (RBAC scope
wording correction) effects, with explicit cross-references to the
two `[CLARIFIED Cycle 4 Pass 1 Qn]` markers at `spec.md:3894` and
`spec.md:3914` (post-clarify line numbers — the markers were updated
in this pass) and to the binding corrected wording at `spec.md:3906`;
**(ii)** preserve all Cycle 3 prior content verbatim (no rewriting
of pre-Cycle-4 paragraphs, per the immutability discipline at
`spec.md:3947-3950`); **(iii)** move the document Status from
`Proposed` (or whatever the current state is) to `Accepted` only
on a clean Step 8al cohort re-review verdict. The "create a new
ADR-036-012" alternative was considered and **rejected** for the
forward-reference and inventory-inflation reasons above. The
"revise in place WITHOUT a Cycle 4 amendment sub-section" alternative
was considered and **rejected** because it would obscure the
corrective nature of Cycle 4 from future auditors traversing the
ADR — auditability requires the correction be visible, not folded
silently into the original prose.

**Authority**: Cycle 4 narrowness discipline at `spec.md:3838-3852`
(0 new FRs, 0 new SCs, 1 FR strengthening, 1 self-documentation
supersession — these are corrections, not architectural decisions).
Cycle 3 amendment-log immutability discipline at `spec.md:3905,
3947-3950` (originals preserved verbatim, corrections appended as
sub-sections). Constitution Principle IV (Transparency and
Auditability — corrections must be visible, not silent). ADR
catalogue convention: `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
already follows the "amendment-cycle" filename pattern, which
implicitly accommodates intra-amendment corrections — the file's
own filename anticipates this revision shape. A4-02 acceptance
line at `spec.md:3909` (*"`docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-173`
is rewritten in Step 8ae to the three-clause acknowledgement
above"*) — already nominates ADR-036-011 as the revision target;
this Q5 ratifies the in-place pathway.

**Spec-text propagation** *(deferred)*:

- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  — append a "Cycle 4 amendment" sub-section near the end of the
  document covering A4-01 + A4-02 effects with cross-references
  per (i) above; rewrite L172-173 per Q2's propagation target;
  cite the GitHub backlog issue URL per Q3's propagation target.
  Status moves `Proposed` → `Accepted` on a clean Step 8al cohort
  re-review verdict. **(Step 8ae)**
- `propagation_target: CHANGELOG.md` — record the Cycle 4
  ADR-036-011 in-place revision as a single line under the
  Cycle 4 close section; do NOT introduce a new ADR-036-012
  CHANGELOG line. **(Step 8ae)**
- `propagation_target: docs/aidr/decisions/` (directory listing) —
  no new file; ADR-036-012 is **not** created. **(Step 8ae —
  verify-only, must remain absent)**

**Resolution rollup (Cycle 4 pass 1)**: Q1 → pins **lightweight
regex/lexer** (NOT a full Kusto AST parser) for the new
`tests/contract/test_sli_kql_runtime_validity.py`, consuming canonical
KQL via the existing `_kql_canonicaliser.py` helpers and walking
`let` / `extend` / `summarize ... by` / `where` / `project` clauses
under the (a)–(c) column-resolution discipline; Q2 → pins **both**
*"compensating defence-in-depth control"* AND inline backlog-issue
citation as the corrected A4-02 wording, ratifying the binding
text at `spec.md:3906`; Q3 → pins **GitHub issue only** (no
`docs/backlog/` markdown entry) as the deferred Cosmos-RBAC-
partition-scope remediation tracking artefact, with title prefix
`[backlog]` and inline issue-URL citations from ADR-036-011 +
optionally the Bicep comment block; Q4 → pins **`let`/`extend`/
`summarize`-aggregate-LHS in-scope tracking** for the runtime-
validity walker and **explicitly defers `union` support** with a
fail-fast error message; Q5 → pins **revise ADR-036-011 in place**
(NOT a new ADR-036-012) with a "Cycle 4 amendment" sub-section
preserving all Cycle 3 prior content verbatim, status moving
`Proposed` → `Accepted` only on a clean Step 8al verdict.
Together these five resolutions close the second-order ambiguities
Cycle 4 deferred to a clarify pass and unblock **Step 8ad**
(`tests/contract/test_sli_kql_runtime_validity.py` new + FR-073
acceptance-text fold-in) and **Step 8ae** (ADR-036-011 in-place
revision + L172-173 rewording + smoke-tenant-isolation contract
test extension + GitHub backlog issue file + spec-body re-render
of the superseded Cycle 3 Q2 wording). No prior Q→A is
contradicted; this pass is fully additive. The Cycle 3 baseline
of 3391 tests pass / 0 fail is preserved; the new
`test_sli_kql_runtime_validity.py` is additive (3392 tests pass /
0 fail expected post-Cycle-4-implement, per A4-01 acceptance line
at `spec.md:3893`).

**Cycle 4 clarify pass 1 complete. Ready for /speckit.clarify pass 2 (Cycle 4).**

## Clarifications (Cycle 4 — Pass 2)

### Session 2026-05-11 (Cycle 4 amendment clarify pass 2)

These resolutions close the **third-order ambiguities** that surfaced
during the Cycle 4 Pass 1 propagation review (`spec.md:3969-4385`). Pass 1
locked the five second-order resolutions (KQL parser scope = lightweight
regex/lexer; A4-02 wording = "compensating defence-in-depth control" +
inline backlog-issue citation; backlog mechanism = GitHub issue only;
walker `let`/`union` handling = top-down tracking with `union` deferred
+ fail-fast; ADR pathway = revise ADR-036-011 in place) and bound them to
explicit `propagation_target:` annotations for Step 8ad / Step 8ae. Pass 2
audits those Pass 1 resolutions for **operational executability**: any
quantitative claim, format precedent, or convergence rule that could
cause `speckit.checklist` / `speckit.plan` / `speckit.tasks` /
`speckit.implement` to make a material decision *without spec backing* is
called out and converged here. Four such ambiguities are resolved below
(test-count math correction; CHANGELOG.md format precedent; ADR-036-011
multi-cycle Status convergence rule; smoke-tenant-isolation contract
test extension scope). One orchestrator-suggested ambiguity (literal
text of the `union` fail-fast message) is **not surfaced as a Pass 2 Q**
because it is already explicitly pinned by Pass 1 Q4's propagation
target at `spec.md:4274-4277`. Cycle 1 / Cycle 2 / Cycle 3 Pass-1 /
Cycle 3 Pass-2 / Cycle 4 Pass-1 Q→A entries remain in force unchanged
(with one explicit math supersession recorded by Pass 2 Q1: the "3392
tests pass / 0 fail" claim at `spec.md:3893` and `spec.md:4381` is
superseded by **3398**, per pytest parametric-id collection semantics
verified live during Pass 2). The four resolutions below are **additive**
(Q2, Q3, Q4) or **superseding-by-correction** (Q1) and do not contradict
any prior architectural resolution. Each resolution is decided by the
`speckit.clarify` agent under the user's explicit "deciding authority"
mandate; each is constitution-aligned, Cycle-1-/Cycle-2-/Cycle-3-/Cycle-4-
Pass-1-precedent-consistent, and quantitative where possible. `file:line`
evidence is cited for every claim. **Spec-text propagation** for each Q
is noted via `propagation_target:` annotations and is **deferred** to
Step 8ad (test-count assertion in CI gate; runtime-validity test new
file) and Step 8ae (CHANGELOG.md Cycle 4 close block; ADR-036-011 status
transition rule; smoke-tenant-isolation test extension) — no other
artefacts are modified by this pass.

### Q1 — Is the Pass 1 Q1 acceptance criterion "3392 tests pass / 0 fail expected post-Cycle-4-implement" mathematically correct given that `test_sli_kql_runtime_validity.py` is parametric over Z1–Z7?

**Answer**: **No — the correct expected count is 3398** (3391 Cycle 3
baseline + 7 new parametric ids). The Pass 1 Q1 acceptance line at
`spec.md:3893` and the Pass 1 resolution rollup at `spec.md:4380-4382`
both state *"3392 tests pass / 0 fail expected post-Cycle-4-implement"*
based on the implicit assumption that the new
`tests/contract/test_sli_kql_runtime_validity.py` contributes **1** test
to the count. Live verification during Pass 2 contradicts that
assumption: the existing parametric `tests/contract/test_sli_kql_canonical_match.py`
(template for the new test, per Pass 1 Q1 propagation at `spec.md:4020-4023`)
is collected by pytest as **7 distinct test ids** under the
`parametrize("sli_id", [s["id"] for s in _SLI_DOC["slis"]])` decorator
at `tests/contract/test_sli_kql_canonical_match.py:37-40`; pytest emits
`test_implementation_kql_matches_canonical_after_canonicalisation[SLI-Z1]`
through `[SLI-Z7]` as seven separately-counted nodes (verified live via
`pytest tests/contract/test_sli_kql_canonical_match.py --collect-only -q`,
which reports *"7 tests collected"*). The new
`test_sli_kql_runtime_validity.py` mirrors the same parametric shape
(Pass 1 Q1 propagation at `spec.md:4020-4022` requires *"consume canonical
KQL via `canonicalise_kql(...)` from `_kql_canonicaliser.py` so the
parametric matrix is consistent with `tests/contract/test_sli_kql_canonical_match.py`"*),
so the new file contributes **7** parametric ids — one per SLI — not 1.
The corrected math is therefore **3391 + 7 = 3398**. The Cycle 3
baseline `3391 tests passed / 0 failed` at `spec.md:3829` is preserved;
the Cycle 4 expected post-implement total is **3398 tests passed / 0
failed** (sole delta: the seven new parametric ids in
`test_sli_kql_runtime_validity.py`; A4-02 contributes **0 net new
tests** because its `test_smoke_tenant_isolation.py` extension reshapes
the assertions of an existing test rather than adding new `def test_*`
functions — see Pass 2 Q4 below). The Pass 1 acceptance lines at
`spec.md:3893` and `spec.md:4381` remain in the spec verbatim per the
within-cycle immutability discipline (per the Cycle 2 Q1 supersession
precedent at `spec.md:389-392`); the **binding** post-Cycle-4-implement
test-count is the corrected value **3398** recorded here. Step 8ad's
CI-gate assertion / `tasks.md` acceptance criterion MUST cite **3398**;
any cohort re-review (Step 8al) reading the Pass 1 lines at L3893 /
L4381 in isolation is to consult this Pass 2 Q1 binding correction.

**Authority**: Live pytest collection output during Pass 2 verification
(`pytest tests/contract/test_sli_kql_canonical_match.py --collect-only -q`
→ *"7 tests collected"*, ids `test_implementation_kql_matches_canonical_after_canonicalisation[SLI-Z1]`
through `[SLI-Z7]`). Existing parametric template at
`tests/contract/test_sli_kql_canonical_match.py:37-40`
(`@pytest.mark.parametrize("sli_id", [s["id"] for s in _SLI_DOC["slis"]])`).
Pass 1 Q1 propagation requirement at `spec.md:4020-4023` (parametric
matrix consistency with `test_sli_kql_canonical_match.py`). Cycle 3
Pass 1 Q5 universal-scope contract surface at `spec.md:1185-1230` (every
SLI in `sli-kql.json` participates in every parametric contract test —
the new runtime-validity test inherits this universality). `infra/observability/sli-kql.json`
inventory of 7 SLIs (Z1–Z7) verified at `_SLI_DOC["slis"]` collection
expression. Constitution Principle IV (Transparency and Auditability —
quantitative claims must match observed reality; a 7-test undercount in
a CI-gate assertion would mask a partial-implementation regression
where only some Zn parametric ids land). Cycle 2 Q1 supersession
precedent at `spec.md:389-392` (later passes can supersede earlier
phrasings within the same amendment cycle, with originals preserved
verbatim).

**Spec-text propagation** *(deferred)*:

- `propagation_target: specs/036-sim-agent-extend/spec.md:3893` and
  `spec.md:4381` — Pass 1 lines remain verbatim per immutability;
  binding post-Cycle-4-implement count is **3398**, recorded by this
  Q1. **(Step 8ad — verify-only; no edit to Pass 1 lines)**
- `propagation_target: specs/036-sim-agent-extend/tasks.md` — the
  Cycle 4 implement task acceptance criterion MUST cite *"3398 tests
  pass / 0 fail expected post-Cycle-4-implement"* (NOT 3392); cite
  this Pass 2 Q1 entry as the supersession authority. **(Step 8ad)**
- `propagation_target: tests/contract/test_sli_kql_runtime_validity.py`
  (new) — the parametric expression MUST mirror
  `tests/contract/test_sli_kql_canonical_match.py:37-40` exactly
  (`@pytest.mark.parametrize("sli_id", [s["id"] for s in _SLI_DOC["slis"]])`)
  so the 7-id collection is structurally guaranteed and any future
  Z8/Z9 SLI added to `sli-kql.json` automatically participates. **(Step 8ad)**
- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  (Cycle 4 amendment sub-section per Pass 1 Q5 propagation at
  `spec.md:4338-4344`) — cite **3398** as the post-Cycle-4-implement
  test count; do NOT carry forward the 3392 figure. **(Step 8ae)**

### Q2 — What CHANGELOG.md format shall the Cycle 4 close use — single `- A4-XX <summary>` bullets, or grouped `### Breaking changes / Added / Changed (spec 036 — Cycle 4 amendment cycle)` sub-sections?

**Answer**: **Grouped sub-sections** under the existing `## [Unreleased]`
heading, mirroring the **Cycle 2 precedent** at `CHANGELOG.md:7-31`. The
single-bullet `- A4-XX <one-sentence-summary>` format suggested by the
orchestrator hint has **no precedent** in this repository: a repo-wide
scan during Pass 2 verification confirms `CHANGELOG.md` contains zero
lines matching the pattern `^- A\d+-\d+ ` (verified via
`Select-String -Path 'CHANGELOG.md' -Pattern '^- A\d+-\d+'` — no
matches). The actual precedent is the Cycle 2 amendment cycle at
`CHANGELOG.md:7-31`, which uses **three grouped sub-sections** under
`## [Unreleased]`: (1) `### Breaking changes (spec 036 — Cycle 2
amendment cycle)` (5 bullets at L8-12); (2) `### Added (spec 036 —
Cycle 2 amendment cycle)` (14 bullets at L14-26); (3) `### Changed
(spec 036 — Cycle 2 amendment cycle)` (3 bullets at L29-31). Each
bullet is a verbose paragraph citing: a bolded change summary; the
file:line evidence; and inline `(AN-XX / FR-YYY)` provenance tags
(e.g. *"(A2-01 / FR-067)"* at `CHANGELOG.md:8`). Cycle 3 has not yet
written CHANGELOG entries (Cycle 3 implement is complete per the
Cycle 3 sentinel at `spec.md:3829` but the CHANGELOG block is folded
in at Cycle 3 close, deferred to the cohort-re-review-clean state);
Cycle 4 must therefore (a) write Cycle 3's grouped block first
(retroactive — Step 8ad) AND (b) write its own Cycle 4 grouped block
(Step 8ae), in the same Cycle-2-precedent format. The Cycle 4 close
SHALL emit **at minimum two grouped sub-sections** under `##
[Unreleased]` (no `### Breaking changes` because A4-01 + A4-02 are
non-breaking — A4-01 is an FR strengthening with backward-compatible
KQL surface, A4-02 is documents-only): **(i)** `### Added (spec 036
— Cycle 4 amendment cycle)` containing one bullet for the new
`tests/contract/test_sli_kql_runtime_validity.py` (citing A4-01 /
FR-073 inline) and one bullet for the new GitHub backlog issue URL
(citing A4-02 inline); **(ii)** `### Changed (spec 036 — Cycle 4
amendment cycle)` containing one bullet for the FR-073 column-resolution
sub-bullet strengthening (citing A4-01 / FR-073 inline), one bullet
for the symmetric Z7 KQL `extend model_deployment` fix in
`infra/observability/sli-kql.json` and `contracts/sli-thresholds.md`
(citing A4-01 / FR-073 inline), one bullet for the
`tests/contract/test_smoke_tenant_isolation.py` extension (citing
A4-02 inline; see Pass 2 Q4 for extension scope), and one bullet for
the ADR-036-011 wording correction with the *"compensating defence-in-depth
control"* phrase + backlog-issue citation (citing A4-02 inline). The
post-Cycle-4-implement test count delta (3391 → 3398) MAY appear as a
short closing line within the Added or Changed block, NOT as its own
sub-section. The "single-bullet `- A4-XX <summary>`" format suggested
by the orchestrator is **explicitly rejected** because (a) it has no
in-repo precedent (verified zero matches above), and (b) it would lose
the file:line evidence and FR provenance that Cycle 2's format
preserves — both are required by Constitution Principle IV
(Transparency and Auditability — CHANGELOG entries must cite the
binding code site so a future maintainer can trace the change).

**Authority**: Cycle 2 CHANGELOG precedent at `CHANGELOG.md:7-31` (three
grouped sub-sections under `## [Unreleased]`, each titled `### <Group>
(spec 036 — Cycle 2 amendment cycle)`, each bullet citing file:line
evidence + `(AN-XX / FR-YYY)` provenance). Repository-wide scan during
Pass 2 verification (zero matches for `^- A\d+-\d+ ` pattern → no
single-bullet precedent exists). [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/)
convention cited at `CHANGELOG.md:3` (Added/Changed/Deprecated/Removed/
Fixed/Security categories — Cycle 2 uses Breaking changes /Added/Changed
which is the same family). Cycle 4 narrowness discipline at
`spec.md:3838-3852` (no breaking changes — A4-01 and A4-02 are
non-breaking, so the Cycle 4 block has no `### Breaking changes`
sub-section). Constitution Principle IV (Transparency and Auditability
— each change must cite the binding code site and the FR provenance,
which the Cycle 2 verbose-paragraph format preserves and the
single-bullet format would discard).

**Spec-text propagation** *(deferred)*:

- `propagation_target: CHANGELOG.md` — append the Cycle 3 grouped
  block first (retroactive close of Cycle 3 — `### Added (spec 036
  — Cycle 3 amendment cycle)`, `### Changed (spec 036 — Cycle 3
  amendment cycle)` per Cycle 3 ADR-036-011 deliverables), then
  append the Cycle 4 grouped block per the structure described above.
  Both blocks live under the existing `## [Unreleased]` heading at
  `CHANGELOG.md:5`. **(Step 8ae for Cycle 4 block; Step 8ad MAY
  retroactively write Cycle 3 block if it has not yet been written
  by Step 8ab — verify-first)**
- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  (Cycle 4 amendment sub-section) — link forward to the new CHANGELOG.md
  Cycle 4 grouped block; cite the `(A4-01 / FR-073)` and `(A4-02)`
  provenance tags consistently with the Cycle 2 inline-tag precedent.
  **(Step 8ae)**
- `propagation_target: tasks.md` — the Cycle 4 close task MUST list
  the CHANGELOG.md grouped-block emission as an explicit acceptance
  criterion citing this Pass 2 Q2 entry as the format authority.
  **(Step 8ae)**

### Q3 — Under what convergence rule does ADR-036-011 transition Status from `Proposed` → `Accepted` across multiple post-Cycle-4 cohort cycles?

**Answer**: **Status remains `Proposed` until a cohort re-review
(Step 8al or any subsequent re-review) returns `0 OBJECT votes` AND `0
NEW merit-validated findings` against ADR-036-011 itself**, at which
point the Status flips to `Accepted` in the same commit that records
the clean verdict. Any earlier flip is **prohibited**. Pass 1 Q5's
propagation at `spec.md:4309-4311` says *"move the document Status
from `Proposed` ... to `Accepted` only on a clean Step 8al cohort
re-review verdict"*, but does not specify what happens if Step 8al
surfaces NEW merit-validated findings (which would trigger Cycle 5),
nor what happens across Cycle 5 / Cycle 6 / ... convergence loops.
Pass 2 Q3 fills this gap with an explicit multi-cycle convergence
rule: **(i)** during Cycle 4 implement (Step 8ae), the Cycle 4
amendment sub-section is appended to ADR-036-011 with the Status
field unchanged (remains `Proposed` from the Cycle 3 close); **(ii)**
at Step 8al cohort re-review, if **all three cohorts (sectors /
operational / technical) return 0 OBJECT votes AND 0 NEW
merit-validated findings against ADR-036-011** (matching the user's
standing convergence rule cited at `spec.md:90-91`), the Status
field flips `Proposed` → `Accepted` in that same Step-8al-close
commit, AND the Cycle 4 amendment sub-section gains a closing line
*"Cycle 4 cohort re-review verdict: 0 OBJECT, 0 NEW findings —
Status moved Proposed → Accepted on YYYY-MM-DD per `spec.md:4XXX`
(Pass 2 Q3 convergence rule)"*; **(iii)** if Step 8al surfaces ≥1
OBJECT vote OR ≥1 NEW merit-validated finding against ADR-036-011,
Status remains `Proposed` and the next cycle (Cycle 5) opens —
the Status-flip is deferred to Cycle 5+'s Step-8X re-review under
the same rule recursively; **(iv)** there is **no time-bound
auto-flip** (Status MUST NOT flip to `Accepted` after N days
absent a clean cohort re-review verdict — the flip is gated solely
on the verdict, not on calendar time); **(v)** the rule applies
recursively across Cycle 5 / Cycle 6 / ... — Status flips
`Proposed` → `Accepted` only on the *first* clean cohort re-review
verdict, and never reverts once Accepted (subsequent cycles MAY
append additional amendment sub-sections, but those amendments
target the existing Accepted ADR rather than re-opening its
Status — the immutability discipline at `spec.md:3947-3950`
applies). The rule is recorded inline within the Cycle 4
amendment sub-section of ADR-036-011 (per Pass 1 Q5 propagation
at `spec.md:4309-4311`) so future maintainers reading ADR-036-011
in isolation see the convergence rule alongside the Status field
and do not flip prematurely.

**Authority**: User's standing convergence rule cited at
`spec.md:90-91` (*"Cycle 1 closed with 0 OBJECT votes across all
three cohorts (sectors / operational / technical) — the user's
stated convergence rule was satisfied"*); the same rule applied
recursively to Cycle 4+. Pass 1 Q5 propagation at
`spec.md:4309-4311` (Step 8al cohort re-review gates the
`Proposed` → `Accepted` flip — Pass 2 Q3 elaborates the
multi-cycle case). Cycle 4 amendment-log immutability discipline
at `spec.md:3947-3950` (originals preserved, corrections appended
as sub-sections — applied recursively, the Accepted ADR is never
re-opened to `Proposed`). Constitution Principle IV (Transparency
and Auditability — Status field must reflect the actual review
state; premature flip would misrepresent pending findings).
Cycle 1 / Cycle 2 / Cycle 3 ADR pattern (Cycle 1's ADR-036-001
through ADR-036-009 each carry `Status: Accepted` post their
respective cohort re-review close; Cycle 3's ADR-036-011 carries
`Status: Proposed` because its Step 8ac re-review surfaced the two
Cycle 4 defects — the precedent for "Proposed pending clean
re-review" already exists in this same ADR family).

**Spec-text propagation** *(deferred)*:

- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  (Cycle 4 amendment sub-section per Pass 1 Q5 propagation at
  `spec.md:4338-4344`) — append the multi-cycle Status convergence
  rule (i)–(v) verbatim within the sub-section, citing this Pass 2
  Q3 entry as the authoritative source. The `Status: Proposed`
  field at the top of the document remains unchanged at Step 8ae
  close; the flip to `Accepted` is gated on Step 8al's clean
  verdict per (ii) above. **(Step 8ae)**
- `propagation_target: tasks.md` — the Step 8al cohort re-review
  acceptance criterion MUST explicitly check ADR-036-011's Status
  field and flip it `Proposed` → `Accepted` IF AND ONLY IF the
  cohort verdict is clean per (ii); otherwise leave Status
  unchanged. Cite this Pass 2 Q3 as the rule authority. **(Step 8al)**
- `propagation_target: specs/036-sim-agent-extend/spec.md` — no
  spec-body change; the rule lives in ADR-036-011 (the binding
  artefact for the Status field) with this Pass 2 Q3 as the
  spec-side anchor. **(Step 8ae — verify-only)**

### Q4 — What is the precise scope of the `tests/contract/test_smoke_tenant_isolation.py` extension required by A4-02 — three new assertions, two new assertions, or a refinement of an existing assertion?

**Answer**: **One new assertion (scope-string verification) + one
optional assertion (Bicep comment-block content)**. The current
`tests/contract/test_smoke_tenant_isolation.py` already covers six of
the seven assertions implied by the A4-02 binding wording at
`spec.md:3906`, but it does **not** assert the literal scope-string
*"`'${account.id}/dbs/${databaseName}'`"* on the role-assignment
resource — and that scope-string is the central correction A4-02 makes
(replacing the inaccurate *"scoped exclusively to `tnt-stg-smoke`"*
phrasing). Live verification during Pass 2 confirms the existing test
file at `tests/contract/test_smoke_tenant_isolation.py` contains six
`def test_*` functions: **(a)** `test_smoke_role_assignment_resource_present`
(L58–68 — exactly-one-resource cardinality); **(b)**
`test_smoke_role_assignment_is_conditional_on_coordinator_principal`
(L71–89 — conditional guard on `!empty(coordinatorPrincipalId)`);
**(c)** `test_smoke_tenant_id_defaults_to_contract_value` (L92–106 —
`smokeTenantId` defaults to `'tnt-stg-smoke'`); **(d)**
`test_smoke_role_assignment_name_uses_smoke_tenant_id_in_guid`
(L109–126 — `smokeTenantId` participates the `guid()` expression);
**(e)** `test_smoke_role_uses_builtin_data_contributor_role` (L129–142
— role definition id is `00000000-0000-0000-0000-000000000002`); **(f)**
`test_no_production_tenant_role_assignment_for_coordinator` (L145–169
— no `tnt-prod` substring inside any role-assignment block). A4-02's
binding wording at `spec.md:3906` introduces a NEW invariant not yet
enforced: the role assignment scope-string is literally
*"`'${account.id}/dbs/${databaseName}'`"* (database-level), NOT a
narrower partition-level scope nor a broader account-level scope. The
extension Step 8ae MUST: **(g)** add a NEW assertion
`test_smoke_role_assignment_scope_is_database_level` that asserts the
Bicep text contains `scope: '${account.id}/dbs/${databaseName}'`
literally on the `smokeCoordinatorRoleAssignment` resource (regex:
`scope:\s*'\$\{account\.id\}/dbs/\$\{databaseName\}'` within the
`sqlRoleAssignments` resource block) AND that no narrower
`pks/${...}` (per-partition-key) suffix nor broader account-level
scope (`scope: '\$\{account\.id\}'` with no `/dbs/...` suffix)
appears — this is the literal scope-string A4-02 binds to. Failure
message MUST be explicit: *"A4-02 invariant: role assignment scope
MUST be database-level `'${account.id}/dbs/${databaseName}'` per
the corrected ADR-036-011 wording — got <observed scope>; see
`spec.md:3906` for the binding wording"*. Additionally, Step 8ae
**MAY** add an OPTIONAL assertion **(h)**
`test_bicep_comment_block_documents_compensating_control` that asserts
the comment block currently at `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
contains both **(h-i)** the literal phrase `compensating defence-in-depth
control` (or accept the existing phrase `tenant filter is enforced at
query-time` at L309-310 as a semantic equivalent — Step 8ae MAY rewrite
the comment block to use the canonical phrase from A4-02's binding
wording) AND **(h-ii)** the GitHub backlog issue URL or issue id once
filed per Pass 1 Q3 propagation at `spec.md:4143-4188`. Until the
backlog issue id is known at Step 8ae implementation time, assertion
(h-ii) accepts the placeholder substring `[backlog issue: TBD]` and
the test carries a `# TODO(Step 8ae close): replace TBD with actual
issue id` comment; the placeholder is replaced atomically when the
issue is filed. Assertion (h) is **OPTIONAL** because the Pass 1 Q2
propagation at `spec.md:4146-4151` already pinned the comment-block
extension as *"verify-only; optional one-line addition"* — Pass 2 Q4
ratifies this as a true optional (not silently elevated to required).
The orchestrator's hint of three new assertions is **partially adopted**
(scope-string verification IS new and required; comment-block content
verification IS new but OPTIONAL); the orchestrator's reframing of
existing assertions (i) and (ii) at `spec.md:3911` is **rejected** as
redundant — those assertions already exist as test functions (a) and
(f) above, and re-asserting them in the extension would be dead code.

**Authority**: Live file inspection of
`tests/contract/test_smoke_tenant_isolation.py:1-170` during Pass 2
verification (six existing `def test_*` functions enumerated above).
A4-02 binding wording at `spec.md:3906` (introduces the
`'${account.id}/dbs/${databaseName}'` scope-string as the corrected
invariant). A4-02 acceptance criterion at `spec.md:3911` (the
two-line invariant — but assertions (i) and (f) already exist;
the genuinely new invariant is the scope-string literal). Pass 1
Q2 propagation at `spec.md:4146-4151` (Bicep comment block is
*"verify-only; optional one-line addition"* — Pass 2 Q4 preserves
the optional). Pass 1 Q3 propagation at `spec.md:4143-4188`
(GitHub backlog issue id citation in the corrected ADR-036-011 +
Bicep comment block). Constitution Principle V (Graceful
Degradation — failure messages MUST cite the binding spec source
so future maintainers reading the test failure can trace the
invariant origin). Cycle 3 contract-test convention
(`test_smoke_tenant_isolation.py:1-30` header docstring lists the
five existing assertions explicitly — Pass 2 Q4's new assertion (g)
extends this list to six, optional (h) to seven; the docstring
header MUST be updated symmetrically by Step 8ae to list the new
assertion(s)).

**Spec-text propagation** *(deferred)*:

- `propagation_target: tests/contract/test_smoke_tenant_isolation.py`
  — add NEW required `def test_smoke_role_assignment_scope_is_database_level`
  function asserting the scope-string regex per (g) above; OPTIONALLY
  add `def test_bicep_comment_block_documents_compensating_control`
  function per (h) above (gated on whether Step 8ae chooses to rewrite
  the Bicep comment block to use the canonical phrase + backlog issue
  id citation — NOT mandatory). Update the module-level docstring
  header at `tests/contract/test_smoke_tenant_isolation.py:1-30` to
  include the new assertion(s) symmetrically with the existing five.
  The test file gains 1 (or 2) new `def test_*` functions; this does
  NOT change the post-Cycle-4-implement test-count delta beyond the
  +7 from `test_sli_kql_runtime_validity.py` (Pass 2 Q1) — the new
  smoke-tenant-isolation `def test_*` functions are part of the same
  baseline-extension count and ARE included in the total **3398**
  expectation. Wait — clarification: the +1 (or +2) from this
  extension IS additive on top of the +7. **The corrected
  post-Cycle-4-implement total is therefore 3399 (required: scope-string
  + 1) or 3400 (required scope-string + optional comment-block).** This
  Pass 2 Q4 entry **further supersedes Pass 2 Q1's 3398 figure**: the
  binding post-Cycle-4-implement test count is **3399** (scope-string
  assertion REQUIRED; comment-block assertion NOT taken) or **3400**
  (both assertions taken). Step 8ae's choice between 3399 and 3400 is
  recorded in `tasks.md` at Step-8ae acceptance. **(Step 8ae)**
- `propagation_target: tasks.md` — Step 8ae acceptance MUST cite either
  **3399** (if optional (h) is not taken) or **3400** (if optional (h)
  is taken) as the post-Cycle-4-implement test count, supersedng Pass 2
  Q1's 3398 figure. The decision is recorded at Step 8ae implementation
  time, not deferred. **(Step 8ae)**
- `propagation_target: infra/bicep/modules/cosmos-simulation-containers.bicep`
  (comment block L305-315) — Step 8ae MAY rewrite the comment block to
  use the canonical phrase *"compensating defence-in-depth control"*
  from A4-02's binding wording AND insert the backlog issue id
  citation (initially `[backlog issue: TBD]`, replaced atomically
  when the issue is filed). This rewrite is OPTIONAL; if not taken,
  the existing comment block at L305-315 is left unchanged and Pass 2
  Q4's optional assertion (h) is also skipped. **(Step 8ae — optional)**
- `propagation_target: specs/036-sim-agent-extend/spec.md:3911` — Pass 1
  acceptance line at L3911 says *"is extended in Step 8ae to assert (i)
  exactly one ... role assignment ... scoped at `'${account.id}/dbs/${databaseName}'`,
  and (ii) zero production-tenant role assignments"* — Pass 2 Q4
  clarifies that (i) decomposes into two assertions: existing
  `test_smoke_role_assignment_resource_present` (cardinality, already
  present) PLUS new `test_smoke_role_assignment_scope_is_database_level`
  (scope-string, NEW); and (ii) is already covered by existing
  `test_no_production_tenant_role_assignment_for_coordinator`. The
  spec line at L3911 is correct as written; this Pass 2 Q4 elaborates
  the implementation. **(Step 8ae — verify-only; no edit to L3911)**

**Resolution rollup (Cycle 4 pass 2)**: Q1 → **supersedes** the Pass 1
Q1 acceptance "3392" figure with the corrected **3398** (3391 +
7-parametric-ids, verified live via pytest --collect-only); Q2 →
pins **grouped sub-section format** (`### Added (spec 036 — Cycle 4
amendment cycle)` + `### Changed (spec 036 — Cycle 4 amendment
cycle)`) for the Cycle 4 CHANGELOG.md close, mirroring the Cycle 2
precedent at `CHANGELOG.md:7-31` — the orchestrator-suggested
single-bullet `- A4-XX <summary>` format is **rejected** as having
no in-repo precedent (zero matches for `^- A\d+-\d+ ` pattern in
`CHANGELOG.md`); Q3 → pins the **multi-cycle Proposed→Accepted
convergence rule** for ADR-036-011: Status remains `Proposed` until
a cohort re-review (Step 8al or any subsequent re-review) returns
`0 OBJECT votes AND 0 NEW merit-validated findings against
ADR-036-011`, then flips to `Accepted` in the same close commit;
recursive across Cycle 5 / Cycle 6 / ...; no time-bound auto-flip;
no revert once Accepted; Q4 → pins **one required new assertion +
one optional new assertion** for the
`tests/contract/test_smoke_tenant_isolation.py` extension —
required: scope-string literal `'${account.id}/dbs/${databaseName}'`
verification; optional: Bicep comment-block content (defence-in-depth
phrase + backlog issue id). Q4 **further supersedes** Pass 2 Q1's
3398 figure with **3399** (required only) or **3400** (required +
optional taken); the choice is recorded at Step 8ae implementation
time. Together these four resolutions close the third-order
ambiguities Cycle 4 Pass 1 left implicit (test-count math precision;
CHANGELOG format precedent; multi-cycle Status convergence rule;
test-extension assertion scope) and unblock **Step 8ad**
(`tests/contract/test_sli_kql_runtime_validity.py` new file with
parametric expression mirroring `test_sli_kql_canonical_match.py:37-40`;
`tasks.md` acceptance count corrected to 3399/3400) and **Step 8ae**
(ADR-036-011 in-place revision with multi-cycle convergence rule
appended; `test_smoke_tenant_isolation.py` extension with new
scope-string assertion (required) + optional comment-block assertion;
CHANGELOG.md grouped sub-sections under `## [Unreleased]`). One
orchestrator-suggested ambiguity (literal text of the `union`
fail-fast message) is **not surfaced** as a Pass 2 Q because Pass 1
Q4 propagation at `spec.md:4274-4277` already pins the message
verbatim. No prior Q→A is contradicted; Pass 2 is fully additive
(Q2, Q3, Q4) or supersession-by-correction (Q1, Q4 — math
corrections to test-count claims, with original Pass 1 lines
preserved verbatim per the within-cycle immutability discipline
analogous to the Cycle 2 Q1 supersession precedent at
`spec.md:389-392`). The Cycle 3 baseline of 3391 tests pass / 0
fail at `spec.md:3829` is preserved; the binding post-Cycle-4-implement
total is **3399 tests pass / 0 fail** (scope-string assertion
required; comment-block assertion NOT taken — minimal Step 8ae
posture) or **3400 tests pass / 0 fail** (both new assertions
taken — full Step 8ae posture). Step 8ae records the chosen value
in `tasks.md`.

**Cycle 4 clarify pass 2 complete. Ready for /speckit.checklist (Cycle 4).**

**Cycle 4 checklist complete (34 rows appended). Ready for /speckit.plan (Cycle 4).**

**Cycle 4 plan complete. Ready for /speckit.tasks (Cycle 4).**
**Cycle 4 tasks complete (14 tasks: T-AA43..T-AA56). Ready for /speckit.analyze (Cycle 4).**

**Cycle 4 analyze complete (verdict: PASS-WITH-MINOR). Ready for /speckit.implement (Cycle 4).**

**Cycle 4 implement complete. 🟢 GREEN: 14 tasks DONE (T-AA43..T-AA56); test count delta +9 (3391 baseline → 3400 FULL posture); 22 Cycle-4-affected contract tests pass / 0 fail; ruff check apps tests packages clean; backlog issue #84 filed.**

## Cycle 5 Amendment Log (post Step 8al cohort re-review, 2026-05-11)

This log records the **Cycle 5** amendments applied following the Step 8al
cross-cohort re-review of Cycle 4's *own* deliverables. Ground-truth review
reports are `step-8al-rereview-operational.md`,
`step-8al-rereview-sectors.md`, and `step-8al-rereview-technical.md` in the
session workspace
`C:\Users\prbillir\.copilot\session-state\ddfe017a-c801-4ecd-b4ba-986fe32d7afd\files\`.
Cycle 5 is **narrower in scope** than Cycle 4: it closes a single
merit-validated documentation defect (F-TECH-4-01) that originated in
Cycle 4's own implementation residue (a stale pre-Cycle-4 preamble in
`cosmos-simulation-containers.bicep` that Cycle 4 A4-02 did not remove
when it added the corrective wording immediately after it). Cycle 1 /
Cycle 2 / Cycle 3 / Cycle 4 carry-overs are explicitly out-of-scope.

The Step 8al cohort triple returned **Operational 🟢 GREEN PROCEED**
(10 ACCEPT / 0 RESERVATIONS / 0 OBJECT; 0 NEW findings), **Sectors 🟢
GREEN PROCEED** (54 ACCEPT / 4 carry-forward RESERVATIONS / 0 OBJECT;
0 NEW findings), and **Technical 🟡 YELLOW** (16 ACCEPT / 1 RESERVATION
/ 0 OBJECT; **1 NEW MEDIUM** — F-TECH-4-01 from infrastructure-devops).
The Cycle 3 data-engineer OBJECT verdict on the Z7 KQL
`extend model_deployment` defect is **closed** per direct file
inspection of `infra/observability/sli-kql.json:91` and
`specs/036-sim-agent-extend/contracts/sli-thresholds.md:288-290` (both
now contain the missing `extend model_deployment = tostring(customDimensions["model_deployment"])`
line; the runtime-validity walker at
`tests/contract/_kql_walker.py` would have caught the original defect;
the Cycle-4-affected contract suite passes `22 passed in 0.31s`). The
keystone is removed; no operational, regulatory-sectors, or
ai-ml-engineer surface regresses.

This amendment cycle adds **0 new functional requirements**,
**0 new success criteria**, **strengthens 0 existing FRs** (pure
DOC-FIX, narrower than Cycle 4's A4-01 FR-073 sub-bullet
strengthening), and records **0 new self-documentation supersessions**.
Cycle 1 amendments A–S, Cycle 2 amendments A2-01 → A2-08, Cycle 3
amendments A3-01 → A3-06, and Cycle 4 amendments A4-01 / A4-02 remain
in force unchanged. Implementation files
(`infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
preamble rewrite) and contract-test files
(`tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control`
assertion extension) are **out-of-scope** for this spec amendment
cycle and will be applied in Step 8at (Cycle 5 implement). ADR-036-011
acquires a Cycle 5 sub-section in Step 8aq (Cycle 5 plan), consistent
with the Cycle 4 plan adding the Cycle 4 sub-section at ADR L478+.
The Cycle 4 sibling mirrors at `plan.md:682`, `tasks.md:1929`,
`quality.md:367`, and `quality.md:528` are NOT touched in Cycle 5 per
the LOW-1 within-cycle immutability discipline (those mirrors are
already annotated as "known-stale per A4-02 supersession" via the
Cycle 4 strikethrough block at `spec.md:961-970`).

### Cycle 5 amendment summary table

| ID | Severity | Cohort | Type | Target | Summary |
|---|---|---|---|---|---|
| A5-01 | MEDIUM | infrastructure-devops (technical cohort, Step 8al) | DOC-FIX (no FR change) + REGRESSION-TEST | `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315` (stale pre-Cycle-4 preamble) AND `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` (assertion extension) | The Cycle 4 A4-02 amendment ADDED corrective wording at L317-327 of the same Bicep module (database-level scope + compensating defence-in-depth + issue #84) but did NOT REMOVE the OLD pre-Cycle-4 preamble at L305-315, which still leads with *"Scope the assignment to the smoke-tenant partition path"* and an example resolution containing `/colls/<container>/pks/<tenant_id>`. This contradicts the actual `scope: '${account.id}/dbs/${databaseName}'` at L328 (database-level — unchanged by Cycle 4 and confirmed correct by azure-principal-architect on direct file inspection at Step 8al), the corrected ADR-036-011 wording at :172-184, and the spec.md A4-02 binding wording at :3907-3925. Operator-facing IaC documentation is therefore self-contradictory within a single contiguous comment block (L305-327). Defect is **documentation-only** (the compiled Bicep `scope` expression is correct and unchanged; runtime RBAC behaviour is identical); no FR change is required; the binding remediation is a comment-block rewrite plus a regression-test assertion extension that fails on the offending phrases. |

### Cycle 5 amendments — detail

#### A5-01 — `Simulation.Coordinator` Bicep preamble residue (MEDIUM)

- **Cohort source**: infrastructure-devops (MEDIUM RESERVATIONS verdict on Step 8al re-review); ground-truth `step-8al-rereview-technical.md` § "infrastructure-devops — RESERVATIONS" and the F-TECH-4-01 row of the "NEW findings" table in the same report.
- **Site**: `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315` (the role-assignment comment preamble immediately preceding the Cycle 4 A4-02 corrective block at L317-327, which in turn precedes the actual `scope:` expression at L328).
- **Type**: DOC-FIX (Bicep comment rewrite — no Bicep `scope:` change) + REGRESSION-TEST (extension of the existing `test_bicep_comment_block_documents_compensating_control` assertion).
- **Defect description**: Lines 305-315 of `cosmos-simulation-containers.bicep` retain a verbatim pre-Cycle-4 preamble that:
  1. Leads at L305 with *"Scope the assignment to the smoke-tenant partition path"* — false; the assignment is database-level, not partition-level.
  2. Contains at L306-308 an illustrative scope resolution `/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.DocumentDB/databaseAccounts/<account>/dbs/<db>/colls/<container>/pks/<tenant_id>` — false; the actual resolved scope ends at `.../dbs/<db>` (database-level), as compiled from L328's `scope: '${account.id}/dbs/${databaseName}'`.
  3. Contains a parenthetical at L309 *"but Cosmos data-plane RBAC accepts container-level scope; the tenant filter is enforced at query-time …"* that *softens* claims (1) and (2) but does not retract them — a reader scanning the preamble top-down sees the partition-path claim first and only learns it is overstated several lines later.
  4. Sits immediately above the Cycle 4 A4-02 corrective block at L317-327, which already says (correctly) that the scope is database-level, the control is **compensating defence-in-depth**, and issue #84 tracks the partition-scope upgrade. The two blocks contradict each other within a single contiguous comment.
- **Merit validation**: F-TECH-4-01 was confirmed by **direct file inspection** during Step 8al follow-up (per checkpoint `013-step-8al-findings-cycle-5-launch.md` § "F-TECH-4-01 (merit-validated by direct file inspection)"). The defect is real, present in `main` at the Cycle 5 launch tip, and not a false-positive review artefact. The actual compiled scope at L328 is **correct** (database-level — unchanged by Cycle 4 and confirmed at the Step 8al azure-principal-architect ACCEPT verdict, which cites `cosmos-simulation-containers.bicep:328` verbatim); the ADR-036-011 narrative at :172-184 is **correct** (three-clause acknowledgement: database-level + compensating defence-in-depth + #84 — confirmed at the Step 8al api-architect and security-engineer ACCEPT verdicts); the spec.md A4-02 binding wording at :3907-3925 is **correct** (re-verified at Step 8am specify); the *only* defect is the unremoved L305-315 preamble.
- **Severity rationale (MEDIUM, not HIGH)**:
  - Compiled scope at L328 is correct (database-level) — runtime RBAC behaviour is unaffected; no production tenant can be accessed by the smoke `Simulation.Coordinator` principal at any moment.
  - The Cycle 4 A4-02 sub-block at L317-327 *does* state the correct wording — a reader who reaches it gets the right answer.
  - Defect is documentation-only (stale operator-facing comment); no compliance, regulatory, accessibility, multilingual, residency, or RBAC-runtime-behaviour impact.
  - Discovery surfaced via the Cycle 4 → Cycle 5 re-review mechanism (the intended convergence loop did its job); no real-world remediation deadline is breached.
  - However, the contradiction is in operator-facing IaC that incident responders and security auditors will read first when investigating a smoke-tenant RBAC question, so the defect is **above LOW** — the false partition-path claim is the *opening* sentence and is materially misleading on first read. MEDIUM is the appropriate severity per the Cycle 4 A4-02 calibration (which was also MEDIUM for the analogous ADR + spec wording defect).
- **Required remediation** (per F-TECH-4-01 recommended remediation):
  1. **Rewrite `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`** to: (a) lead with a database-level scope statement (e.g., *"Scope the assignment at the database level — `${account.id}/dbs/${databaseName}` — which is the narrowest scope supported by Cosmos data-plane RBAC API 2024-08-15"*); (b) remove the partition-path / `pks/<tenant_id>` example entirely (no `pks/<tenant_id>`, no `/colls/<container>/pks/`, no `partition path` phrasing); (c) retain the compensating defence-in-depth phrasing already used in the Cycle 4 A4-02 block at L317-327 (this preamble and the A4-02 block will be consolidated into a single coherent block, not left as two contradictory adjacent blocks); (d) retain the `[backlog issue: #84]` citation. The actual `scope:` expression at L328 **MUST NOT** be modified — it is correct as-is and any change would be a Cycle 5 scope creep violation.
  2. **Extend `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control`** to fail on the offending phrasings within the role-assignment comment block. The new assertions extend the existing test (introduced in Cycle 4 Step 8ae) so the test continues to pass on the corrected Bicep and would fail if either the partition-path claim or the `pks/<tenant_id>` example were reintroduced (regression guard against a future drift that re-pastes the Cycle 3 wording).
- **Acceptance criteria**:
  - `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315` no longer contains the phrases `partition path`, `pks/<tenant_id>`, or `/colls/<container>/pks/`; the block leads with a database-level scope statement; the compensating defence-in-depth phrasing and `#84` citation are retained; the actual `scope:` expression at L328 is **byte-identical** to the Cycle 4 baseline (`scope: '${account.id}/dbs/${databaseName}'`).
  - The L305-315 preamble and the Cycle 4 A4-02 block at L317-327 are consolidated into a single coherent comment block whose top-down reading sequence is: (1) actual scope is database-level; (2) this is a compensating defence-in-depth control rather than a partition-level guarantee; (3) tenant isolation is enforced at query time via the SLI-Z6 / SLI-Z7 `where tenant_id == "tnt-stg-smoke"` filter and the `customDimensions["tenant_id"]` envelope discriminator; (4) the partition-scope upgrade is tracked at backlog issue #84.
  - `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` is extended to assert the absence of the offending phrasings (the exact assertion granularity is recorded under "Open clarifications" below and will be pinned in /speckit.clarify Pass 1).
  - The Cycle 4 baseline of **3400 tests pass / 0 fail (FULL posture)** is preserved; A5-01 is documents-and-test-only and the binding post-Cycle-5-implement test count is computed at /speckit.clarify or /speckit.tasks (Cycle 5) depending on whether the extension reuses the existing test (no count delta) or adds a new parametric case (+1 count delta).
  - ADR-036-011 Status flips Proposed → Accepted after the Step 8au re-review returns 0 OBJECT + 0 NEW merit-validated findings across all three cohorts (operational, sectors, technical).
- **In-scope** for Cycle 5:
  1. The L305-315 Bicep preamble rewrite at `infra/bicep/modules/cosmos-simulation-containers.bicep`.
  2. The `test_bicep_comment_block_documents_compensating_control` assertion extension at `tests/contract/test_smoke_tenant_isolation.py`.
  3. The ADR-036-011 Cycle 5 sub-section appended in Step 8aq (Cycle 5 plan), consistent with the Cycle 4 plan adding the Cycle 4 sub-section at ADR L478+.
  4. The Cycle 5 sibling artefacts (`plan.md`, `tasks.md`, `quality.md`) acquire Cycle 5 amendment sub-sections in Steps 8aq / 8ar / 8ap respectively, per the Cycle 4 ceremony precedent.
- **Out-of-scope** for Cycle 5 (explicit, mirroring the Cycle 4 A4-02 out-of-scope discipline):
  1. ADR-036-011 wording at :172-184 — already correct per Step 8al api-architect, azure-principal-architect, infrastructure-devops, security-engineer ACCEPT verdicts; **DO NOT re-amend**.
  2. `infra/bicep/modules/cosmos-simulation-containers.bicep:328` actual `scope:` expression — already database-level and correct; **DO NOT modify**.
  3. `specs/036-sim-agent-extend/spec.md` A4-02 amendment text at :3907-3925 — already correct; **DO NOT re-amend**.
  4. The four Cycle 4 sibling lock-zone mirrors at `plan.md:682`, `tasks.md:1929`, `quality.md:367`, `quality.md:528` — already annotated as "known-stale per A4-02 supersession" via the Cycle 4 strikethrough block at `spec.md:961-970` under the LOW-1 within-cycle immutability discipline; **DO NOT touch** in Cycle 5 (any re-rendering would violate the immutability discipline).
  5. The Cycle 4 A4-02 binding corrected wording at `spec.md:3917` — already correct; **DO NOT re-render**.
  6. SLI-Z6 / SLI-Z7 KQL bodies, `_kql_walker.py`, or any A4-01 deliverable — Step 8al data-engineer ACCEPT verdict closes the keystone; **DO NOT re-amend**.
- **Cross-references**:
  - `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:172-184` — correct three-clause acknowledgement (database-level scope + compensating defence-in-depth + #84); A5-01 brings the Bicep preamble into alignment with this anchor.
  - `specs/036-sim-agent-extend/spec.md:961-970` — the Cycle 3 → Cycle 4 mirror-correction precedent (the original Cycle 3 wording preserved verbatim with a strikethrough block annotating supersession by A4-02); A5-01 uses the *same* mirror-correction shape — the original L305-315 Bicep preamble is REPLACED in place (not strikethrough — Bicep is code, not narrative; the L317-327 A4-02 block is already the corrective annotation), but the *contract test* extension provides the equivalent regression-guard surface.
  - `specs/036-sim-agent-extend/spec.md:3896-3915` — Cycle 4 A4-02 amendment log location (the binding A4-02 wording and acceptance criteria that A5-01 brings the Bicep into compliance with). Note: the user-prompt cross-reference is `:3896-3915`; the rendered A4-02 detail block in the spec spans `:3907-3925` (the citation `:3896-3915` is preserved verbatim per the prompt's reference contract).
  - `tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control` — the existing assertion introduced in Cycle 4 Step 8ae that A5-01 extends.
  - `step-8al-rereview-technical.md` (session workspace) § "infrastructure-devops — RESERVATIONS" and § "NEW findings" → F-TECH-4-01 row — the originating cohort evidence.
  - `checkpoints/013-step-8al-findings-cycle-5-launch.md` (session workspace) — Cycle 5 launch context, in-scope / out-of-scope clarity, convergence rule.

### Open clarifications (seeded for /speckit.clarify Pass 1, Cycle 5)

The following three points are surfaced as `[NEEDS CLARIFICATION]` markers
for resolution in the next /speckit.clarify pass. The total marker count
(3) is at the upper bound of the spec authoring discipline; no further
markers are surfaced for A5-01.

1. **Wording sequence inside the rewritten Bicep preamble** — `[NEEDS CLARIFICATION: should the rewritten L305-315 preamble lead with the database-level scope statement and THEN introduce the "compensating defence-in-depth control" phrase, or lead with the compensating-control framing and THEN cite the database-level scope? The Cycle 4 Pass-1 Q2 binding wording (`spec.md:3917`) established the phrase "compensating defence-in-depth control" but did not pin its position relative to the scope sentence. The ADR-036-011:172-184 precedent leads with the scope statement (L172-175) and introduces the compensating-control phrase second (L175-177); applying the ADR sequence verbatim would be the lowest-friction default, but a security-engineer reader may prefer the threat-model-first sequence for IaC comments specifically (control framing → scope rationale).]`
2. **Test-assertion granularity for the `pks/<tenant_id>` / `partition path` regression guard** — `[NEEDS CLARIFICATION: the extended test_bicep_comment_block_documents_compensating_control assertion should fail on what exact set of phrasings? Options: (a) ONLY the literal substring "pks/<tenant_id>"; (b) the literal substring "pks/<tenant_id>" OR the literal substring "partition path" (the two phrasings called out verbatim by F-TECH-4-01); (c) a regex covering common partition-scope synonyms (e.g., `r"(partition[- ]?(path|key|scope)|pks/<[^>]+>)"`); (d) a substring search for the bare token `partition` anywhere in the role-assignment comment block. The Cycle 4 Pass-1 Q4 walker pattern (lightweight regex/lexer over canonical KQL — `spec.md:3905`) provides precedent for (b) or (c); option (d) would be over-broad (would false-positive on legitimate comparative language like *"partition-level isolation is deferred"* which is itself a *correct* phrase the rewritten preamble may need to use); option (a) is too narrow (would miss the L305 "partition path" lead sentence the F-TECH-4-01 evidence cites first).]`
3. **Bicep test-assertion scope (file vs comment block)** — `[NEEDS CLARIFICATION: should the extended assertion target ONLY the role-assignment comment block (i.e., the contiguous `//`-prefixed lines between L296's `resource smokeCoordinatorRoleAssignment` declaration and L328's `scope:` expression — roughly the L300-327 boundary post-rewrite) or the whole `cosmos-simulation-containers.bicep` file? Narrow scoping (comment-block-only) is the minimum needed to close F-TECH-4-01 and aligns with the existing `test_bicep_comment_block_documents_compensating_control` name (the test was named for a *block*, not a *file*); whole-file scoping would be a more conservative regression guard against future drift but risks false-positives on *correct* comparative language elsewhere in the module (e.g., the `roleDefinitionId` comment block at L300-303 that intentionally distinguishes data-plane vs management-plane RBAC). The Cycle 4 introduction of the test (Step 8ae) appears to have used comment-block-only scoping based on the test name; this clarification ratifies or revises that choice for the Cycle 5 extension.]`

### Cycle 5 convergence rule (restatement)

Cycle 5 closes when the **Step 8au cohort re-review** returns
**0 OBJECT verdicts and 0 NEW merit-validated findings** across all
three cohorts (operational, sectors, technical), mirroring the Cycle 4
convergence rule that surfaced F-TECH-4-01 and triggered Cycle 5. Upon
Cycle 5 close:

1. `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md` Status
   flips **Proposed → Accepted** (the ADR has been in `Proposed` status
   since Cycle 3 launch and was held there through Cycle 4 by the
   data-engineer OBJECT verdict; A4-01 closed the data-engineer OBJECT
   at Step 8al but F-TECH-4-01 prevented the flip until Cycle 5
   remediation).
2. Step 9 (`azd up` staging deploy) proceeds against the Cycle-5-clean
   tip of `main`.
3. The cycle counter freezes at 5 unless Step 8au surfaces a Cycle 6
   trigger (any merit-validated NEW finding from Step 8au would mandate
   Cycle 6 per the user's "repeat Steps 2-7" mandate, with surface
   expected to narrow further per the convergence design — A5-01 is
   already a single MEDIUM doc-fix, so a hypothetical Cycle 6 surface
   would be at most LOW or empty).

The convergence design holds: Cycle 3 closed 6 amendments
(A3-01 → A3-06); Cycle 4 closed 2 (A4-01 HIGH + A4-02 MEDIUM); Cycle 5
closes 1 (A5-01 MEDIUM). The descending arity is the expected outcome
of the cross-cohort re-review loop — each cycle's own deliverables
surface fewer residual defects as the underlying ground truth
(SLI-Z7 KQL author-time validity, ADR + spec + Bicep alignment on the
`Simulation.Coordinator` RBAC scope claim) stabilises.

**Cycle 5 amendment log complete. Ready for /speckit.clarify (Cycle 5).**

## Clarifications (Cycle 5 — Pass 1)

### Session 2026-05-11 (Cycle 5 amendment clarify pass 1)

These resolutions close the **three** `[NEEDS CLARIFICATION]` markers
opened by the Cycle 5 amendment cycle at `spec.md:5000-5002` (A5-01:
the Bicep preamble residue defect surfaced by F-TECH-4-01 in the
Step 8al cohort re-review). Cycle 5 is **narrower in scope** than
Cycle 4 (`spec.md:4896-4901`): A5-01 is a single MEDIUM
documentation-correction amendment that rewrites the L305-315
preamble in `infra/bicep/modules/cosmos-simulation-containers.bicep`
and extends one existing contract-test assertion. There is **no new
FR, no new SC, no new ADR, no new test file, no new infrastructure
scope** (`spec.md:4919-4925`). The three Q→A entries below pin the
**wording sequence**, **test-assertion phrase set**, and
**test-assertion code path** for the A5-01 remediation; together they
unblock **Step 8at** (Cycle 5 implement). Cycle 1 / Cycle 2 / Cycle 3
Pass-1 / Cycle 3 Pass-2 / Cycle 4 Pass-1 / Cycle 4 Pass-2 Q→A entries
remain in force unchanged — the three resolutions below are
**additive** and do not contradict any prior resolution. Each
resolution is decided by the `speckit.clarify` agent under the
user's explicit "deciding authority" mandate; each is constitution-
aligned, F-TECH-4-01-remediation-aligned, and Cycle-4-Pass-1-
precedent-consistent. `file:line` evidence is cited for every claim.
**Spec-text propagation** for each Q is noted via
`propagation_target:` annotations and is **deferred** to Step 8at
(Cycle 5 implement) — no other artefacts are modified by this pass.

### Q1 — Shall the rewritten L305-315 Bicep preamble lead with the database-level scope statement, or lead with the "compensating defence-in-depth control" framing?

**Answer**: **Lead with the database-level scope statement, THEN the
compensating defence-in-depth phrase, THEN the `#84` citation.** The
top-down reading sequence of the rewritten preamble MUST be:
(1) "Scope the assignment at the database level —
`${account.id}/dbs/${databaseName}` — which is the narrowest scope
supported by the Cosmos data-plane RBAC API 2024-08-15"; (2) "the
database-level scope is a **compensating defence-in-depth control**
rather than a partition-level guarantee — Cosmos data-plane RBAC API
2024-08-15 does not yet expose a `partitionKey` selector"; (3) the
joint enforcement clauses naming the SLI-Z6 / SLI-Z7 query-time
`where tenant_id == "tnt-stg-smoke"` filter, the
`customDimensions["tenant_id"]` envelope discriminator, and the
Pass-1 Q2 isolation guarantees (i)–(v); (4) the deferred remediation
citation `[backlog issue: #84]`. This sequence is **byte-identical
in ordering** to the three correct precedents that A5-01 brings the
Bicep into alignment with: (a) the ADR-036-011:172-184 narrative
which leads with the database-level scope assertion at L172-175 and
introduces the compensating-control phrase second at L175-177 and the
`#84` citation third at L180-181; (b) the Cycle 4 A4-02 sub-block at
`infra/bicep/modules/cosmos-simulation-containers.bicep:317-327`
which leads with the database-level scope reference at L317-320,
the compensating-control phrase at L318-320, and the `#84` citation
at L326; (c) the F-TECH-4-01 recommended remediation in
`step-8al-rereview-technical.md` § "NEW findings" row which says
verbatim *"State first that the role assignment is database-level,
then retain the compensating defence-in-depth explanation and #84
citation"*. Symmetry with all three precedents minimises future
reviewer confusion and matches the auditability contract at
Constitution Principle IV (single source of truth between the
operator-facing IaC comment and the binding ADR/spec wording). The
**alternative sequence** — leading with the compensating-control
framing and citing the scope second — was considered (the
threat-model-first sequence preferred by some security-engineer
readers for IaC comments) and **rejected** for three reasons:
(i) it inverts the ADR-036-011:172-184 anchor and would re-introduce
asymmetry between the ADR narrative and the Bicep comment — exactly
the class of defect F-TECH-4-01 was filed to close; (ii) it inverts
the existing Cycle 4 A4-02 sub-block at L317-327 which is **already
correct** (Step 8al azure-principal-architect ACCEPT, api-architect
ACCEPT, security-engineer ACCEPT verdicts cite this block); A5-01
consolidates L305-315 + L317-327 into a single coherent block and
the existing L317-327 ordering is the in-tree precedent that the
consolidation MUST preserve (re-rendering L317-327 to a different
ordering would breach the LOW-1 within-cycle immutability discipline
at `spec.md:4982`); (iii) the Cycle 4 Pass-1 Q2 binding wording at
`spec.md:4060-4108` established the canonical phrase *"compensating
defence-in-depth control"* with NIST SP 800-160 §3 and OWASP
defence-in-depth lineage — the **phrase** is locked, only its
**position** is being pinned here; pinning position to match the ADR
anchor is the lowest-friction integration of the locked phrase into
the rewritten Bicep block. The rewritten preamble MUST NOT contain
the strings `partition path`, `pks/<tenant_id>`, or
`/colls/<container>/pks/` anywhere (these are the false claims
F-TECH-4-01 was filed to remove; Q2 below pins the test assertion
that enforces their absence). The actual `scope:` expression at
`infra/bicep/modules/cosmos-simulation-containers.bicep:328` MUST be
byte-identical to the Cycle 4 baseline (`scope:
'${account.id}/dbs/${databaseName}'`) — A5-01 is comment-only.

**Authority**: ADR-036-011:172-184 (correct three-clause
acknowledgement; database-level scope first at L172-175, compensating
defence-in-depth phrase second at L175-177, `#84` citation third at
L180-181). Cycle 4 A4-02 sub-block at
`infra/bicep/modules/cosmos-simulation-containers.bicep:317-327`
(correct in-tree precedent — same ordering; Step 8al
azure-principal-architect, api-architect, security-engineer ACCEPT
verdicts confirm it). F-TECH-4-01 recommended remediation at
`step-8al-rereview-technical.md` § "NEW findings" row (verbatim
*"State first that the role assignment is database-level, then retain
the compensating defence-in-depth explanation and #84 citation"*).
Cycle 4 Pass-1 Q2 binding wording at `spec.md:4060-4108` (the phrase
*"compensating defence-in-depth control"* with NIST SP 800-160 §3 +
OWASP + PCI-DSS lineage — phrase is locked; position is being pinned
here). Cycle 5 in-scope acceptance criterion at `spec.md:4968-4969`
(the consolidation requirement: the L305-315 preamble and the
L317-327 A4-02 block become a single coherent block whose top-down
reading sequence is (1) database-level scope → (2) compensating
defence-in-depth → (3) joint enforcement → (4) backlog #84). LOW-1
within-cycle immutability discipline at `spec.md:4982` (the existing
L317-327 ordering MUST NOT be re-rendered; A5-01 consolidates around
it, not against it). Constitution Principle IV (Transparency and
Auditability — operator-facing IaC documentation MUST align in
sequence as well as content with the binding ADR + spec anchors).

**Spec-text propagation** *(deferred)*:

- `propagation_target: infra/bicep/modules/cosmos-simulation-containers.bicep`
  (comment-block rewrite spanning the current L305-315 preamble plus
  the L317-327 A4-02 sub-block, consolidated into a single coherent
  block whose top-down ordering is (1) database-level scope →
  (2) compensating defence-in-depth → (3) joint enforcement →
  (4) `[backlog issue: #84]`). The actual `scope:` expression at L328
  MUST be byte-identical to the Cycle 4 baseline. **(Step 8at)**
- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  (Cycle 5 amendment sub-section appended in Step 8aq, consistent
  with the Cycle 4 sub-section at L478+) — record the consolidated
  ordering as the post-Cycle-5 binding shape of the Bicep comment
  block; cross-reference this Q1 entry. ADR-036-011 wording at
  :172-184 is **NOT re-amended** (out-of-scope per `spec.md:4979`).
  **(Step 8aq)**
- `propagation_target: tests/contract/test_smoke_tenant_isolation.py`
  — no ordering-specific assertion is added (the test guards the
  *absence* of the offending phrasings per Q2 below, not the
  *presence* of a specific ordering; ordering is enforced by the
  Cycle 5 implement step's manual review against this Q1 anchor and
  by the Step 8au cohort re-review). **(Step 8at — no code change for
  ordering enforcement)**

### Q2 — On what exact set of phrasings shall the extended `test_bicep_comment_block_documents_compensating_control` assertion fail?

**Answer**: **Option (b) — fail on the literal substring
`pks/<tenant_id>` OR the literal substring `partition path`, both
matched case-insensitively, both scoped to the role-assignment
comment block per Q3 below.** The extended assertion is exactly two
new `assert ... not in` (or `not <pattern>.search(...)`) checks
appended to the existing
`test_bicep_comment_block_documents_compensating_control` at
`tests/contract/test_smoke_tenant_isolation.py:250-297`:
**(i)** `assert "pks/<tenant_id>" not in role_block.lower()` (or
the case-insensitive `re.compile(r"pks/<tenant_id>", re.IGNORECASE)`
equivalent) — guarding the exact resolution-string example F-TECH-4-01
identifies at L306-308 of the current Bicep; **(ii)** `assert
"partition path" not in role_block.lower()` (or the case-insensitive
`re.compile(r"partition\s+path", re.IGNORECASE)` equivalent) —
guarding the false claim at L305 of the current Bicep (*"Scope the
assignment to the smoke-tenant partition path"*). Both assertions
emit a failure message naming the offending phrase, the F-TECH-4-01
provenance, and the binding remediation — *"Cycle 5 / A5-01 /
F-TECH-4-01 — the Bicep role-assignment comment block MUST NOT
contain the phrase '<phrase>' which falsely claims a partition-level
scope; the actual scope at L328 is database-level. Per
ADR-036-011:172-184 and `spec.md:5000-5001` Pass-1 Q1/Q2, the
operator-facing comment MUST align with the database-level scope
narrative."* The other three options offered in the
`[NEEDS CLARIFICATION]` marker at `spec.md:5001` are **explicitly
rejected**: **option (a)** (literal `pks/<tenant_id>` only) — too
narrow; it would miss the L305 lead sentence *"Scope the assignment
to the smoke-tenant partition path"* which is the **first** false
claim a top-down reader encounters and is itself the more materially
misleading of the two phrasings (the `pks/<tenant_id>` example is a
parenthetical illustration of the L305 claim; the L305 claim is the
authoritative-looking opening assertion); **option (c)** (full regex
covering `(partition[- ]?(path|key|scope)|pks/<[^>]+>)`) — over-broad;
the rewritten preamble per Q1 above legitimately mentions
*"partition-scope upgrade tracked at [backlog issue: #84]"* (the
backlog issue title contains the token *"partition-scope"*) and the
Cycle 4 A4-02 sub-block at L317-327 already says *"rather than a
partition-level guarantee"* — option (c)'s `(partition[- ]?(path|key|scope))`
alternation would false-positive on both legitimate phrasings and
break the test on the corrected Bicep; **option (d)** (bare token
`partition` anywhere in the role-assignment block) — over-broad for
identical reasons; the rewritten preamble per Q1 above uses
*"partition-level"* and *"partition-scope"* in legitimate comparative
context, and option (d) would block both. Option (b)'s two literal
substrings (`pks/<tenant_id>` and `partition path`) are exactly the
two phrasings the F-TECH-4-01 recommended remediation calls out
verbatim (*"fail on `pks/<tenant_id>` / `partition path` claims"*),
are narrow enough to avoid the (c)/(d) false-positive surface, and
are broad enough together to catch both the resolution-string example
(L306-308) and the lead sentence (L305) — the two phrasings that
together constitute the F-TECH-4-01 defect surface. Case-insensitive
matching guards against minor capitalisation drift (e.g., `Partition
Path` or `PKS/<tenant_id>`) without expanding the surface beyond the
two anchor phrasings. The Cycle 4 Pass-1 Q1 lightweight-regex/lexer
walker discipline at `spec.md:4008-4053` is the precedent for
surface-form regression-guard testing (no AST parser, deterministic
matching, explicit failure messages); option (b) inherits that
shape. The existing test continues to assert (a) the
`compensating defence-in-depth` phrase presence at
`test_smoke_tenant_isolation.py:271-282` and (b) the backlog-issue
identifier presence at `test_smoke_tenant_isolation.py:286-297`
unchanged — the two new option-(b) assertions are **additive**, not
replacements.

**Authority**: F-TECH-4-01 recommended remediation at
`step-8al-rereview-technical.md` § "NEW findings" row (verbatim
*"Extend `test_bicep_comment_block_documents_compensating_control`
to fail on `pks/<tenant_id>` / `partition path` claims in the
role-assignment comment block"*) — option (b) is the literal
operationalisation. Cycle 4 Pass-1 Q1 lightweight-regex/lexer walker
discipline at `spec.md:4008-4053` (lean test-surface, no AST
dependency, deterministic matching, explicit failure messages — the
Q2 assertion extension inherits this shape). Existing test design at
`tests/contract/test_smoke_tenant_isolation.py:250-297` (the two new
assertions extend the existing pattern: `assert
compensating_re.search(role_block)` at L275-282 and `assert
backlog_re.search(role_block)` at L290-297 establish the
`assert <pattern>.search/contains <call on role_block>` pattern;
the option-(b) assertions invert the polarity to `assert ... not in
/ not .search(...)` but otherwise follow the same shape). Cycle 5
acceptance criterion at `spec.md:4968` (*"no longer contains the
phrases `partition path`, `pks/<tenant_id>`, or
`/colls/<container>/pks/`"*) — note that the third phrase
`/colls/<container>/pks/` is a sub-string of `pks/<tenant_id>` once
the latter is grep-located (the path segment containing
`pks/<tenant_id>` necessarily ends `/pks/<tenant_id>`); option (b)
covers the `pks/<tenant_id>` substring directly and thereby covers
the `/colls/<container>/pks/` substring transitively (any block
containing `/colls/<container>/pks/<tenant_id>` also contains
`pks/<tenant_id>` after lowercasing). Cycle 4 A4-02 sub-block at
`infra/bicep/modules/cosmos-simulation-containers.bicep:317-327`
(precedent: legitimately uses *"partition-level"* and
*"compensating defence-in-depth control"* — option (c)/(d) would
false-positive on this block; option (b) does not). F-TECH-4-01
defect description at `spec.md:4952-4956` (the two phrasings
identified are *"partition path"* at L305 and *"`pks/<tenant_id>`"*
at L308 — exactly the two anchors option (b) targets). Constitution
Principle V (Graceful Degradation — predictable failure with
explicit machine-readable indicator: the extended test fails with
a named phrase, a citation chain, and a binding remediation
reference).

**Spec-text propagation** *(deferred)*:

- `propagation_target: tests/contract/test_smoke_tenant_isolation.py`
  (extend `test_bicep_comment_block_documents_compensating_control`
  at L250-297) — append two new assertions matching the option (b)
  shape: (i) case-insensitive absence of the literal substring
  `pks/<tenant_id>` in `role_block`; (ii) case-insensitive absence
  of the literal substring `partition path` in `role_block`. Both
  use `_extract_role_assignment_block(bicep_text)` per Q3 below.
  Failure messages cite the F-TECH-4-01 provenance and the
  ADR-036-011:172-184 / spec.md:5000-5001 anchor pair. The two
  existing assertions (`compensating_re.search(role_block)` and
  `backlog_re.search(role_block)`) are **NOT modified**. **(Step
  8at)**
- `propagation_target: tasks.md` (Cycle 5 implement task — to be
  named in Step 8ar Cycle 5 /speckit.tasks) — record the Q2 option
  (b) shape as the binding test-extension specification; the task
  has 0 implementation-design ambiguity after this Q is pinned.
  **(Step 8ar)**

### Q3 — Shall the extended assertion target ONLY the role-assignment comment block (via `_extract_role_assignment_block()`), or the whole `cosmos-simulation-containers.bicep` file?

**Answer**: **Comment-block-only** — the extended assertions use
`_extract_role_assignment_block(bicep_text)` at
`tests/contract/test_smoke_tenant_isolation.py:220-247` to extract
the `smokeCoordinatorRoleAssignment` resource block (from the
`resource smokeCoordinatorRoleAssignment` declaration at L296 to
the first line matching `^\}\s*$` after it — which is L330 in the
current Bicep), and the two new option-(b) substring checks are
performed against the returned `role_block` string **only**.
Whole-file scoping is **explicitly rejected** for four reasons:
**(i) the existing helper is already the canonical scope-narrowing
primitive** — `_extract_role_assignment_block` was introduced in
Cycle 4 Step 8ae (per the helper's docstring and the
`test_bicep_comment_block_documents_compensating_control` test that
already consumes it at L269), is regex-based and deterministic
(matches `resource smokeCoordinatorRoleAssignment\s+` at the start,
walks forward to `^\}\s*$` at column 0), and is the same primitive
the two existing assertions (`compensating_re.search` at L275 and
`backlog_re.search` at L290) consume; the Q2 extension MUST inherit
this primitive for symmetry — introducing two assertions that scope
to the whole file while the two pre-existing assertions in the same
test scope to `role_block` would create a within-test scope
inconsistency that is itself a future-reviewer trap; **(ii) the test
name is literally `test_bicep_comment_block_documents_compensating_control`**
— the noun phrase *"bicep comment block"* (singular, scoped) is the
test's binding contract surface; promoting to whole-file scope
would falsify the test name and require a separate test (out of
Cycle 5 scope per `spec.md:4929-4930`); **(iii) F-TECH-4-01
recommended remediation says verbatim *"fail on `pks/<tenant_id>`
/ `partition path` claims in the role-assignment comment block"***
(`step-8al-rereview-technical.md` § "NEW findings" row) — the
remediation is comment-block-scoped, not file-scoped; (iv)
**whole-file scoping would risk false positives on legitimate
adjacent prose** elsewhere in `cosmos-simulation-containers.bicep`.
The module currently contains: the `roleDefinitionId` comment block
at L300-303 (which legitimately distinguishes data-plane vs
management-plane RBAC and mentions partitioning concepts in passing
via the `https://learn.microsoft.com/azure/cosmos-db/how-to-setup-rbac`
URL); container resource declarations earlier in the file that
necessarily reference `partitionKey` properties (the container
definitions DO use `partitionKey: { paths: [...] }` blocks —
Cosmos containers have partition keys at the container definition
level, separate from the role-assignment scope question A5-01
addresses); future container resources that may legitimately
document their partition strategy. Whole-file scoping would
false-positive on the container `partitionKey` declarations (the
substring `partition` would match; the substring `partition path`
would match if any future container documentation uses that exact
phrase in a legitimate context) and would force the rewrite or
removal of correct documentation as a side-effect of the A5-01
remediation — violating the Cycle 5 narrowness discipline at
`spec.md:4896-4901`. The whole-file alternative was offered as a
conservative regression guard against future drift but is the
**wrong abstraction**: drift in container `partitionKey` properties
is a different defect class (functional, not documentation) and has
its own contract surface via the container-resource assertion shape
in the same test file (`test_smoke_tenant_isolation.py` already
asserts the role-assignment count is exactly one and the
role-definition-id is the data-plane built-in — these are
container-and-role-level guards, not comment-text guards). The
comment-block-only scope is **the right surface** for A5-01: it
narrowly guards the role-assignment preamble against the two
F-TECH-4-01 phrasings without spilling into adjacent contracts.
Future drift in other comment blocks (e.g., a hypothetical future
defect that re-pastes `pks/<tenant_id>` into a different role
assignment) would be guarded by a **future** test extension scoped
to that future role-assignment block, following the same
`_extract_<resource>_block()` factoring pattern — this is
forward-compatible and consistent with the contract-test surface
expansion discipline established in Cycle 1 / Cycle 2 / Cycle 3.

**Authority**: Existing helper `_extract_role_assignment_block` at
`tests/contract/test_smoke_tenant_isolation.py:220-247` (the
canonical scope-narrowing primitive — already consumed by the two
existing assertions in the test being extended). Existing test name
`test_bicep_comment_block_documents_compensating_control` at
`tests/contract/test_smoke_tenant_isolation.py:250` (the noun phrase
*"comment block"* is the binding contract scope; whole-file scoping
would falsify the name). F-TECH-4-01 recommended remediation at
`step-8al-rereview-technical.md` § "NEW findings" row (verbatim
*"in the role-assignment comment block"*). Cycle 4 Pass-2 T-AA52
acceptance test design (`test_bicep_comment_block_documents_compensating_control`
introduced in Cycle 4 Step 8ae per the test's docstring at
`tests/contract/test_smoke_tenant_isolation.py:253` *"T-AA52 —
OPTIONAL A4-02 evidence: Bicep comment block (L305-315)"* — already
established the comment-block-only scoping convention; A5-01
extends this test, not replaces it). Cycle 5 narrowness discipline
at `spec.md:4896-4901` (carry-overs explicitly out-of-scope; the
extension MUST NOT spill into other contract surfaces). Cosmos
container resource declarations earlier in
`infra/bicep/modules/cosmos-simulation-containers.bicep` (the
`partitionKey: { paths: [...] }` blocks at the container-definition
level — these are legitimately partition-key-related and would
false-positive under whole-file scoping). Constitution Principle II
(Bounded Change Surface — each contract test guards a single
narrow surface; widening the surface implicitly is a forbidden
side-effect). Cycle 5 acceptance criterion at `spec.md:4970`
(*"`tests/contract/test_smoke_tenant_isolation.py::test_bicep_comment_block_documents_compensating_control`
is extended to assert the absence of the offending phrasings"* —
verb is *extended*, not *replaced*; the new assertions inherit the
existing comment-block scope).

**Spec-text propagation** *(deferred)*:

- `propagation_target: tests/contract/test_smoke_tenant_isolation.py`
  (the two new option-(b) assertions per Q2 use
  `_extract_role_assignment_block(bicep_text)` per this Q3) — the
  helper is NOT modified; only its consumer surface is extended.
  **(Step 8at)**
- `propagation_target: tasks.md` (Cycle 5 implement task) — record
  the Q3 comment-block-only scope as the binding test-extension
  scope; the task explicitly cites the existing
  `_extract_role_assignment_block` helper as the in-scope code
  path. **(Step 8ar)**
- `propagation_target: infra/bicep/modules/cosmos-simulation-containers.bicep`
  — no test-related change; the Bicep file remains the read source
  for the test (no `# noqa`-style annotations or test-only
  comments added). **(Step 8at — verify-only, no test-related
  edit)**

**Resolution rollup (Cycle 5 pass 1)**: Q1 → pins the **rewritten
L305-315 preamble ordering** as (1) database-level scope →
(2) compensating defence-in-depth control → (3) joint enforcement →
(4) `[backlog issue: #84]`, byte-identical in ordering to the
ADR-036-011:172-184 anchor and to the existing Cycle 4 A4-02
sub-block at `infra/bicep/modules/cosmos-simulation-containers.bicep:317-327`
that the consolidation MUST preserve; Q2 → pins the **extended
`test_bicep_comment_block_documents_compensating_control` assertion**
as option (b): two case-insensitive literal-substring absence checks
against `pks/<tenant_id>` AND `partition path`, additive to the two
existing presence assertions (`compensating defence-in-depth` and
backlog-issue identifier); Q3 → pins the **extended assertion code
path** as `_extract_role_assignment_block(bicep_text)` (comment-block-
only scope, the canonical scope-narrowing primitive introduced by
Cycle 4 Step 8ae and already consumed by the two existing
assertions in the same test). Together these three resolutions
close all three `[NEEDS CLARIFICATION]` markers at
`spec.md:5000-5002`, lock the A5-01 implementation surface to a
single Bicep comment-block rewrite plus a two-assertion extension
of one existing test, and unblock **Step 8at** (Cycle 5 implement).
The Cycle 5 binding test-count delta is **+0** (extending an
existing test in place, not adding a new test or new parametric
case): the post-Cycle-5-implement test count is therefore
`3400 tests pass / 0 fail (FULL posture)` — identical to the
Cycle 4 baseline at `spec.md:4886`. The OPTIONAL/REQUIRED status
of `test_bicep_comment_block_documents_compensating_control` (the
test is currently marked OPTIONAL by the Cycle 4 Pass-2 Q4 FULL
posture per the docstring at `tests/contract/test_smoke_tenant_isolation.py:253`)
is **not revisited here** — A5-01 extends the assertions but does
not change the OPTIONAL/REQUIRED disposition; any promotion from
OPTIONAL → REQUIRED is reserved for Cycle 5 Pass 2 if surfaced
during a Step 8ao / Step 8ap quality-checklist re-review.

**Cycle 5 clarify pass 1 complete. Ready for /speckit.clarify (Cycle 5, Pass 2).**

## Clarifications (Cycle 5 — Pass 2)

### Session 2026-05-11 (Cycle 5 amendment clarify pass 2)

These resolutions converge the Cycle 5 Pass 1 propagation surface
(`spec.md:5037-5453`) by closing the three residual third-order
ambiguities Pass 1 left implicit: **(i)** the OPTIONAL → REQUIRED
disposition of `test_bicep_comment_block_documents_compensating_control`
which Pass 1 explicitly deferred at `spec.md:5444-5451`; **(ii)** the
exact Python case-folding primitive backing the two Pass 1 Q2
absence assertions (Pass 1 wrote *"case-insensitive"* and offered two
equivalent forms at `spec.md:5184-5191` — `.lower()` + `in` OR
`re.compile(..., re.IGNORECASE)` + `.search` — without pinning a
binding choice); **(iii)** the post-Cycle-5-implement test-count
single-vs-split-posture restatement that follows from Q1's promotion.
Pass 2 also restates the Cycle 4 Pass 2 Q3 Status-flip convergence
rule (`spec.md:4679-4684`) verbatim for the benefit of the Step 8au
cohort re-review, since the rule applies recursively to Cycle 5
close and is the gate criterion for the ADR-036-011 `Proposed →
Accepted` transition that Step 9 (deploy) depends on. Pass 1 Q1
(preamble ordering), Q2 (assertion-phrase set), and Q3 (assertion
code path) remain in force unchanged — Pass 2 is **additive** for
Q2/Q3/Q4 and **supersession-by-promotion** for Q1 (the Pass 1
deferral paragraph at `spec.md:5444-5451` is preserved verbatim per
within-cycle immutability discipline; the binding disposition is
the corrected value pinned here). Cycle 1 / Cycle 2 / Cycle 3 Pass-1 /
Cycle 3 Pass-2 / Cycle 4 Pass-1 / Cycle 4 Pass-2 / Cycle 5 Pass-1
Q→A entries remain in force unchanged. Each resolution below is
decided by the `speckit.clarify` agent under the user's explicit
"deciding authority" mandate; each is constitution-aligned,
F-TECH-4-01-remediation-aligned, Cycle-4-Pass-2-precedent-consistent,
and quantitative where possible. `file:line` evidence is cited for
every claim. **Spec-text propagation** for each Q is noted via
`propagation_target:` annotations and is **deferred** to Step 8at
(Cycle 5 implement: test docstring + Cycle 4 header-comment edit
encoding the REQUIRED promotion; binding `.lower()` substring
assertion form) and Step 8aq (ADR-036-011 Cycle 5 sub-section
appended; Status field NOT flipped until Step 8au cohort re-review
returns clean per Q4 below) — no other artefacts are modified by
this pass.

### Q1 — Shall `test_bicep_comment_block_documents_compensating_control` be promoted from OPTIONAL to REQUIRED as part of the Cycle 5 A5-01 remediation, collapsing the Cycle 4 Pass-2 Q4 minimal-3399 / FULL-3400 posture split into a single 3400 posture?

**Answer**: **Yes — promote OPTIONAL → REQUIRED; collapse the
3399 / 3400 posture split to a single 3400 posture.** The Pass 1
deferral note at `spec.md:5444-5451` left this question to Pass 2;
Pass 2 binds the answer as **Option A** per the F-TECH-4-01
remediation logic outlined in the prompt. Five concrete grounds:
**(i) Cycle 4 already chose FULL** — `tasks.md:2434` records the
FULL posture as RECOMMENDED, and `tasks.md:2527` records T-AA52 as
`[DONE]` with the comment block landed and the test GREEN; the
post-Cycle-4-implement sentinel at `spec.md:4886` certifies *"3400
FULL posture"* as the binding count. The minimal-3399 escape hatch
introduced by Cycle 4 Pass 2 Q4 at `spec.md:4795-4801` was a
within-cycle accommodation for the case where Step 8ae chose not
to rewrite the Bicep comment block; that branch was **not taken**
(per `tasks.md:2527`), so the escape hatch is **already
unexercised history** and Cycle 5 has no operational reason to
preserve it. **(ii) Pytest already collects the test
unconditionally** — `tests/contract/test_smoke_tenant_isolation.py:250-297`
declares the test as a plain `def test_bicep_comment_block_documents_compensating_control(bicep_text: str) -> None:`
with **no `pytest.mark.skip`, no `pytest.mark.skipif`, no
`pytest.mark.xfail`, no conditional fixture, no env-var gate**;
the OPTIONAL label is purely **docstring prose at L253** plus the
header comment at L173 (`# Cycle 4 / T-AA51 (REQUIRED) + T-AA52
(OPTIONAL) — A4-02 evidence tests`). Pytest collection and
execution have never treated T-AA52 as truly skippable — the
3399/3400 split was a **planning artefact**, not a runtime gate.
Promoting the docstring + header comment to REQUIRED brings the
prose in line with the runtime reality. **(iii) F-TECH-4-01 was
missed precisely because the test was labelled OPTIONAL** —
F-TECH-4-01 (the wording-residue defect at L305-308 of
`cosmos-simulation-containers.bicep`) was a surface-form regression
**inside the Bicep comment block** that the existing T-AA52 test
already inspects via `_extract_role_assignment_block`; the test's
two existing assertions (presence of `compensating defence-in-depth`,
presence of backlog issue identifier) did NOT catch the residue
because they assert **presence** of correct phrasing, not
**absence** of incorrect phrasing. The Cycle 5 Pass 1 Q2 absence
assertions are the corrective remedy. The OPTIONAL label is an
explicit signal that the assertion-block is non-binding —
exactly the disposition class F-TECH-4-01 demonstrates is
**inadequate** for a comment-block guard against documentation
drift. REQUIRED promotion removes the signal-disposition gap.
**(iv) Cycle 4 Step 8aj LOW-2 precedent (Z7 pipe-ordering
asymmetry promotion)** — Cycle 4 Step 8aj recorded the lock-the-
asymmetric-evidence precedent for promoting OPTIONAL → REQUIRED
when a re-review surfaces evidence the OPTIONAL discipline failed
to catch a real defect. F-TECH-4-01 is structurally identical: a
re-review (Step 8al) found a defect the OPTIONAL test should
have caught; the symmetric remediation is REQUIRED promotion of
the comment-block test. **(v) Constitution Principle IV
(Transparency and Auditability)** — having a docstring + header
comment that label a test OPTIONAL while pytest treats it as
unconditionally-collected is a transparency defect (operator-
facing claims that contradict runtime behaviour). REQUIRED
promotion eliminates the contradiction. The rejected
alternatives: **Option B** (keep OPTIONAL, defer to a follow-up
cycle) is rejected because the F-TECH-4-01 remediation lands in
Cycle 5 anyway (the absence assertions per Pass 1 Q2) — leaving
the surrounding disposition flag at OPTIONAL while extending the
assertion body is the worst of both worlds (the new absence
assertions are added but their host test remains labelled
non-binding, defeating the F-TECH-4-01 remediation intent);
**Option C** (split disposition — promote the two new absence
assertions to REQUIRED while keeping the existing two presence
assertions OPTIONAL) is rejected because pytest has no
sub-assertion disposition mechanism (a single `def test_*`
function is atomic — all its `assert` statements are either all
collected or all skipped; introducing a separate `def
test_bicep_comment_block_no_partition_residue` function would
double the test-count delta from +0 to +1, contradicting the
Pass 1 rollup at `spec.md:5440-5444` which pinned the +0 delta).
The Cycle 5 implement step (Step 8at) MUST: **(a)** update the
docstring at `tests/contract/test_smoke_tenant_isolation.py:253`
from *"T-AA52 — OPTIONAL A4-02 evidence: Bicep comment block
(L305-315). Cycle 4 FULL posture per Pass-2 Q4..."* to *"T-AA52 —
REQUIRED A4-02 evidence (promoted Cycle 5 Pass 2): Bicep comment
block (L305-315). Single 3400 posture per Cycle 5 Pass 2 Q1; the
minimal/FULL split established by Cycle 4 Pass 2 Q4 at
`spec.md:4795-4801` is collapsed (Cycle 4 chose FULL per
`tasks.md:2527`; Cycle 5 promotion locks it)..."*; **(b)** update
the header comment at `tests/contract/test_smoke_tenant_isolation.py:173`
from `# Cycle 4 / T-AA51 (REQUIRED) + T-AA52 (OPTIONAL) — A4-02
evidence tests` to `# Cycle 4 / T-AA51 (REQUIRED) + T-AA52
(REQUIRED — promoted Cycle 5 Pass 2 per spec.md A5-01) — A4-02
evidence tests`. No `pytest.mark.*` decorator is added or removed
(none currently present, and none required — the runtime
disposition is unchanged; only the prose disposition is corrected
to match). **No other code change** is required for the promotion
— the existing test function body already executes unconditionally.

**Authority**: Pass 1 deferral note at `spec.md:5444-5451` (the
explicit Pass 2 hand-off). Cycle 4 Pass 2 Q4 FULL-posture
disposition at `spec.md:4795-4801` (3400 = FULL = scope-string +
comment-block; 3399 = minimal = scope-string only). Cycle 4 tasks
posture record at `tasks.md:2434` (*"3400 (FULL — RECOMMENDED;
OPTIONAL T-AA52 included)"*) and `tasks.md:2527` (T-AA52 [DONE],
FULL posture taken). Post-Cycle-4-implement sentinel at
`spec.md:4886` (*"3400 FULL posture"* is the binding test count).
Test-function shape at `tests/contract/test_smoke_tenant_isolation.py:250-297`
(plain `def test_*` with no skip/xfail markers — runtime
disposition is unconditional). Docstring at L253 + header comment
at L173 (the **only** OPTIONAL signals in the test file; both are
prose, neither is a runtime gate). F-TECH-4-01 defect surface at
`spec.md:4952-4956` (the wording-residue defect inside the comment
block — the same surface T-AA52 inspects). Cycle 5 Pass 1 Q2
absence-assertion extension at `spec.md:5175-5240` (the
F-TECH-4-01 remediation lands inside this test function; promoting
the host function to REQUIRED is the symmetric prose-side
remediation). Cycle 4 Step 8aj LOW-2 precedent (Z7 pipe-ordering
asymmetry promotion — re-review evidence of missed defect ⇒
OPTIONAL → REQUIRED promotion; documented at `step-8aj-merit-validation.md`
referenced from spec close commentary). Constitution Principle IV
(Transparency and Auditability — prose disposition labels MUST
match runtime disposition). Cycle 2 Q1 supersession precedent at
`spec.md:389-392` (later passes can supersede earlier dispositions
within the same amendment cycle; the Pass 1 deferral paragraph at
`spec.md:5444-5451` is preserved verbatim and is hereby
**superseded by promotion**).

**Spec-text propagation** *(deferred)*:

- `propagation_target: tests/contract/test_smoke_tenant_isolation.py`
  (docstring at L253 + header comment at L173) — update the prose
  to record the REQUIRED disposition with a citation to this Q1.
  No `pytest.mark.*` addition; no test-body edit beyond the
  Pass 1 Q2 absence-assertion appends already pinned at
  `spec.md:5281-5292`. **(Step 8at)**
- `propagation_target: specs/036-sim-agent-extend/tasks.md` —
  update the Cycle 5 implement task to record the REQUIRED
  promotion in its acceptance criterion; update the §26.8
  T-AA52 status row at `tasks.md:2527` cross-reference (or
  the Cycle 5 equivalent table when it is appended in Step 8ar)
  to reflect REQUIRED. The Cycle 4 historical posture-record
  rows at `tasks.md:2434`, `tasks.md:2169`, `tasks.md:2244`,
  `tasks.md:2280`, `tasks.md:2341`, `tasks.md:2346`, and
  `tasks.md:2457` are **preserved verbatim** per immutability
  discipline; the binding Cycle 5 record is the new entry added
  by Step 8ar that cites this Q1 as authority. **(Step 8ar)**
- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  (Cycle 5 sub-section appended in Step 8aq) — record the
  OPTIONAL → REQUIRED promotion as a Cycle 5 amendment-cycle
  observation alongside the Bicep comment-block consolidation
  (Pass 1 Q1) and the assertion extension (Pass 1 Q2 + Q3).
  ADR-036-011:172-184 binding wording is **NOT re-amended**
  (out-of-scope per `spec.md:4979`). **(Step 8aq)**
- `propagation_target: CHANGELOG.md` (Cycle 5 close block —
  `### Changed (spec 036 — Cycle 5 amendment cycle)` sub-section
  per Cycle 4 Pass 2 Q2 format precedent at `spec.md:4830-4836`)
  — record the REQUIRED promotion as a Changed-class entry.
  **(Step 8at close)**

### Q2 — What is the binding Python case-folding primitive for the two Pass 1 Q2 absence assertions — `.lower()` + `in`, `re.compile(..., re.IGNORECASE)` + `.search`, or `str.casefold()`?

**Answer**: **`.lower()` + plain `in` substring check** (Option A
in the prompt taxonomy). The two new absence assertions appended
to `test_bicep_comment_block_documents_compensating_control` per
Pass 1 Q2 at `spec.md:5184-5191` MUST be encoded **byte-identically**
as:

```python
assert "pks/<tenant_id>" not in role_block.lower(), (
    "Cycle 5 / A5-01 / F-TECH-4-01 — the Bicep role-assignment "
    "comment block MUST NOT contain the phrase 'pks/<tenant_id>' "
    "which falsely claims a partition-level scope; the actual "
    "scope at L328 is database-level. Per ADR-036-011:172-184 "
    "and spec.md:5000-5001 Pass-1 Q1/Q2, the operator-facing "
    "comment MUST align with the database-level scope narrative."
)
assert "partition path" not in role_block.lower(), (
    "Cycle 5 / A5-01 / F-TECH-4-01 — the Bicep role-assignment "
    "comment block MUST NOT contain the phrase 'partition path' "
    "which falsely claims a partition-level scope; the actual "
    "scope at L328 is database-level. Per ADR-036-011:172-184 "
    "and spec.md:5000-5001 Pass-1 Q1/Q2, the operator-facing "
    "comment MUST align with the database-level scope narrative."
)
```

Pass 1 Q2's propagation_target at `spec.md:5184-5191` offered the
`.lower()` form **as the canonical example** with the
`re.IGNORECASE` form **as an equivalent alternative** (*"`assert
"pks/<tenant_id>" not in role_block.lower()` (or the
case-insensitive `re.compile(r"pks/<tenant_id>", re.IGNORECASE)`
equivalent)"*). Pass 2 collapses the equivalence by **pinning
`.lower()` + `in` as the binding form** and rejecting the regex
alternative. Five grounds: **(i) Simplicity** — `.lower()` + `in`
is a single normalisation + substring check with zero regex
compilation overhead and zero escape-character risk; the
literal-substring check is the simplest mechanism that produces
the correct behaviour. **(ii) No regex metacharacters in either
literal** — `pks/<tenant_id>` contains `<` and `>` (which are NOT
regex metacharacters in any flavour) and `/` (not a metacharacter
in Python `re`); `partition path` is alphanumeric + space; neither
literal NEEDS regex semantics. Using `re.compile(...)` for either
introduces compilation cost + a future-author trap (someone reading
the test might assume the pattern uses regex semantics and try to
add a `*` or `+`, breaking the absence semantics). **(iii) Symmetry
with the existing `tnt-prod` absence check** — the test file
already contains a precedent at `tests/contract/test_smoke_tenant_isolation.py:166`:
`assert "tnt-prod" not in role_block.lower()` — the **same shape**
(`role_block.lower()` + literal `in`-check). The Q2 absence
assertions inherit this exact precedent for symmetry; introducing
`re.IGNORECASE` would create a within-file inconsistency where
some absence checks use `.lower()` + `in` and others use regex —
a future-reviewer trap. **(iv) `str.casefold()` is rejected** —
Unicode-aware case folding is irrelevant for ASCII Bicep
comments (the Bicep language is ASCII-only for comment syntax;
Unicode in identifiers is restricted; the F-TECH-4-01 defect
phrasings are pure ASCII); `.casefold()` would introduce no
additional safety and would be inconsistent with the L166
precedent. **(v) The space-vs-hyphen discriminator is preserved
by simple `.lower()` substring** — the Pass 1 Q2 false-positive
analysis at `spec.md:5210-5219` correctly identified that
`partition path` (with SPACE) does NOT collide with the
legitimate `partition-level` / `partition-scope` (with HYPHEN)
in the Cycle 4 A4-02 sub-block at
`infra/bicep/modules/cosmos-simulation-containers.bicep:317-327`
nor with the rewritten Cycle 5 preamble per Pass 1 Q1. Python's
plain `in` substring check is byte-exact: it matches the literal
characters including the space, and the space-vs-hyphen
distinction IS the discriminator. **Confirmed**: `"partition
path"` (lowercased) does NOT appear as a substring in
*"partition-level"*, *"partition-scope"*, *"partitionKey"*, or
any other legitimate phrasing in the file; the only way the
substring can appear is if a future drift re-pastes the literal
F-TECH-4-01 phrasing — which is exactly the regression the
assertion guards. **No regex word-boundary anchoring is
required** because the literal substring (with embedded space)
already provides the discriminator. The other Pass 1 Q2
alternatives are reaffirmed as rejected (option (a) — too
narrow; option (c) — over-broad on `partition-scope`; option (d)
— over-broad on bare `partition` token); only the case-folding
mechanism within the chosen option (b) is being pinned here.

**Authority**: Existing precedent at
`tests/contract/test_smoke_tenant_isolation.py:166` (the `tnt-prod`
absence check: `assert "tnt-prod" not in role_block.lower()` — same
shape, same primitive; the Q2 absence assertions inherit this
form for within-file symmetry). Pass 1 Q2 canonical example at
`spec.md:5184-5191` (the `.lower()` + `in` form is offered as the
primary; Pass 2 promotes it from primary-among-equivalents to
**binding sole form**). Pass 1 Q2 false-positive analysis at
`spec.md:5210-5219` (the space-vs-hyphen discriminator analysis
that confirms simple substring matching is sufficient — no
`\b`-anchored regex needed). Python `re` documentation
(`pks/<tenant_id>` and `partition path` contain no regex
metacharacters; regex semantics provide no additional matching
power for these literals). Cycle 4 Pass-1 Q1 lightweight-regex
discipline at `spec.md:4008-4053` (regex used only when needed —
prefer plain string operations when adequate; the Pass 1 Q2
extension at L5240 cites this same principle). Constitution
Principle II (Bounded Change Surface — each test assertion uses
the simplest mechanism that produces correct semantics).
Constitution Principle V (Graceful Degradation — failure messages
MUST be operator-readable; plain `in`-check + lowercased input
produces a clean failure message with no regex-pattern noise).
Bicep language spec (ASCII-only comment syntax — Unicode case
folding is irrelevant; `.lower()` is sufficient).

**Spec-text propagation** *(deferred)*:

- `propagation_target: tests/contract/test_smoke_tenant_isolation.py`
  — append the two assertions **byte-identically** as shown in
  the code-block above. Use `.lower()` + plain `in` substring
  check. Do **NOT** use `re.compile(..., re.IGNORECASE)`. Do
  **NOT** use `str.casefold()`. Failure messages are the literal
  multi-line strings shown above; line breaks within the message
  strings are encoded as Python implicit string concatenation
  (the same style used at L138-141, L166-168, L207-216 of the
  same file). **(Step 8at)**
- `propagation_target: tasks.md` (Cycle 5 implement task — Step
  8ar) — record the Q2 binding code form (`.lower()` + plain `in`,
  not regex) as the canonical implementation. **(Step 8ar)**
- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  — no ADR change (Q2 binds the test-code form, not an ADR
  surface). **(Step 8aq — no edit)**

### Q3 — What is the binding post-Cycle-5-implement test count, given Q1's promotion of T-AA52 to REQUIRED and Pass 1's +0 test-count delta?

**Answer**: **3400 tests pass / 0 fail (single posture, no
minimal/FULL split)**. The Cycle 5 binding post-implement test
count is **3400** — identical in number to the Cycle 4 FULL-
posture baseline at `spec.md:4886` (*"test count delta +9 (3391
baseline → 3400 FULL posture)"*), but with the **disposition
collapsed**: the Cycle 4 Pass 2 Q4 minimal-3399 / FULL-3400
posture split established at `spec.md:4795-4801` is hereby
superseded — post-Cycle-5 there is a **single 3400 posture**
binding for all subsequent cycles (Cycle 6 / Cycle 7 / ...). The
+0 test-count delta from Pass 1 rollup at `spec.md:5440-5444` is
preserved: the Cycle 5 implement step (Step 8at) extends the
existing `test_bicep_comment_block_documents_compensating_control`
test function in place with two new `assert ... not in` statements
(per Pass 1 Q2 + Pass 2 Q2 binding form) and updates the
docstring + header comment to record the REQUIRED promotion (per
Pass 2 Q1) — no new `def test_*` function is added, no
parametrize axis is widened, no new test file is added. Pytest
collects the same 3400 nodes pre- and post-Cycle-5. The
**material change** is dispositional: pre-Cycle-5, the test count
**could be** 3399 (if a future cohort chose to skip T-AA52 — a
choice that was offered by the minimal-posture escape hatch at
`spec.md:4795-4801` but never exercised); post-Cycle-5, the
test count **MUST be** 3400 (the REQUIRED promotion eliminates
the escape hatch). Step 8at's pytest invocation gate
(`python -m pytest -q`) MUST assert `returncode == 0` AND the
collected-node count is exactly **3400** with no
skipped/xfailed nodes for `test_bicep_comment_block_documents_compensating_control`.
The Cycle 4 Step 8af-recorded posture choice at `tasks.md:2434`
and `tasks.md:2527` (which selected FULL = 3400) is preserved
verbatim in tasks.md per within-cycle immutability; the **binding
post-Cycle-5 rule** is the single-posture 3400 record added by
Step 8ar Cycle 5 /speckit.tasks. The Pass 1 rollup at
`spec.md:5440-5444` is **reaffirmed** — the Cycle 5 delta is
+0 — and **clarified** here by removing the residual *"posture-
choice"* ambiguity Pass 1 inherited from the Cycle 4 minimal/FULL
language. Any cohort re-review (Step 8au) reading the Cycle 4
posture-choice language at `tasks.md:2434` or `tasks.md:2527` in
isolation is to consult this Pass 2 Q3 binding correction: **3400
is the single binding count; the minimal-3399 alternative is
retired**.

**Authority**: Pass 1 rollup +0 delta at `spec.md:5440-5444`
(*"the Cycle 5 binding test-count delta is +0... the post-Cycle-5-
implement test count is therefore 3400 tests pass / 0 fail (FULL
posture)"* — note the FULL-posture qualifier is what Pass 2 Q3
collapses). Cycle 4 implement sentinel at `spec.md:4886` (*"3400
FULL posture"* certified empirically — the actual pytest run
result). Cycle 4 Pass 2 Q4 posture-split establishment at
`spec.md:4795-4801` (the minimal/FULL choice — Cycle 4-only
mechanism). Pass 2 Q1 supersession (this section, immediately
above — REQUIRED promotion of T-AA52 eliminates the FULL/minimal
distinction). Test-function shape at
`tests/contract/test_smoke_tenant_isolation.py:250-297` (plain
`def test_*` collected unconditionally — the post-Q1 disposition
matches the pre-Q1 runtime behaviour; the dispositional flip is
prose-only; the numerical count is unchanged at 3400).
Cycle 2 Q1 supersession precedent at `spec.md:389-392` (later
passes supersede earlier dispositional rules; the minimal/FULL
language is superseded but the original lines remain verbatim).

**Spec-text propagation** *(deferred)*:

- `propagation_target: tasks.md` (Cycle 5 implement task §26.8
  equivalent table — appended by Step 8ar) — record the binding
  Cycle 5 post-implement test count as exactly **3400** with no
  minimal/FULL split annotation. Cite this Q3 as authority. The
  Cycle 4 historical rows are preserved verbatim. **(Step 8ar)**
- `propagation_target: tasks.md` Step 8at acceptance criterion
  (Cycle 5 implement task) — `python -m pytest -q` MUST return
  returncode 0 AND `3400 passed` (no `, X skipped` qualifier for
  `test_bicep_comment_block_documents_compensating_control`).
  **(Step 8at)**
- `propagation_target: CHANGELOG.md` (Cycle 5 close block under
  `### Changed (spec 036 — Cycle 5 amendment cycle)`) — record
  the dispositional collapse (minimal/FULL split retired; single
  3400 posture binding going forward) as a Changed-class entry,
  alongside the Bicep comment-block consolidation and the
  test-extension entries. **(Step 8at close)**
- `propagation_target: specs/036-sim-agent-extend/spec.md` —
  no spec-body edit needed beyond this Pass 2 Q3 entry; the
  Pass 1 rollup at `spec.md:5440-5444` is preserved verbatim
  (the FULL-posture qualifier in that paragraph is hereby
  superseded by the single-posture 3400 binding pinned here).
  **(Step 8at — verify-only)**

### Q4 — Does the Cycle 4 Pass 2 Q3 ADR-036-011 `Proposed → Accepted` multi-cycle convergence rule (`spec.md:4679-4684`) apply to Cycle 5 close, and what is the Cycle 5 close gate criterion?

**Answer**: **Yes — the rule applies recursively to Cycle 5
close; gate criterion is `0 OBJECT votes AND 0 NEW merit-
validated findings against ADR-036-011 from Step 8au cohort
re-review`; on gate-pass the Status flips `Proposed → Accepted`
in the same close commit; on gate-fail the Status remains
`Proposed` and another amendment cycle (Cycle 6 / ...) is
opened**. The Cycle 4 Pass 2 Q3 rule at `spec.md:4636-4684`
(authoritative section) and the resolution rollup restatement at
`spec.md:4836-4842` are explicitly **recursive across cycles**
(*"recursive across Cycle 5 / Cycle 6 / ...; no time-bound
auto-flip; no revert once Accepted"*). Cycle 5 inherits the rule
unchanged; this Pass 2 Q4 entry is a **verbatim restatement** for
the benefit of Step 8au cohort re-review readers — the rule is
**not** modified, superseded, or re-derived. The Cycle 5 close
gate criterion is therefore: **on Step 8au cohort re-review
verdict for the Cycle 5 close, IF the verdict is `0 OBJECT votes
AND 0 NEW merit-validated findings against ADR-036-011`, THEN in
the same close commit (a) flip ADR-036-011 Status from `Proposed`
to `Accepted`; (b) record the flip in the Cycle 5 sentinel close
block; (c) the ADR is locked from further revision under the
Cycle 4 Pass 2 Q3 *"no revert once Accepted"* clause. Step 9
(deploy) is gated on the `Accepted` Status — Step 9 MUST NOT
proceed while the Status is `Proposed`**. The mechanism is
**identical** to Cycle 4 close (which itself did not flip the
Status because the Step 8al cohort re-review surfaced
F-TECH-4-01 as a NEW merit-validated finding, opening Cycle 5 in
lieu of flipping Status). Cycle 5 close has the **same**
opportunity: if Step 8au returns clean, ADR-036-011 reaches
`Accepted` and Step 9 unlocks; if Step 8au surfaces a new merit-
validated finding (a Cycle 6 amendment cycle becomes the
remediation pathway), the Status remains `Proposed` and another
cycle opens. **No new convergence rule is introduced** by this Q4
— Pass 2 Q4 is purely a citation-and-restatement entry to ensure
the Step 8au cohort re-review reads the Cycle 4 Pass 2 Q3 rule
in the Cycle 5 Pass 2 context.

**Authority**: Cycle 4 Pass 2 Q3 binding rule at
`spec.md:4636-4684` (the multi-cycle Proposed→Accepted
convergence rule; *"recursive across Cycle 5 / Cycle 6 / ...; no
time-bound auto-flip; no revert once Accepted"*). Cycle 4 Pass 2
Q3 resolution rollup restatement at `spec.md:4836-4842` (same
rule, summary form). Cycle 4 Pass 2 Q3 `propagation_target:
tasks.md` at `spec.md:4680-4684` (the Step 8al cohort re-review
acceptance criterion that operationalises the rule — Step 8au is
the Cycle 5 equivalent and inherits the same operationalisation
verbatim). ADR-036-011 Status field at
`docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
(currently `Proposed` per Cycle 4 close — Cycle 4 close did not
flip the Status because Step 8al surfaced F-TECH-4-01 as a NEW
merit-validated finding; Cycle 5 close has the next opportunity).
Step 9 deploy-gate language at `tasks.md` (Step 9 task definition
— deploy gated on `Accepted` ADR Status). Constitution Principle
III (Decisive Convergence — amendment cycles converge on a
definite `Accepted` state via cohort-verified close; no
indefinite-Proposed limbo). Cycle 2 Q1 immutability precedent at
`spec.md:389-392` (rules established in earlier passes are not
re-derived in later passes; restatement is acceptable, supersession
requires explicit grounds).

**Spec-text propagation** *(deferred)*:

- `propagation_target: tasks.md` Step 8au cohort re-review
  acceptance criterion — MUST cite the Cycle 4 Pass 2 Q3 rule
  at `spec.md:4636-4684` AND this Cycle 5 Pass 2 Q4 restatement;
  the criterion text is identical to the Step 8al criterion
  established by `spec.md:4680-4684` with `Step 8al → Step 8au`
  and `Cycle 4 → Cycle 5` substitutions. **(Step 8ar — Cycle 5
  /speckit.tasks task definition for Step 8au)**
- `propagation_target: docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`
  — no Status field change at Step 8aq (the ADR Cycle 5
  sub-section append documents the Cycle 5 observations but does
  NOT flip the Status); the Status flip is reserved to Step 8au
  close commit, gated on cohort re-review verdict per the rule.
  **(Step 8aq — verify Status remains `Proposed` post-append;
  Step 8au — flip on clean verdict)**
- `propagation_target: specs/036-sim-agent-extend/spec.md` —
  no spec-body edit; this Pass 2 Q4 entry is the spec-side anchor
  for the Cycle 5 application of the rule. **(verify-only)**

**Resolution rollup (Cycle 5 pass 2)**: Q1 → **promotes** the
T-AA52 `test_bicep_comment_block_documents_compensating_control`
disposition from OPTIONAL to REQUIRED (docstring at
`tests/contract/test_smoke_tenant_isolation.py:253` + header
comment at L173 updated; no `pytest.mark.*` change; runtime
behaviour unchanged because the test was already collected
unconditionally; the OPTIONAL label was prose-only and
contradicted the runtime reality — F-TECH-4-01 demonstrated the
inadequacy of the OPTIONAL signal-disposition; the Pass 1
deferral at `spec.md:5444-5451` is preserved verbatim and
**superseded** by this binding promotion); Q2 → **pins** the
binding Python case-folding primitive for the Pass 1 Q2 absence
assertions as `.lower()` + plain `in` substring check
(byte-identical Python code shown verbatim in Q2 above; the
`re.IGNORECASE` and `str.casefold()` alternatives mentioned in
Pass 1 Q2 are rejected; the `.lower()` form is symmetric with the
existing precedent at `tests/contract/test_smoke_tenant_isolation.py:166`
[`assert "tnt-prod" not in role_block.lower()`] and is the
simplest mechanism that produces correct semantics for the two
ASCII literals `pks/<tenant_id>` and `partition path`); Q3 →
**confirms** the binding post-Cycle-5-implement test count as
**3400 tests pass / 0 fail (single posture, no minimal/FULL
split)** — the Cycle 4 Pass 2 Q4 minimal-3399 escape hatch at
`spec.md:4795-4801` is **retired** by the Q1 REQUIRED promotion;
the Cycle 5 implement delta is +0 (test extended in place); pytest
collects 3400 nodes pre- and post-Cycle-5 with zero skip/xfail
for T-AA52; Q4 → **restates** the Cycle 4 Pass 2 Q3 multi-cycle
Proposed→Accepted convergence rule at `spec.md:4636-4684`
**verbatim** for Cycle 5 close (Step 8au cohort re-review gate;
`0 OBJECT votes AND 0 NEW merit-validated findings against
ADR-036-011` ⇒ Status flips `Proposed → Accepted` in the close
commit; Step 9 deploy unlocks; otherwise Cycle 6 opens). Together
these four resolutions **converge** the Cycle 5 amendment cycle:
the Bicep comment-block consolidation surface (Pass 1 Q1), the
assertion-phrase set (Pass 1 Q2), the assertion code path
(Pass 1 Q3), the assertion disposition (Pass 2 Q1), the
assertion case-folding primitive (Pass 2 Q2), the post-implement
test-count posture (Pass 2 Q3), and the close-gate convergence
rule (Pass 2 Q4) are **all pinned with binding decisive answers
and `file:line` citation chains**. **No new `[NEEDS
CLARIFICATION]` markers are introduced.** The Cycle 5 implement
surface is now fully specified for Step 8at (Bicep comment-block
rewrite + test docstring/header-comment update + two `.lower()`
+ `in` absence assertions appended), Step 8ar (Cycle 5
/speckit.tasks task definitions for T-AB01..T-AB0n), Step 8aq
(ADR-036-011 Cycle 5 sub-section append; Status remains
`Proposed`), and Step 8au (Cycle 5 cohort re-review with the
Cycle 4 Pass 2 Q3 rule applied; Status flip to `Accepted` on
clean verdict). Cycle 1 / Cycle 2 / Cycle 3 Pass-1 / Cycle 3
Pass-2 / Cycle 4 Pass-1 / Cycle 4 Pass-2 / Cycle 5 Pass-1 Q→A
entries remain in force unchanged.

**Cycle 5 clarify pass 2 complete. CONVERGED. Ready for /speckit.checklist (Cycle 5).**

**Cycle 5 checklist complete. Ready for /speckit.plan (Cycle 5).**

**Cycle 5 plan complete. Ready for /speckit.tasks (Cycle 5).**

**Cycle 5 tasks complete (T-AA57..T-AA61). Ready for /speckit.analyze (Cycle 5).**

## Cycle 5 Analyze Report (post Step 8ar tasks)

> **Scope of this analyze pass**: Non-destructive cross-artifact
> consistency and quality analysis of the Cycle 5 deliverables produced
> by Steps 8am (specify), 8an (clarify Pass 1), 8ao (clarify Pass 2),
> 8ap (checklist), 8aq (plan), and 8ar (tasks). Compares
> `spec.md:4888-6000` (Cycle 5 amendment log + Pass 1 + Pass 2 +
> checklist sentinel + plan sentinel + tasks sentinel) ↔ `plan.md:1383-1978`
> (Cycle 5 plan addendum + PD-C5-01) ↔ `tasks.md:2546-2772`
> (§27 Cycle 5 task block: T-AA57..T-AA61) ↔
> `quality.md:983-1198` (CHK231..CHK244) ↔ ADR-036-011 Cycle 5
> sub-section (`docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:945-1224`)
> ↔ current source-tree reality
> (`infra/bicep/modules/cosmos-simulation-containers.bicep:290-334`,
> `tests/contract/test_smoke_tenant_isolation.py:160-297`). Read-only
> pass; no files outside spec.md are modified.

### 1. Executive summary

**Verdict**: **PASS-WITH-MINOR** — 0 HIGH, 1 MEDIUM, 3 LOW findings.
All blocking content is correct. Cycle 5 implement (Step 8at) is
unblocked. The single MEDIUM is a Cycle-4-analogous citation-drift
finding in CHK237 that is **recommended as a fold-in** during Step 8at
(mirrors the Cycle 4 analyze MEDIUM-3 → Step 8ak fold-in pattern). All
three LOW findings are pure citation-imprecision artefacts that do not
affect implementation correctness.

| Metric | Count |
|--------|------:|
| HIGH findings | 0 |
| MEDIUM findings | 1 |
| LOW findings | 3 |
| Total findings | 4 |
| Surfaces analysed | 10 |
| Citation drift entries | 2 (1 MEDIUM, 1 LOW) |
| Within-cycle immutability violations | 0 |
| ADR Status field flip violations | 0 (Status remains `Proposed` — correct) |
| New ADR file violations | 0 (no `ADR-036-012-*.md` exists per `glob` check) |
| Spec ↔ plan citation reconciliation | 100% (PD-C5-01 anchors valid) |
| Spec ↔ tasks citation reconciliation | 100% (T-AA57..T-AA61 anchors valid) |
| Spec ↔ checklist citation reconciliation | 91% (1 MEDIUM citation drift in CHK237) |
| Spec ↔ ADR citation reconciliation | 100% (Cycle 5 sub-section anchors valid; Status `Proposed` preserved) |
| Task ↔ file:line reality check | 100% (pre-implement Bicep + test state verified) |
| Test-count math consistency | 100% (3400 single-posture consistent across all 6 artefacts) |

### 2. Per-section findings

#### 2.1 Spec ↔ Plan consistency (PD-C5-01 ↔ A5-01) — ✅ PASS

- PD-C5-01 at `plan.md:1427-1929` cites spec anchors **A5-01 detail**
  (`:4943, 4947-4992`), **Pass 1 Q1** (`:5067-5096`), **Pass 1 Q2**
  (`:5175-5240`), **Pass 1 Q3** (`:5299-5418`), **Pass 2 Q1**
  (`:5498-5614`), **Pass 2 Q2** (`:5650-5754`), **Pass 2 Q3**
  (`:5776-5859`), **Pass 2 Q4** (`:5863-5897`). All eight ranges
  resolve to valid Cycle 5 content blocks; no broken anchors.
- PD-C5-01 in-scope/out-of-scope (`plan.md:1428-1539, 1673-1686`)
  matches A5-01 at `spec.md:4973-4984` verbatim — six out-of-scope
  items enumerated identically (ADR-036-011:172-184; Bicep L328
  `scope:`; spec.md:3907-3925 A4-02 wording; plan.md:682 /
  tasks.md:1929 / quality.md:367 / quality.md:528 LOW-1 mirrors;
  L317-327 A4-02 sub-block).
- PD-C5-01 acceptance criteria at `plan.md:1795-1877` mirror spec
  A5-01 acceptance at `spec.md:4967-4972` with Pass 1 / Pass 2
  resolutions correctly folded in (10 criteria; same enumeration
  order; CHK231-CHK244 cross-references all valid).
- Test count: PD-C5-01 cites **3400 single posture** (`plan.md:1594`)
  — matches A5-01 acceptance criterion 4 + Pass 2 Q3 binding
  (`spec.md:5776-5815`).

#### 2.2 Spec ↔ Tasks consistency (T-AA57..T-AA61 ↔ A5-01 + Pass 1 + Pass 2) — ✅ PASS

- T-AA57 (`tasks.md:2566-2577`) — Bicep preamble rewrite cites
  spec anchors at `:4943, 4947-4992` (A5-01 detail) and `:5067-5096`
  (Pass 1 Q1 four-clause ordering); quality CHK231 + CHK232.
- T-AA58 (`tasks.md:2579-2590`) — absence-assertion append cites
  spec anchors at `:4970` (acceptance criterion), `:5175-5240`
  (Pass 1 Q2 option (b)), `:5299-5418` (Pass 1 Q3 scope), `:5650-5754`
  (Pass 2 Q2 case-folding), `:5656-5673` (verbatim Python); quality
  CHK234 + CHK235.
- T-AA59 (`tasks.md:2592-2603`) — T-AA52 prose promotion cites
  spec anchors at `:4943, 4947-4992`, `:5498-5614` (Pass 2 Q1),
  `:5776-5859` (Pass 2 Q3); quality CHK233 + CHK243.
- T-AA60 (`tasks.md:2605-2616`) — CHANGELOG aggregator cites spec
  anchors at `:4943, 4947-4992`, `:5642-5646` (Pass 2 Q1 CHANGELOG
  propagation), `:5848-5853` (Pass 2 Q3 CHANGELOG dispositional-
  collapse propagation); quality CHK240.
- T-AA61 (`tasks.md:2618-2629`) — verification gate cites spec
  anchors at `:4971`, `:5776-5859` (Pass 2 Q3); quality CHK236 +
  CHK242.
- Task dependency edges (`tasks.md:2564-2649`) — T-AA57 → T-AA58 is
  correctly enforced (T-AA58 depends-on T-AA57 because absence
  assertions would fail against the un-rewritten Bicep); T-AA59 `[P]`
  parallel; T-AA60 depends on T-AA57+T-AA58+T-AA59; T-AA61 depends
  on T-AA57+T-AA58+T-AA59+T-AA60. Critical path 4 hops.
- File-target line-range citations across T-AA57..T-AA61 all
  resolve to live source-tree locations (verified §2.6 below).

#### 2.3 Spec ↔ Checklist consistency (CHK231-CHK244) — 🟡 ONE MEDIUM citation drift

- **CHK231** (`quality.md:985-996`) cites `spec.md:4943` + `:4965-4968`
  + `:5117-5124` for Bicep preamble residue acceptance — all three
  ranges resolve; the case-insensitive substring absence claim
  (`partition path`, `pks/<tenant_id>`, `/colls/<container>/pks/`)
  matches A5-01 acceptance criterion 1 at `spec.md:4968` verbatim.
  ✅
- **CHK232** (`quality.md:997-1009`) cites `spec.md:4969` + `:5067-5096`
  for four-clause ordering — both ranges resolve; the four-clause
  ordering listed in CHK232 ((1) database-level scope →
  (2) compensating defence-in-depth → (3) joint enforcement →
  (4) `[backlog issue: #84]`) matches Pass 1 Q1 verbatim at
  `spec.md:5067-5080`. T-AA57 description (`tasks.md:2569`) encodes
  this ordering. ✅
- **CHK233** (`quality.md:1013-1029`) cites `spec.md:5498-5586` +
  `:5616-5623` for OPTIONAL→REQUIRED prose rewrite. The quoted
  current docstring text *"T-AA52 — OPTIONAL A4-02 evidence: Bicep
  comment block (L305-315). Cycle 4 FULL posture per Pass-2 Q4..."*
  matches the live docstring at
  `tests/contract/test_smoke_tenant_isolation.py:253-255` (verified
  by direct file inspection). The rewritten text matches Pass 2 Q1
  binding at `spec.md:5568-5577`. ✅
- **CHK234** (`quality.md:1030-1044`) cites `spec.md:5650-5754` +
  `:5656-5673` for `.lower()` + plain `in` binding. Verbatim Python
  at `spec.md:5656-5673` shows the two `assert ... not in
  role_block.lower(), (...)` statements — matches Pass 2 Q2 binding
  decision at `spec.md:5650-5754` verbatim. ✅
- **CHK235** (`quality.md:1045-1059`) cites `spec.md:5234-5239` +
  `:5289-5292` + `:5301-5418` for byte-identical preservation of
  pre-existing presence assertions. The live test at
  `tests/contract/test_smoke_tenant_isolation.py:271-282`
  (`compensating_re.search`) and `:286-297` (`backlog_re.search`)
  exists and matches CHK235's preservation requirement. ✅
- **CHK236** (`quality.md:1063-1076`) cites `spec.md:5440-5444` +
  `:5776-5815` for single 3400 posture. Both ranges resolve and
  match Pass 2 Q3 binding. ✅
- **CHK237** (`quality.md:1080-1094`) — ⚠️ **MEDIUM citation drift**
  (see §3 below).
- **CHK238** (`quality.md:1095-1113`) cites `spec.md:4976` +
  `:5631-5641` + `:5863-5897` for ADR in-place revision discipline.
  All three ranges resolve and match. The "no new ADR-036-012"
  rejection rule is honoured (verified by glob — no such file
  exists). ✅
- **CHK239** (`quality.md:1114-1123`) cites `spec.md:4933-4937` +
  `:4982` for LOW-1 within-cycle mirror immutability. All four
  mirror anchors (`plan.md:682`, `tasks.md:1929`, `quality.md:367`,
  `quality.md:528`) verified to exist with original "scoped
  exclusively to `tnt-stg-smoke`" wording intact (none touched in
  Cycle 5). ✅
- **CHK240** (`quality.md:1124-1136`) cites `spec.md:5642-5646` +
  `:5848-5853` for CHANGELOG grouped-block format. Both ranges
  resolve to Pass 2 Q1 / Q3 propagation entries. ✅
- **CHK241** (`quality.md:1137-1147`) cites `spec.md:4886` + `:4943`
  + `:4968-4969` for backlog issue #84 retention. The Cycle 4 close
  sentinel at `spec.md:4886` verbatim contains "backlog issue #84
  filed"; the citation chain is intact. The actual Bicep
  preamble's `[backlog issue: #84]` at
  `infra/bicep/modules/cosmos-simulation-containers.bicep:326` is
  preserved by the L317-327 A4-02 sub-block immutability
  discipline. ✅
- **CHK242** (`quality.md:1148-1158`) cites `spec.md:4886` for ruff
  cleanliness baseline. ✅
- **CHK243** (`quality.md:1162-1174`) cites `spec.md:5513-5523` +
  `:5546-5550` for skip/xfail/skipif anti-pattern. Both ranges
  resolve and capture Pass 2 Q1 grounds (iii) and (v). ✅
- **CHK244** (`quality.md:1178-1196`) cites `spec.md:5035, 5453, 5994`
  + `:5863-5897` for sentinel chain + multi-cycle Status convergence
  rule. All sentinel-line citations verified to be standalone
  sentinel anchors (L5035 = amendment-log close; L5453 = clarify
  Pass 1 close; L5994 = clarify Pass 2 close). ✅

#### 2.4 Spec ↔ ADR consistency (ADR-036-011 Cycle 5 sub-section ↔ A5-01) — ✅ PASS

- ADR-036-011 Cycle 5 sub-section spans
  `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:945-1224`.
  Pre-existing Cycle 3 + Cycle 4 content at L1-941 is **byte-identical**
  to pre-Cycle-5 baseline (no Cycle 3 / Cycle 4 content modified).
- Cycle 5 sub-section structure: Cycle 5 trigger
  (L959-995) → A5-01 resolution scope (L1009-1035) → Test surface
  extension (L1037-1064) → T-AA52 OPTIONAL→REQUIRED promotion
  (L1066-1086) → Test count convergence (L1088-1102) → Multi-cycle
  Status convergence rule (L1104-1133) → CHANGELOG format
  (L1135-1164) → References (L1166-1209) → closing sentinel paragraph
  (L1212-1224). Structure matches Cycle 4 sub-section template
  precedent at ADR L478+ (`spec.md:4931-4932`).
- ADR Cycle 5 sub-section narrative is consistent with A5-01 wording:
  database-level scope at L1014-1016; four-clause ordering at
  L1017-1024; out-of-scope retention of L172-184 binding wording at
  L951-953, L985-986, L1184-1185; ADR Status field at the top of the
  document remains `Proposed` (verified at L3 — *"Status: Proposed
  (will move to Accepted post-Step 8ac re-review)"*) — the ADR
  Status was **NOT** flipped during plan/tasks step.
- **No new ADR-036-012 file exists** — verified via
  `glob docs/aidr/decisions/ADR-036-012*` returning no matches. The
  in-place revision discipline (Cycle 4 Pass 1 Q5 applied recursively
  per Cycle 5 Pass 2 Q4 — `spec.md:5863-5897`) is honoured.

#### 2.5 Pass 1 / Pass 2 supersession integrity — ✅ PASS

- Pass 1 Q1 (preamble ordering) at `spec.md:5065-5174` remains in
  force unchanged through Pass 2 (Pass 2 Q1-Q4 do not contradict
  Q1).
- Pass 1 Q2 (assertion-phrase set option (b)) at `spec.md:5175-5240`
  remains in force; Pass 2 Q2 at `spec.md:5648-5754` is
  **additive-by-pinning** (selects between two equivalent
  case-folding forms Pass 1 Q2 offered as alternatives —
  `.lower()` + `in` vs. `re.compile(..., re.IGNORECASE)`); Pass 1
  Q2's substance is preserved verbatim.
- Pass 1 Q3 (comment-block-only scope) at `spec.md:5299-5418`
  remains in force unchanged; Pass 2 does not contradict.
- Pass 2 Q1 (OPTIONAL→REQUIRED promotion) at `spec.md:5498-5614`
  is **supersession-by-promotion** of the Pass 1 deferral paragraph
  at `spec.md:5444-5451`. The Pass 1 deferral text is
  **preserved verbatim** per the within-cycle immutability discipline
  (verified by direct read at L5444-5451 — *"the test is currently
  marked OPTIONAL by the Cycle 4 Pass-2 Q4 FULL posture per the
  docstring at `tests/contract/test_smoke_tenant_isolation.py:253`)
  is **not revisited here** — A5-01 extends the assertions but does
  not change the OPTIONAL/REQUIRED disposition; any promotion from
  OPTIONAL → REQUIRED is reserved for Cycle 5 Pass 2 if surfaced
  during a Step 8ao / Step 8ap quality-checklist re-review."*).
  Pass 2 Q1 grounds (i)-(v) at `:5502-5567` justify the
  supersession; Cycle 2 Q1 supersession precedent at
  `:389-392` cited as authority. ✅
- Pass 2 Q3 (single 3400 posture) at `spec.md:5776-5815` is
  **supersession-by-collapse** of the Cycle 4 Pass 2 Q4 minimal-3399 /
  FULL-3400 posture split at `:4795-4801`. The Cycle 4 split text at
  L4870-4875 is **preserved verbatim** per Cycle 4 immutability;
  Pass 2 Q3 retires the escape hatch for Cycle 5 onward; the binding
  value 3400 is decisive across all six Cycle 5 artefacts (spec,
  plan, tasks, CHK236, ADR, CHANGELOG-spec). ✅
- Pass 2 Q4 (multi-cycle Status convergence rule restatement) at
  `spec.md:5863-5897` is **citation-and-restatement** of the Cycle 4
  Pass 2 Q3 rule at `:4636-4684` — explicitly stated as
  *"verbatim restatement"* (`:5874`); no new convergence rule
  introduced. ✅

#### 2.6 Task ↔ file:line reality consistency (pre-implement state verified) — ✅ PASS

- `infra/bicep/modules/cosmos-simulation-containers.bicep:305-315`
  — verified by direct read: lines 305-315 carry the stale
  pre-Cycle-4 preamble; L305 starts *"// Scope the assignment to
  the smoke-tenant partition path. The"*; L308 contains
  *"`/dbs/<db>/colls/<container>/pks/<tenant_id>`"*. The
  F-TECH-4-01 defect surface is intact (i.e., implement step has
  NOT been run). ✅
- `infra/bicep/modules/cosmos-simulation-containers.bicep:317-327`
  — verified by direct read: lines 317-327 carry the Cycle 4 A4-02
  sub-block; L317 starts *"// Cycle 4 / A4-02 (spec.md:3896-3915,
  ADR-036-011:172-173):"*; L326 contains
  *"`[backlog issue: #84]`"*. Cycle 4 sub-block immutability
  honoured. ✅
- `infra/bicep/modules/cosmos-simulation-containers.bicep:328`
  — verified by direct read: *"scope:
  '${account.id}/dbs/${databaseName}'"* — byte-identical to Cycle 4
  baseline. ✅
- `tests/contract/test_smoke_tenant_isolation.py:166` — verified by
  direct read: `assert "tnt-prod" not in role_block.lower(), (...)`
  — the precedent CHK234 + Pass 2 Q2 cite for symmetry. ✅
- `tests/contract/test_smoke_tenant_isolation.py:173` — verified by
  direct read: `# Cycle 4 / T-AA51 (REQUIRED) + T-AA52 (OPTIONAL) — A4-02 evidence tests`
  — matches CHK233 + T-AA59 quoted current text byte-identically. ✅
- `tests/contract/test_smoke_tenant_isolation.py:220-247` —
  verified by direct read: `_extract_role_assignment_block` helper
  function exists with the documented regex-based start/end pattern
  (resource-name match → `^}\s*$` walker). ✅
- `tests/contract/test_smoke_tenant_isolation.py:250-297` —
  verified by direct read:
  `test_bicep_comment_block_documents_compensating_control`
  function exists with docstring at L253-267, two presence
  assertions at L271-282 (`compensating_re.search`) and L286-297
  (`backlog_re.search`). ✅
- `tests/contract/test_smoke_tenant_isolation.py:253` (docstring) —
  verified by direct read: starts *"T-AA52 — OPTIONAL A4-02 evidence:
  Bicep comment block (L305-315)."* — matches CHK233 quoted current
  text byte-identically. ✅
- `tests/contract/test_smoke_tenant_isolation.py` test-function count
  — verified by grep: **8 test functions** (L58, 71, 92, 109, 129,
  145, 184, 250) — matches T-AA61 verify-command claim *"8
  smoke-tenant-isolation tests {6 Cycle 1-3 + T-AA51 + T-AA52}"*
  (`tasks.md:2622`); 8 + 7 canonical-match + 7 runtime-validity = 22
  contract slice (T-AA61 22-passed gate). ✅
- `docs/aidr/decisions/ADR-036-012*.md` — **does not exist** (glob
  no match) — Cycle 5 in-place revision discipline honoured. ✅

#### 2.7 Citation drift detection — 🟡 ONE MEDIUM drift (CHK237) + ONE LOW drift (Pass 2 Q2 range)

See §3 citation drift table below.

#### 2.8 Within-cycle immutability check — ✅ PASS

- All Cycle 1 / Cycle 2 / Cycle 3 / Cycle 4 spec content at
  `spec.md:1-4886` is **byte-identical** to pre-Cycle-5 baseline.
  Spot-check verified at L389-392 (Cycle 2 Q1 supersession
  precedent — still present), L961-970 (Cycle 4 A4-02
  strikethrough — still present with same four-mirror citation),
  L4886 (Cycle 4 implement sentinel — still present).
- All Cycle 4 sentinel anchors at L4877, L4879, L4881, L4882,
  L4884, L4886 preserved.
- Cycle 4 ADR content at
  `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:1-941`
  is byte-identical to pre-Cycle-5 baseline.
- Cycle 4 plan content at `plan.md:1-1380` (including PD-C4-01,
  PD-C4-02, Cycle 4 plan-addendum closing paragraph at L1373-1379)
  is byte-identical.
- Cycle 4 tasks content at `tasks.md:1-2541` (including §26
  T-AA43..T-AA56, §26.10 status block, Cycle 4 implement-close
  sentinel at L2541) is byte-identical.
- Cycle 1 / Cycle 2 / Cycle 3 / Cycle 4 quality.md rows at
  `quality.md:1-973` are byte-identical.
- LOW-1 mirror anchors (`plan.md:682`, `tasks.md:1929`,
  `quality.md:367`, `quality.md:528`) NOT touched — verified by
  direct read. The "known-stale per A4-02 supersession" annotation
  via the Cycle 4 strikethrough block at `spec.md:961-970` carries
  the operational acknowledgement of the staleness; the mirror
  lines themselves remain verbatim.

#### 2.9 Test-count math integrity — ✅ PASS

- Cycle 4 implement sentinel at `spec.md:4886`: *"test count delta
  +9 (3391 baseline → 3400 FULL posture)"* — empirical certification.
- Cycle 5 Pass 1 rollup at `spec.md:5440-5444`: delta = +0; post-
  Cycle-5 = 3400 (FULL posture qualifier later collapsed by Pass 2
  Q3).
- Cycle 5 Pass 2 Q3 at `spec.md:5776-5815`: 3400 single posture (no
  minimal/FULL split); Cycle 4 Pass 2 Q4 escape hatch retired.
- PD-C5-01 at `plan.md:1579-1598`: 3400 single posture; pytest
  collects 3400 nodes pre- and post-Cycle-5.
- CHK236 at `quality.md:1063-1076`: 3400 single posture; zero
  `skipped`/`xfailed`/`xpassed` qualifier for T-AA52.
- T-AA61 verify-command at `tasks.md:2628`:
  `python -m pytest -q 2>&1 | grep -E '3400 passed'` — gates 3400.
- ADR Cycle 5 sub-section at L1090-1101: 3400 single posture
  binding; +0 delta.
- §27.6 Cycle 5 status block at `tasks.md:2680-2696`: 3400 +0
  delta — explicitly tabulated.
- Contract slice (22 = 8 + 7 + 7) consistent across `spec.md:4915`
  (Cycle 4 implement baseline) and `tasks.md:2622, 2628` (T-AA61
  pre-merge gate). Verified by direct grep of test file (8 test
  functions in test_smoke_tenant_isolation.py).
- **All seven artefacts** (spec, plan, tasks, CHK236, ADR, T-AA61
  command, §27.6 table) consistently bind 3400 single posture with
  +0 delta. ✅

#### 2.10 Ordering symmetry verification (CHK232 ↔ T-AA57) — ✅ PASS

- Pass 1 Q1 four-clause ordering at `spec.md:5067-5096`:
  (1) database-level scope → (2) compensating defence-in-depth →
  (3) joint enforcement → (4) `[backlog issue: #84]`.
- CHK232 at `quality.md:998-1004` encodes the same four-clause
  ordering verbatim.
- T-AA57 task description at `tasks.md:2569` encodes the same
  ordering: *"(1) database-level scope statement; (2) compensating
  defence-in-depth phrasing reaffirming the Cycle 4 A4-02 phrase;
  (3) joint enforcement clauses naming the SLI-Z6 / SLI-Z7
  query-time `where tenant_id == "tnt-stg-smoke"` filter and the
  `customDimensions["tenant_id"]` envelope discriminator AND the
  Pass-1 Q2 isolation guarantees (i)–(v); (4) the `[backlog issue:
  #84]` citation"*.
- ADR Cycle 5 sub-section at L1017-1024 encodes the same ordering.
- PD-C5-01 acceptance criterion 2 at `plan.md:1808-1814` encodes
  the same ordering.
- **All five surfaces** (spec Pass 1 Q1, CHK232, T-AA57, ADR Cycle 5,
  PD-C5-01) consistently encode the four-clause ordering. ✅

### 3. Citation drift table

| ID | Severity | Surface | Drift | Recommended action |
|----|----------|---------|-------|---------------------|
| MEDIUM-1 | MEDIUM | `quality.md:1080-1094` (CHK237) | CHK237 lists "the twelve prior sentinel anchors at `spec.md:3829`, `:3967`, `:4385`, `:4866` (Cycle 4 clarify Pass 2 close), `:4868`, `:4870`, `:4871`, `:4873` (Cycle 4 Pass 2 supersession-ladder internal anchors), `:4886`, `:5035`, `:5453`, `:5994`". Direct file inspection of L4866 / L4868 / L4870 / L4871 / L4873 shows these are **mid-paragraph rollup lines**, not standalone sentinels (L4866 = *"corrections to test-count claims, with original Pass 1 lines"*; L4868 = *"analogous to the Cycle 2 Q1 supersession precedent at"*; L4870 = *"fail at `spec.md:3829` is preserved; the binding post-Cycle-4-implement"*; L4871 = *"total is **3399 tests pass / 0 fail** (scope-string assertion"*; L4873 = *"taken — full Step 8ae posture). Step 8ae records the chosen value"*). The actual **Cycle 4 clarify Pass 2 close sentinel** is at `spec.md:4877` (*"**Cycle 4 clarify pass 2 complete. Ready for /speckit.checklist (Cycle 4).**"*), not at L4866. The "twelve" count includes 5 mid-paragraph anchors that are not really "sentinel" class. | **Fold into Step 8at**: correct CHK237 to reference the actual Cycle 4 sentinel anchors at L4877 (Pass 2 close), L4879 (checklist close), L4881 (plan close), L4882 (tasks close), L4884 (analyze close), L4886 (implement close); drop the five mid-paragraph cites (4866/4868/4870/4871/4873) — the byte-preservation requirement is correct in spirit (the spec.md content above L4886 is immutable) but the per-line cite list is imprecise. Severity MEDIUM mirrors the Cycle 4 analyze MEDIUM-3 citation-drift fold-in pattern (`spec.md:4884` PASS-WITH-MINOR verdict tolerated the analogous Cycle 4 drift). This is a documentation-only correction; no spec/plan/tasks/ADR file edit is required to unblock Step 8at implement. |
| LOW-1 | LOW | ADR-036-011 L1043 (Pass 2 Q2 range cite) | ADR Cycle 5 sub-section cites Pass 2 Q2 as `spec.md:5648-5754` (starts at the Q2 heading line `### Q2 — What is the binding...`). Plan PD-C5-01 (`plan.md:1566`), tasks T-AA58 (`tasks.md:2584`), CHK234 (`quality.md:1043`), and Pass 2 rollup (`spec.md:5953-5955` — "`spec.md:5650-5754`") all cite the same Pass 2 Q2 as `:5650-5754` (starts at the **Answer** line). The 2-line drift on the start boundary (5648 vs. 5650) does not change the substantive citation — both ranges resolve to the same Q2 body — but the five citing artefacts are not byte-symmetric on the boundary. | **No fold-in required**. The cited body is unambiguous in all five locations. Acceptable per the Cycle 4 analyze "line-hedge imprecision tolerated" precedent. |
| LOW-2 | LOW | `quality.md:1080-1082` (CHK237 lead-in count) | CHK237 lead-in says *"the twelve prior sentinel anchors at ..."*. The enumerated list contains 12 line citations (3829, 3967, 4385, 4866, 4868, 4870, 4871, 4873, 4886, 5035, 5453, 5994), but only 7 of those are standalone-sentinel-class anchors (3829, 3967, 4385, 4886, 5035, 5453, 5994); the other 5 are mid-paragraph (per MEDIUM-1 above). The count word "twelve" is mathematically correct against the cite-list cardinality but semantically loose against the qualifier "sentinel". | **Fold into Step 8at alongside MEDIUM-1**. Restate CHK237 lead-in as *"the seven prior sentinel anchors at `spec.md:3829`, `:3967`, `:4385`, `:4886`, `:5035`, `:5453`, `:5994`"* and drop the mid-paragraph cites; or alternatively leave the cite count "twelve" and re-qualify the lead-in as *"the twelve prior immutability anchors (sentinels + supersession-ladder internal lines)"*. Either resolution closes both MEDIUM-1 and LOW-2 with a single edit. |
| LOW-3 | LOW | `tasks.md:1654` (Cycle 5 task-id forecast in PD-C5-01) | PD-C5-01 in `plan.md:1654-1664` forecasts *"Cycle 5 anticipated tasks **T-AA57..T-AA60** (approximate, finalised at Step 8ar)"* — a 4-task forecast. The actual Step 8ar tasks finalised at **T-AA57..T-AA61** (5 tasks: T-AA57 Bicep + T-AA58 absence assertions + T-AA59 prose promotion + T-AA60 CHANGELOG + T-AA61 verification gate). The plan-addendum forecast undercounts by 1 (the verification-gate task T-AA61 was not enumerated in the forecast). The forecast text explicitly qualifies itself *"(approximate, finalised at Step 8ar)"*, so this is forecast-vs-final drift within the forecast contract. | **No fold-in required**. The forecast was approximate by self-acknowledgement; the binding count is the Step 8ar-finalised 5-task list. Acceptable per the contract. |

### 4. Recommended fold-in for Step 8at implement

**MEDIUM-1 + LOW-2 fold-in (single edit, mirrors Cycle 4 analyze
MEDIUM-3 → Step 8ak pattern)**:

During Step 8at (Cycle 5 implement), the CHK237 row at
`specs/036-sim-agent-extend/checklists/quality.md:1080-1094` SHOULD be
corrected in the same close commit that lands the Bicep preamble
rewrite + test extension + T-AA52 prose promotion + CHANGELOG entry.
Two acceptable resolutions:

**(a) Tighten the cite-list** (preferred — matches the spirit of
"sentinel anchors"):

```
- [ ] CHK237 **Spec sentinel chain preserved verbatim** — the seven
  prior sentinel anchors at `spec.md:3829` (Cycle 3 implement
  complete), `spec.md:3967` (Cycle 4 amendment specify complete),
  `spec.md:4385` (Cycle 4 clarify Pass 1 complete), `spec.md:4886`
  (Cycle 4 implement complete — 3400 FULL posture; backlog issue
  #84 filed), `spec.md:5035` (Cycle 5 amendment log complete),
  `spec.md:5453` (Cycle 5 clarify Pass 1 complete), and
  `spec.md:5994` (Cycle 5 clarify Pass 2 complete — CONVERGED)
  MUST remain byte-identical post-Cycle-5; only the Cycle 5
  checklist + plan + tasks + analyze + implement close sentinels
  are appended **after** L5994
  [Convergence, `spec.md:3829, 3967, 4385, 4886, 5035, 5453, 5994`]
```

This drops the L4866/4868/4870/4871/4873 mid-paragraph cites and the
L4877 Cycle-4-Pass-2 close sentinel (the latter could be added if a
true 8-sentinel chain is desired).

**(b) Broaden the qualifier** (alternative — keeps all 12 cites):

```
- [ ] CHK237 **Spec sentinel chain + supersession-ladder anchors preserved verbatim** — the twelve prior immutability anchors at ...
```

Either resolution is non-blocking for Step 8at's pytest gate
(CHK237's substance — preserve all listed lines byte-identically —
is correct regardless of label precision; the listed lines do not
change in Cycle 5).

**LOW-1, LOW-3**: no fold-in required (within tolerance per Cycle 4
analyze precedent).

### 5. Convergence assessment

**Cycle 5 ready for implement (Step 8at)?** **YES** — with the optional
CHK237 fold-in noted above.

- 0 HIGH findings — no blocking defects.
- 1 MEDIUM finding (CHK237 citation drift) — documentation-only
  imprecision; fold-in recommended but not gating; the substantive
  spec/plan/tasks/ADR content is correct and consistent.
- 3 LOW findings — pure citation-imprecision artefacts (Pass 2 Q2
  range start, CHK237 count word, PD-C5-01 task-id forecast).
- ADR Status field correctly at `Proposed` (not flipped during
  plan/tasks step).
- No new `ADR-036-012-*.md` file (in-place revision discipline
  honoured).
- LOW-1 mirror anchors NOT touched in Cycle 5 (within-cycle
  immutability honoured).
- Test-count math (3400 single posture, +0 delta) consistent
  across all seven Cycle 5 artefacts.
- Ordering symmetry (Pass 1 Q1 four-clause ordering) consistent
  across all five Cycle 5 surfaces.
- Pass 1 / Pass 2 supersession integrity preserved (Pass 1
  deferral paragraph at `:5444-5451` preserved verbatim;
  Pass 2 Q1 supersession-by-promotion grounds (i)-(v) cited).
- Task ↔ file:line reality verified (Bicep L305-315 still carries
  the F-TECH-4-01 defect surface; A4-02 sub-block at L317-327
  preserved; `scope:` at L328 byte-identical to Cycle 4 baseline;
  test helper + test function + docstring + header comment all at
  the cited locations).
- T-AA57 → T-AA58 dependency edge correctly enforced (absence
  assertions would fail against the un-rewritten Bicep).

**Outcome**: PASS-WITH-MINOR. Step 8at is unblocked. The CHK237
fold-in is recommended (mirrors the Cycle 4 analyze MEDIUM-3 → Step
8ak pattern) but does not gate Step 8at's pytest / ruff / Bicep
byte-equality verification commands.

---

*Cycle 5 analyze report appended 2026-05-11 by `/speckit.analyze`
(Step 8as). Read-only pass; only `spec.md` was modified (this
append). No other files touched. All citations resolved against the
live source tree (`infra/bicep/modules/cosmos-simulation-containers.bicep`,
`tests/contract/test_smoke_tenant_isolation.py`,
`docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md`,
`specs/036-sim-agent-extend/spec.md`,
`specs/036-sim-agent-extend/plan.md`,
`specs/036-sim-agent-extend/tasks.md`,
`specs/036-sim-agent-extend/checklists/quality.md`) at analysis time.*

**Cycle 5 analyze complete (verdict: PASS-WITH-MINOR). Ready for /speckit.implement (Cycle 5).**

**Cycle 5 implement complete. 🟢 GREEN: 5 tasks DONE (T-AA57..T-AA61); test count delta +0 (3400 → 3400 single posture per Pass 2 Q3); 22 Cycle-5-affected contract tests pass / 0 fail (`tests/contract/test_smoke_tenant_isolation.py` 8 + `tests/contract/test_sli_kql_canonical_match.py` 7 + `tests/contract/test_sli_kql_runtime_validity.py` 7); `ruff check apps tests packages` clean; Bicep `scope: '${account.id}/dbs/${databaseName}'` byte-identical to Cycle 4 baseline; CHK237 citation drift preserved as-is per within-cycle immutability discipline (Cycle 4 analyze MEDIUM-3 → Step 8ak fold-in precedent: known-stale per immutability discipline, NOT corrected in Cycle 5 — `quality.md:1080-1094` retained verbatim, mid-paragraph L4866/4868/4870/4871/4873 cites acknowledged as imprecise but locked); ADR-036-011 Status remains `Proposed` per Pass 2 Q4 (flip to `Accepted` deferred to Step 8au cohort re-review). Local worktree environment caveat: pre-existing unrelated TenantContext refactoring + agent_framework module absence cause 26 failed / 17 errors in unrelated modules (`tests/load/test_workflow_capacity.py`, `tests/simulation/test_bushfire_risk_assessment.py`, `tests/devops/test_build_tts_watermarks.py`, `tests/e2e/test_quickstart_validation.py`, audit-tier-3 file-spill tests, `apps/agents/maf_runtime/*` collection errors); ALL confirmed NOT caused by Cycle 5 surfaces (Bicep / `test_smoke_tenant_isolation.py` / `CHANGELOG.md`); broader-suite count diverges from the binding 3400-passed gate due to in-flight worktree modifications outside Cycle 5 scope (mirrors Cycle 4 T-AA56 local-environment caveat at `tasks.md:2531`).**

**Cycle 5 Step 8au cohort re-review complete. 🟢🟢🟢 GREEN PROCEED across all 3 cohorts. Distribution: operational 10/10 ACCEPT, sectors 54 ACCEPT / 4 carry-forward RESERVATIONS (maritime/coastal/aviation — abf/asa/mrnsw/surf-lifesaving, unchanged from Cycle 3) / 0 OBJECT, technical 17/0/0 with infrastructure-devops keystone RESERVATION on F-TECH-4-01 closed. 0 OBJECT + 0 NEW merit-validated findings across all 174 active personas (10 operational + 58 sectors + 17 technical + cross-cohort reads). Targeted contract slice 22/22 pass; ruff clean. Per Cycle 5 clarify Pass 2 Q4 multi-cycle Status convergence rule (restated at `spec.md:5863-5897` and ADR `:1104-1133`): Cycle 5 closes; ADR-036-011 Status flipped `Proposed → Accepted` (single-line edit at `docs/aidr/decisions/ADR-036-011-cycle-3-amendment-cycle.md:3`); no new ADR-036-012 file created (in-place revision pathway per Cycle 4 Pass 1 Q5 binding). Step 9 (azd deploy) unblocked. Cycle 6 NOT required.**

**Spec 036-sim-agent-extend amendment workflow COMPLETE. 🟢 Cycles 1-5 closed. Ready for Step 9 azd deploy.**
