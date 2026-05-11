# Specification Quality Checklist: Real Sub-Agent Invocation & Simulation Telemetry-Injection Agent

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-05-08
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Items marked incomplete require spec updates before `/speckit.clarify` or `/speckit.plan`.
- Validation iterations performed: 4 (initial draft + 2026-05-08 pass-1 clarifications + 2026-05-08 pass-2 clarifications + 2026-05-08 pass-3 checklist-surfaced clarifications).
- Pointers to specific spec sections that satisfy each criterion are listed below.

### Validation evidence (iteration 1)

| Criterion | Evidence |
|---|---|
| No implementation details | Spec describes *what* (sub-agent invocation, typed signals, map overlays, `[SIMULATION] ` prefix) and *why* (capstone outcomes, AIIMS cohort asks). The only file/path reference is `apps/api/app/services/simulation/sub_agent_invoker.py`, included intentionally as the migration target named in the user input — it is the *what changes*, not a *how-to-implement*. |
| Focused on user value and business needs | Each user story leads with the coordinator's exercise outcome and the capstone target it advances. |
| Written for non-technical stakeholders | Acceptance scenarios use Given/When/Then; jargon (FFDI, FDR, AWS, AIIMS, COMDISPLAN, NEMA, etc.) is domain-standard for the operational audience. |
| All mandatory sections completed | Overview, Cohort table, Assumptions, User Scenarios & Testing, Edge Cases, Functional Requirements, Key Entities, Success Criteria — all present. |
| No [NEEDS CLARIFICATION] markers remain | Verified by `grep "NEEDS CLARIFICATION" spec.md` returning no matches. Reasonable defaults documented in Assumptions A1–A10. |
| Requirements are testable and unambiguous | Every FR uses MUST / MUST NOT, names the actor and observable behaviour, and is paired with at least one acceptance scenario or success criterion. |
| Success criteria are measurable | SC-001 through SC-012 each declare a quantitative threshold (≥ 95 %, ≤ 50 %, ≥ 80 %, ≥ 30 %, etc.) and a sample size or measurement window. |
| Success criteria are technology-agnostic | SCs describe coordinator-observable outcomes (lead time, evacuation timing, reallocation count, false-positive count, audit-entry coverage) without naming frameworks, models, or storage technologies. |
| All acceptance scenarios are defined | All 9 user stories have ≥ 3 acceptance scenarios in Given/When/Then form. |
| Edge cases are identified | 16 edge cases listed; cover unparseable input, contradictions, PII, isolation breaches, multi-coordinator conflicts, real Level-3 throttle, observer permission breach, map overflow, role/combat tagging breaches. |
| Scope is clearly bounded | Out-of-scope is explicit: time-warp/playback (spec 026), tenant provisioning (spec 007), map base-layer config (spec 020), real-world publication (Constitution). |
| Dependencies and assumptions identified | Assumptions A1–A10 declared; spec 024 inheritance noted on each carried-forward assumption; spec 020/026/007/028 dependencies named. |
| All functional requirements have clear acceptance criteria | FR-001..FR-056 are each either directly mirrored by an acceptance scenario in stories 1–9 or operationalised by SC-006..SC-012. |
| User scenarios cover primary flows | P1 stories cover the four explicit user asks (real sub-agents, telemetry injection, auto-routing, map updates, `[SIMULATION] ` receipt). P2/P3 cover multi-hazard concurrency, cascading signals, degraded-mode, and lessons capture. |
| Feature meets measurable outcomes defined in Success Criteria | Every capstone target is mapped to at least one SC (SC-002 → 50 % response-time, SC-003 → 24-h-earlier evacuation, SC-004 → 30 % resource efficiency, SC-005 → 30 % economic-loss reduction, SC-006 → constitutional comms-block underpinning the lives-saved goal). |
| No implementation details leak into specification | No language, framework, library, database, or model is named in any FR (the spec-024 stub-file path appears only as the migration target referenced by the user). |

### Validation evidence (iteration 2 — 2026-05-08 pass 1 clarifications)

`/speckit.clarify` pass 1 surfaced and resolved 5 questions; spec was updated surgically.
Re-validation against the same criteria:

| Criterion | Pass | Evidence |
|---|---|---|
| No implementation details | ✅ | New text in FR-008 / FR-010 / FR-015 / FR-021 / FR-039 / FR-052 / FR-057 and A11 stays at the *what / why* level (signal categories, inference-ladder steps, watermark policy, audit-entry types). No new framework, library, or model named. |
| Focused on user value | ✅ | Each clarification ties back to a coordinator-observable outcome (predictable cap behaviour, watermark trustworthiness in CALD locales, life-safety confidence gate, deterministic jurisdiction routing, single audit envelope). |
| Written for non-technical stakeholders | ✅ | New scenarios use Given / When / Then; new audit-entry type names (`thread.cap_exceeded`, `cascade.degraded_to_annotation`, `routing.jurisdiction_ambiguous`, `audit.watermark.locale_missing`, `injection.refused` reason `life_safety_low_confidence`) are surfaced as content not implementation. |
| All mandatory sections completed | ✅ | New `## Clarifications` section added between `## Overview` and `## User Scenarios & Testing`, containing `### Session 2026-05-08 (pass 1)` with 5 Q→A bullets. |
| No [NEEDS CLARIFICATION] markers remain | ✅ | Verified — `grep "NEEDS CLARIFICATION" spec.md` returns 0 matches. Every clarification answer is decisive. |
| Requirements are testable and unambiguous | ✅ | FR-010 hybrid threshold lists exact category sets; FR-021 ladder is enumerated with deterministic stop conditions and an `jurisdiction_inference_step` audit field; FR-039 bilingual rule is byte-for-byte testable; FR-052 hard-cap and FR-057 cascade-degradation rule each name the typed audit entry produced. |
| Success criteria are measurable | ✅ | SC-001..SC-012 unchanged; SC-006 (zero false positives) is reinforced by FR-039 bilingual rule (literal English byte match); SC-011 (no thread collapse) is reinforced by FR-052 / FR-057 (cap enforced at thread creation, not by collapsing). |
| Success criteria are technology-agnostic | ✅ | SCs unchanged. |
| All acceptance scenarios are defined | ✅ | New scenarios added: US1 #5 (sequential placement), US2 #6 + #7 (life-safety vs non-life-safety low-confidence), US4 #7 + #8 (jurisdiction inference ladder), US5 #6 + #7 (bilingual watermark + locale-missing fallback), US6 #5 + #6 (cap-exceedance refusal + cascade degradation). |
| Edge cases are identified | ✅ | Edge case count grew from 16 → 18 with 3 new cases (life-safety low confidence, 6th-thread cap exceedance, multi-jurisdiction inference ladder). The grep-bullet count of 18 reflects that the prior count of 16 in iteration-1 evidence was approximate (actual pre-clarification was 15 distinct cases); the new 3 additions are itemised in the spec's Edge Cases section. |
| Scope is clearly bounded | ✅ | No scope changes. Out-of-scope and spec-007 / 020 / 024 / 026 / 028 dependencies still explicit. |
| Dependencies and assumptions identified | ✅ | A11 added (watermark translation-table policy under spec-024 governance). A10 extended with cap-exceedance rule and the spec-007 FR-010 split-into-parallel-sims escape hatch. |
| All functional requirements have clear acceptance criteria | ✅ | FR-057 mirrored by US6 scenario #6; FR-021 inference ladder mirrored by US4 scenarios #7 + #8; FR-010 hybrid mirrored by US2 scenarios #6 + #7; FR-039 bilingual mirrored by US5 scenarios #6 + #7; FR-008 / FR-015 sequential placement mirrored by US1 scenario #5. |
| User scenarios cover primary flows | ✅ | No story removed or down-prioritised; P1 stories now have 5–8 acceptance scenarios each. |
| Feature meets measurable outcomes defined in Success Criteria | ✅ | SC-006 strengthened by FR-039 (literal English byte match guaranteed); SC-011 strengthened by FR-052 / FR-057 (cap enforced at thread creation). |
| No implementation details leak into specification | ✅ | Verified across all 6 edited FRs and 2 assumption changes — only audit-entry type names, signal categories, and cohort-language references are added. |

**Result**: All 16 checklist items pass for iteration 2.

### Iteration 2 — final counts

- Functional requirements: **57** (FR-001..FR-056 from iteration 1 + FR-057 new for cascade-degradation; FR-057 placed in the Multi-hazard concurrency subsection adjacent to FR-052 / FR-053 to keep the topical grouping intact).
- Success criteria: **12** (SC-001..SC-012, unchanged).
- Edge cases: **18** (15 carried + 3 new — life-safety low-confidence parse, 6th-thread cap exceedance, multi-jurisdiction no-explicit-jurisdiction inference ladder).
- Assumptions: **11** (A1..A10 + new A11 for watermark translation-table policy; A10 extended with cap-exceedance rule).
- Clarifications: **5** Q→A entries dated `Session 2026-05-08 (pass 1)`.

### Validation evidence (iteration 3 — 2026-05-08 pass 2 clarifications)

`/speckit.clarify` pass 2 surfaced and resolved 5 additional questions; spec was updated surgically.
Re-validation against the same criteria:

| Criterion | Pass | Evidence |
|---|---|---|
| No implementation details | ✅ | New text in FR-009 / FR-021 / FR-039 / FR-054 / FR-057 / FR-058 and A11 stays at the *what / why* level (audit-entry tag names, deterministic affinity ladder, audio-prefix-table policy, advisory-vs-server-revalidation contract, parse-attempt circuit-breaker hand-off). No new framework, library, model, or storage technology named — even the ABS-SA fallback is named as a *boundary dataset*, not an implementation. |
| Focused on user value | ✅ | Each pass-2 clarification ties back to a coordinator-observable outcome: CALD audio listeners hear a trustworthy bilingual prefix (Q1); SC-011 reproducibility is preserved across exercise replays (Q2); FR-054 lessons capture stays single-walk per thread (Q3); routing cannot be steered by a buggy or hostile client (Q4); the FR-010 clarification loop and FR-052 cap-refusals do not penalise coordinators under exercise pressure (Q5). |
| Written for non-technical stakeholders | ✅ | New scenarios use Given / When / Then; new audit-entry types (`audit.watermark.locale_missing` (audio variant), `routing.viewport_hint_mismatch`, `cascade.degraded_to_annotation` with `affinity_step`, `origin_cascade_id` tag) are surfaced as content not implementation; the FR-057 ladder is described in plain numbered steps. |
| All mandatory sections completed | ✅ | New `### Session 2026-05-08 (pass 2)` sub-section added under the existing `## Clarifications` section, containing 5 Q→A bullets. No new top-level sections introduced. |
| No [NEEDS CLARIFICATION] markers remain | ✅ | Verified — 0 `NEEDS CLARIFICATION` matches across the spec (PowerShell regex sweep). All five pass-2 answers are decisive. |
| Requirements are testable and unambiguous | ✅ | FR-009 enumerates which events count toward the 30/min/user budget; FR-021 step 3 states the server-computed jurisdiction wins and names the audit entry; FR-039 narrows scope to text artefacts and references FR-058 for audio; FR-058 mirrors FR-039 byte-for-byte for the audio pathway with the same locale-missing fallback contract; FR-057 ladder is enumerated 1..5 with deterministic stop conditions and an `affinity_step` audit field; FR-054 names the single-walk audit-ownership contract. |
| Success criteria are measurable | ✅ | SC-001..SC-012 unchanged; SC-006 (zero false-positive deliveries) is reinforced by FR-058 (no LLM-generated TTS watermark fallback); SC-011 (no thread collapse + reproducible) is reinforced by FR-057's byte-deterministic affinity ladder. |
| Success criteria are technology-agnostic | ✅ | SCs unchanged. |
| All acceptance scenarios are defined | ✅ | New scenarios added: US4 #9 (viewport-hint mismatch — server-computed jurisdiction wins, `routing.viewport_hint_mismatch` written); US5 #8 (CALD audio listener bilingual spoken prefix) and US5 #9 (audio locale-missing fallback to English-only spoken prefix); US6 #7 (affinity tie-break — same jurisdiction + hazard-class + neither thread originated cascade → step-4 most-recent-mutation wins, byte-identical across replays). |
| Edge cases are identified | ✅ | Edge case count grew from 18 → 19 with 1 new case (buggy/malicious client floods parser with junk text — separate parse-attempt circuit-breaker, distinct from the success-counted injection budget). |
| Scope is clearly bounded | ✅ | No scope changes. Out-of-scope and spec-007 / 020 / 024 / 026 / 028 dependencies still explicit. The ABS-SA boundary fallback is named as the source-of-truth dataset; exact wiring is explicitly deferred to plan phase. |
| Dependencies and assumptions identified | ✅ | A11 extended to cover both text and audio bilingual artefacts (parallel `audio-prefix table` governed under the same spec-024 watermark-governance pathway). No new assumptions introduced. |
| All functional requirements have clear acceptance criteria | ✅ | FR-058 mirrored by US5 scenarios #8 + #9; FR-021 step-3 server-revalidation mirrored by US4 scenario #9; FR-057 deterministic ladder + audit-ownership model mirrored by US6 scenario #7; FR-009 rate-limit semantics mirrored by the new Edge Cases bullet on parser-flood and validated by FR-010 / FR-052 refusals not consuming budget; FR-054 single-walk reconstruction underpinned by FR-057's `origin_cascade_id` tagging. |
| User scenarios cover primary flows | ✅ | No story removed or down-prioritised. P1 stories (US1, US2, US3, US4, US5) and P2 stories (US6) all gained scenarios. US7..US9 unchanged. |
| Feature meets measurable outcomes defined in Success Criteria | ✅ | SC-006 strengthened by FR-058 (audio pathway closed against LLM-generated watermark drift); SC-011 strengthened by FR-057 byte-deterministic ladder (reproducible across exercise replays); SC-007 strengthened by FR-009 explicit budget semantics (refused injections still produce typed audit entries — never silently dropped — but do not consume budget). |
| No implementation details leak into specification | ✅ | Verified across all 7 edited FRs (FR-009, FR-021, FR-039, FR-054, FR-057, plus new FR-058) and the A11 extension — only audit-entry type names, dataset categories (jurisdiction registry, ABS-SA boundaries), policy contracts (server-revalidates, no-LLM, single-walk), and a planning hand-off note are added. The parse-attempt circuit-breaker threshold is stated as an *order-of-magnitude* hand-off (~60/min/user) with exact value explicitly deferred to plan phase. |

**Result**: All 16 checklist items pass for iteration 3.

### Iteration 3 — final counts

- Functional requirements: **58** (FR-001..FR-057 from iteration 2 + FR-058 new for bilingual TTS audio watermark; FR-058 placed in the Communication-agent section adjacent to FR-039 to keep the topical grouping intact).
- Success criteria: **12** (SC-001..SC-012, unchanged).
- Edge cases: **19** (18 carried + 1 new — buggy/malicious client floods the Telemetry-Injection parser with junk text; addressed by a separate parse-attempt circuit-breaker distinct from the FR-009 success-counted injection budget).
- Assumptions: **11** (A1..A11; A11 extended in iteration 3 to cover both text and audio bilingual watermark artefacts via a parallel version-controlled audio-prefix table).
- Clarifications: **10** Q→A entries total — 5 dated `Session 2026-05-08 (pass 1)` + 5 dated `Session 2026-05-08 (pass 2)`.

### Validation evidence (iteration 4 — 2026-05-08 pass 3 — checklist-surfaced)

`/speckit.checklist` generation surfaced 3 gaps that the calling agent had already answered with decisive, constitution-aligned, spec-024-inherited responses; those answers were integrated into the spec via this pass-3 clarification cycle (no new ambiguities; pure integration of pre-resolved decisions).
Re-validation against the same criteria:

| Criterion | Pass | Evidence |
|---|---|---|
| No implementation details | ✅ | New text in FR-005 / FR-043 / FR-057 (cascade-depth ceiling block) / FR-059 (lifecycle verbs) / FR-060 (`prompt_hash` capture) and the A12 assumption stays at the *what / why* level (cascade-depth invariant, lifecycle verb semantics, audit-fingerprint field). No new framework, library, model, or storage technology is named — `prompt_hash` is specified as "sha256 over the canonical prompt the sub-agent's LLM actually sees" and `controller_prompt.md` is referenced only as the spec-024 versioning precedent, not as an implementation file path. |
| Focused on user value | ✅ | Each pass-3 clarification ties back to a coordinator-observable outcome: bounded-cascade reproducibility for SC-011 replays (Q6); unambiguous coordinator override surface during exercise pressure (Q7); forensic replay verifiability for any LLM-bearing exercise (Q8 — Constitution IV). |
| Written for non-technical stakeholders | ✅ | New scenarios use Given / When / Then; new audit-entry tags (`lifecycle.paused`, `sub_agent.cancel`, the typed depth-2-refusal entry) are surfaced as content not implementation; FR-059's three lifecycle verbs (`pause`, `resume`, `abort`) are described in plain bullets. |
| All mandatory sections completed | ✅ | New `### Session 2026-05-08 (pass 3 — checklist-surfaced)` sub-section added under the existing `## Clarifications` section, containing 3 Q→A bullets. New `**Coordinator lifecycle controls (inherits spec 024 lifecycle implementation)**` subsection added between the existing Multi-hazard concurrency / degraded-mode subsection and the Post-exercise lessons capture subsection — heading hierarchy preserved (no new top-level `##` sections). |
| No [NEEDS CLARIFICATION] markers remain | ✅ | Verified — `Select-String "NEEDS CLARIFICATION"` returns 0 matches across `spec.md`. All three pass-3 answers are decisive (no markers, no deferrals). |
| Requirements are testable and unambiguous | ✅ | FR-043 names the depth-1 ceiling explicitly and points back to A12 / FR-057; FR-057's cascade-depth-ceiling block enumerates the non-transitive `origin_cascade_id` rule and the re-entry pathway; FR-059 enumerates the three verbs with explicit semantics for in-flight cascade work and an explicit role-restriction (FR-051); FR-060 enumerates which sub-agents populate `prompt_hash` and which receive `null`; FR-005 references FR-060 to make the audit linkage testable. Every new acceptance scenario (US6 #8, US9 #4, US9 #5) is Given/When/Then-shaped with a single observable outcome. |
| Success criteria are measurable | ✅ | SC-001..SC-012 unchanged. SC-011 (no thread collapse + reproducible) is reinforced by the A12 / FR-057 cascade-depth-1 ceiling (bounded cascade count per turn → byte-deterministic replay); SC-007 (100 % typed-signal-or-refused audit coverage) is reinforced by the new typed depth-2-refusal audit entry and the `lifecycle.paused` / `sub_agent.cancel` audit entries on the lifecycle path; the `prompt_hash` field is implicitly under SC-007's audit-coverage umbrella for LLM-bearing sub-agents. |
| Success criteria are technology-agnostic | ✅ | SCs unchanged; `prompt_hash` is named as a generic forensic fingerprint (sha256 is a content-addressing primitive, not a framework or library). |
| All acceptance scenarios are defined | ✅ | New scenarios added: US6 #8 (depth-2 cascade refusal — `origin_cascade_id` non-transitive); US9 #4 (pause-during-cascade — in-flight completes its current step, deferred hops not auto-replayed on resume); US9 #5 (abort-during-cascade — `sub_agent.cancel` per in-flight invocation, `end_reason: aborted`, FR-054 lessons-capture triggered automatically). |
| Edge cases are identified | ✅ | Edge case count grew from 19 → 21 with 2 new cases (depth-2 cascade refusal; abort-during-cascade — and the same bullet covers `pause` semantics analogously). |
| Scope is clearly bounded | ✅ | No scope changes. Out-of-scope and spec-007 / 020 / 024 / 026 / 028 dependencies still explicit. The `prompt_hash` field is named as the *what* (canonical sha256 over the LLM's input); exact wire-format/storage/exporter wiring is owned by plan phase. The lifecycle verbs are explicitly named as inheriting spec-024 implementation — feature 036 only makes the surface explicit within its own FR set, no re-implementation. |
| Dependencies and assumptions identified | ✅ | A12 added (cascade chain-depth = 1 hard cap, with `origin_cascade_id` non-transitivity rationale tied to SC-011 / FR-054 / Constitution V). FR-059 inherits spec-024 lifecycle implementation explicitly; FR-060 inherits spec-024's Controller `controller_prompt.md` versioning precedent explicitly. No new external dependencies introduced. |
| All functional requirements have clear acceptance criteria | ✅ | FR-043 cascade-depth-1 mirrored by US6 scenario #8 + the new "depth-2 cascade refusal" Edge Case bullet; FR-057's cascade-depth ceiling block mirrored by the same scenario + Edge Case bullet (one walk over the cited audit entries demonstrates the rule); FR-059 mirrored by US9 scenarios #4 (pause) and #5 (abort) + the new "abort while a cascade fan-out is mid-flight" Edge Case bullet (which also covers pause analogously); FR-060 mirrored by FR-005's updated linkage and by the Sub-Agent Invocation Record key-entity definition that lists `prompt_hash` as a typed field with population rules. |
| User scenarios cover primary flows | ✅ | No story removed or down-prioritised. P2 story US6 gained scenario #8 (now 8 scenarios); P3 story US9 gained scenarios #4 and #5 (now 5 scenarios). All other stories unchanged. |
| Feature meets measurable outcomes defined in Success Criteria | ✅ | SC-011 strengthened by A12 cascade-depth-1 ceiling (bounded cascade count per turn → byte-deterministic across replays); SC-007 strengthened by typed `lifecycle.paused` / `sub_agent.cancel` / depth-2-refusal audit entries (no silent drops on the lifecycle or cascade-depth pathways); FR-049 audit-export coverage extended via FR-060 to surface `prompt_hash` to FR-054 lessons-capture (forensic replay completeness for LLM-bearing exercises). |
| No implementation details leak into specification | ✅ | Verified across all 7 edited locations (FR-005, FR-043, FR-057 cascade-depth-ceiling block, new FR-059, new FR-060, Sub-Agent Invocation Record key entity, A12) plus the 3 new acceptance scenarios and 2 new edge-case bullets — only audit-entry tag names (`lifecycle.paused`, `sub_agent.cancel`, `cascade.degraded_to_annotation` already existed), policy contracts (cascade-depth-1, `origin_cascade_id` non-transitive, role-restricted lifecycle verbs, `prompt_hash` as a sha256 content-address), and a planning hand-off note are added. The `controller_prompt.md` reference is solely a precedent citation for spec-024's existing Controller-prompt versioning practice (not an implementation directive for feature 036). |

**Result**: All 16 checklist items pass for iteration 4.

### Iteration 4 — final counts

- Functional requirements: **60** (FR-001..FR-058 from iteration 3 + FR-059 new for coordinator lifecycle verbs `pause` / `resume` / `abort` + FR-060 new for `prompt_hash` audit-fingerprint capture; FR-059 placed in a new "Coordinator lifecycle controls" subsection between the Multi-hazard concurrency / degraded-mode subsection and the Post-exercise lessons capture subsection to keep the topical grouping intact; FR-060 placed in the Audit / provenance / isolation subsection adjacent to FR-051 since it's an audit-completeness requirement).
- Success criteria: **12** (SC-001..SC-012, unchanged).
- Edge cases: **21** (19 carried + 2 new — depth-2 cascade refusal with non-transitive `origin_cascade_id`; abort-during-cascade with in-flight cancellation + `end_reason: aborted` + FR-054 lessons-capture trigger, with pause semantics covered analogously in the same bullet).
- Assumptions: **12** (A1..A11 carried + new A12 for the cascade chain-depth = 1 hard cap).
- Clarifications: **13** Q→A entries total — 5 dated `Session 2026-05-08 (pass 1)` + 5 dated `Session 2026-05-08 (pass 2)` + 3 dated `Session 2026-05-08 (pass 3 — checklist-surfaced)`.

**Pass-3 origin note**: Pass 3 is qualitatively different from passes 1 and 2 — passes 1/2 were `/speckit.clarify` discoveries of genuine ambiguities; pass 3 was `/speckit.checklist` surfacing of 3 coverage gaps that the calling agent had already resolved decisively against the project constitution and spec-024 inheritance. The pass-3 cycle therefore did not ask new questions of the user; it integrated pre-resolved answers into the spec to close the checklist gaps. The 5 newly-created supplementary checklists (`safety-and-life-primacy.md`, `audit-and-provenance.md`, `accessibility-and-cald.md`, `integration-and-test-coverage.md`, `graceful-degradation.md`) may need a re-validation sweep against the iteration-4 spec; that re-validation is a follow-up, not part of iteration 4.

## Iteration 5 — Plan-phase output (2026-05-08)

**Iteration trigger**: `/speckit.plan` invocation against the iteration-4 spec.

**Counts (unchanged from iteration 4)**:

- Functional requirements: **60** (FR-001..FR-060) — no FR added or removed in plan phase.
- Success criteria: **12** (SC-001..SC-012) — no SC added or removed in plan phase.
- Edge cases: **21** — no edge case added or removed in plan phase.
- Assumptions: **12** (A1..A12) — no assumption added or removed in plan phase.
- Clarifications: **13** Q→A entries across 3 sessions — no new clarification opened in plan phase.

**Plan-phase outputs** (under `specs/036-sim-agent-extend/`):

| Artefact | Purpose |
|---|---|
| `plan.md` | High-level technical plan; mermaid architecture diagram; decisions on all 12 open trade-offs; Foundry carve-out registry rows; Cosmos Session-consistency ADR; AVM module list; Constitution compliance summary; FR-002 stub-string migration plan; P1/P2/P3 phasing. |
| `research.md` | Detailed rationale for each trade-off with Azure SKU/region/cost; existing-pattern reuse table; full risk register; cost envelope (~AU$555/month MVP). |
| `data-model.md` | 6 Cosmos containers with partition keys + consistency levels; 6 Key Entities (+ supporting entities) with Pydantic v2 + JSON Schema; append-only audit constraints; ER diagram. |
| `contracts/openapi-simulation.yaml` | Extended OpenAPI: direct REST `abort` / `pause` / `resume`; `inject-telemetry` direct surface; SSE stream documentation reference; RFC 7807 Problem Details for refusals. |
| `contracts/sse-map-overlay.md` | **Closed set of 6 SSE event types and 16 layer types yielding ≈81 valid (event_type, layer_type) tuples after §4.6 sentinel-placeholder rules**; freshness-window-driven `stale` rendering contract; reconnect / Last-Event-ID semantics. |
| `contracts/audit-envelope.md` | **19** typed audit-entry schemas (was 18 at iteration-5; F4.1 added `cascade.depth2_refused`); gap-free per-sim sequence-number guarantee; append-only Cosmos RBAC; machine-export pathway with carve-out flagging. |
| `contracts/sub-agent-adapter.md` | `SubAgentFn` interface (unchanged at type level); `SubAgentReply` gains `prompt_hash` / `model_deployment` / `sub_agent_invocation_id`; production-vs-stub factory; FR-006 timeout cascade; FR-002 migration checklist. |
| `contracts/telemetry-injection-llm.md` | Azure OpenAI `gpt-4o-mini` with strict `json_schema` mode; full signal-batch JSON Schema (9-category enum, typed parameters per category); Pydantic v2 post-validator; degraded rule-based fallback; pre-LLM Content-Safety gate; Cosmos Session-token capture for FR-015. |
| `quickstart.md` | 5-min developer walkthrough: env vars; `docker-compose.dev.yml` service list; bootstrap script; inject-via-chat verification loop; FR-002 grep verification; SC-006 egress-block test invocation. |

**Constitution v1.2.0 compliance** (re-confirmed at end of plan phase):

- **AU residency** — all data-plane resources `australiaeast`; Foundry carve-out limited to model-hosting endpoints (`gpt-4o-mini`, `gpt-4o`) per Non-Negotiable #2 with explicit registry rows + 12-month review date.
- **AAD-only auth** — `Simulation.Coordinator` and `Simulation.Observer` Entra app roles; no API keys in request paths.
- **AVM-first** — every new resource specified via `br/public:avm/res/...` Bicep modules with pinned versions; module list in plan.md.
- **3-Container-App cap** — honoured: `simulation-telemetry-injection` is bundled as a Python sibling module inside `apps/agents/`; no 4th Container App proposed.
- **HITL** — coordinator-initiated chat → injection → fan-out remains coordinator-driven; cascade-depth-1 ceiling preserves coordinator situational awareness; lifecycle verbs (`pause` / `resume` / `abort`) restricted to `Simulation.Coordinator`.
- **Transparency / auditability** — append-only `simulation_audit_entries` with gap-free sequence numbers + **19** typed entry schemas (was 18 at iteration-5; F4.1 added `cascade.depth2_refused`) + machine-export with SHA-256 digest; FR-060 `prompt_hash` capture on every LLM-bearing sub-agent invocation; Constitution IV satisfied.

**Pass / fail**: ✅ Plan-phase artefacts complete; iteration-4 counts preserved; no new spec-level open questions surfaced.

**Next iteration trigger**: `/speckit.tasks` will produce `tasks.md` enumerating the implementation work items derived from `plan.md` + `data-model.md` + `contracts/`.

## Iteration 6 — Step 8 amendment cycle (2026-05-08)

**Iteration trigger**: `/speckit.specify` re-loop after the Step 8 cross-cohort review (85
personas: 10 operational + 58 sectors + 17 technical) returned **RE-LOOP** with **18 CRITICAL /
39 HIGH / 24 MEDIUM / 4 LOW** findings and an aggregate verdict of **0 ENDORSE / 30
ENDORSE-WITH-RESERVATIONS / 55 OBJECT**. The full validated synthesis is preserved at
`step8-synthesis.md` in the Step 8 session workspace; every finding cited verifiable
`file:line` evidence in the implementation.

**Counts (post-amendment)**:

- Functional requirements: **66** (FR-001..FR-060 from iteration 5 + **6 new** FR-061..FR-066;
  **12 strengthened** existing FRs: FR-007, FR-009, FR-013, FR-015, FR-027, FR-039, FR-048,
  FR-051, FR-052, FR-054, FR-057, FR-058, FR-059).
- Success criteria: **12** (SC-001..SC-012, unchanged).
- Edge cases: **21** (unchanged).
- Assumptions: **12** (A1..A12, unchanged).
- Clarifications: **21** Q→A entries total — 5 dated `Session 2026-05-08 (pass 1)` + 5 dated
  `Session 2026-05-08 (pass 2)` + 3 dated `Session 2026-05-08 (pass 3 — checklist-surfaced)`
  + **5 dated `Session 2026-05-08 amendment pass 1`** (Q1: trigger_source enum;
  Q2: HTTP 503 + DLQ + sequence_number=-1 + Retry-After; Q3: idempotency-key per-(sim_id,
  verb, route) namespace + RFC 9457 conflict; Q4: aiims_function single-valued +
  secondary_aiims_tags array; Q5: prompt_hash_source enum 3-value) + **3 dated
  `Session 2026-05-08 amendment pass 2`** (Q6: delivery_channel enum on
  audit.watermark.applied; Q7: lifecycle audit lineage + idempotency round-trip;
  Q8: thread_kind="hazard" filter on cap counter).
- Cascade matrix: **expanded** to canonical (utility→{Health, Comms, Transport, Resource};
  hydrology→{Risk, Evac, Comms, Resource}; transport→{Evac, Comms, Resource};
  evacuation-centre→{Planning, Evac, Resource}; geohazard→{Risk, Evac, Resource}).

**FR-coverage summary table — one row per new/strengthened FR pointing to the detailed
checklist items in `amendment-pass.md`**:

| FR | Type | Amendment | Detail items |
|---|---|---|---|
| FR-007 | STRENGTHEN | (synthesis labelled M; corrected to FR-021 in spec.md — see FR-021 row below) | (none — see FR-021) |
| FR-009 | STRENGTHEN | C + pass-1 Q1 | [amendment-pass.md](./amendment-pass.md) CHK009..CHK015 |
| FR-013 | STRENGTHEN | G | [amendment-pass.md](./amendment-pass.md) CHK035..CHK037 |
| FR-015 | STRENGTHEN | C + pass-1 Q1 | [amendment-pass.md](./amendment-pass.md) CHK009..CHK015 |
| FR-021 | STRENGTHEN | M (synthesis labelled "FR-007") | [amendment-pass.md](./amendment-pass.md) CHK060..CHK063; [multi-jurisdiction.md](./multi-jurisdiction.md) CHK001..CHK014 |
| FR-027 | STRENGTHEN | B + H + K | [amendment-pass.md](./amendment-pass.md) CHK006..CHK008 (B), CHK038..CHK040 (H), CHK053..CHK055 (K); [accessibility-and-cald.md](./accessibility-and-cald.md) CHK046..CHK047 |
| FR-039 | STRENGTHEN | L | [amendment-pass.md](./amendment-pass.md) CHK056..CHK059; [accessibility-and-cald.md](./accessibility-and-cald.md) CHK042..CHK045; [multi-jurisdiction.md](./multi-jurisdiction.md) CHK018..CHK023 |
| FR-043 / FR-044 / FR-047 | EXPAND | N | [amendment-pass.md](./amendment-pass.md) CHK064..CHK067 |
| FR-048 | STRENGTHEN | D + pass-1 Q2 | [amendment-pass.md](./amendment-pass.md) CHK016..CHK022; [audit-and-provenance.md](./audit-and-provenance.md) CHK048..CHK051; [graceful-degradation.md](./graceful-degradation.md) CHK065..CHK069 |
| FR-051 | STRENGTHEN | E + pass-1 Q3 | [amendment-pass.md](./amendment-pass.md) CHK023..CHK027; [audit-and-provenance.md](./audit-and-provenance.md) CHK063 |
| FR-052 | STRENGTHEN | J + pass-2 Q8 | [amendment-pass.md](./amendment-pass.md) CHK048..CHK052; [audit-and-provenance.md](./audit-and-provenance.md) CHK061..CHK062; [graceful-degradation.md](./graceful-degradation.md) CHK057..CHK060 |
| FR-054 | STRENGTHEN | I | [amendment-pass.md](./amendment-pass.md) CHK041..CHK045 |
| FR-057 | STRENGTHEN | J + pass-2 Q8 | [amendment-pass.md](./amendment-pass.md) CHK046..CHK052; [graceful-degradation.md](./graceful-degradation.md) CHK061..CHK064 |
| FR-058 | STRENGTHEN | L + pass-2 Q6 | [amendment-pass.md](./amendment-pass.md) CHK056..CHK059, CHK081..CHK085; [audit-and-provenance.md](./audit-and-provenance.md) CHK056..CHK057; [accessibility-and-cald.md](./accessibility-and-cald.md) CHK042..CHK045 |
| FR-059 | STRENGTHEN | F + pass-2 Q7 | [amendment-pass.md](./amendment-pass.md) CHK028..CHK034; [audit-and-provenance.md](./audit-and-provenance.md) CHK058..CHK060; [graceful-degradation.md](./graceful-degradation.md) CHK070..CHK071 |
| **FR-061** | **NEW** | A + pass-1 Q4 | [amendment-pass.md](./amendment-pass.md) CHK001..CHK005; [multi-jurisdiction.md](./multi-jurisdiction.md) CHK015..CHK017 |
| **FR-062** | **NEW** | O | [amendment-pass.md](./amendment-pass.md) CHK068..CHK072 |
| **FR-063** | **NEW** | P | [amendment-pass.md](./amendment-pass.md) CHK073..CHK078 |
| **FR-064** | **NEW** | Q + pass-2 Q6 | [amendment-pass.md](./amendment-pass.md) CHK079..CHK085; [accessibility-and-cald.md](./accessibility-and-cald.md) CHK036..CHK041; [audit-and-provenance.md](./audit-and-provenance.md) CHK056..CHK057 |
| **FR-065** | **NEW** | R + pass-1 Q5 | [amendment-pass.md](./amendment-pass.md) CHK086..CHK091; [audit-and-provenance.md](./audit-and-provenance.md) CHK052..CHK055 |
| **FR-066** | **NEW** | S + pass-1 Q2 + pass-1 Q3 | [amendment-pass.md](./amendment-pass.md) CHK092..CHK099; [audit-and-provenance.md](./audit-and-provenance.md) CHK063..CHK065; [graceful-degradation.md](./graceful-degradation.md) CHK070..CHK071 |

**Pass / fail**: ⏳ Iteration 6 introduces 6 new FRs and strengthens 12 existing FRs;
spec.md amendment log is in place at the top of the spec; the supplementary checklists are
augmented with amendment items; the master traceability matrix is captured in
`amendment-pass.md`. Re-validation against the original 16 spec-quality criteria is owed
once `/speckit.plan` re-aligns plan.md, research.md, data-model.md, contracts/*, and the
ADR set against the amended FR set.

**Next iteration trigger**: `/speckit.plan` to update `plan.md`, `research.md`,
`data-model.md`, and ADRs for the amendment scope (FR-061 → FR-066 + 12 strengthened FRs +
8 new Q→A entries). After plan update, run `/speckit.tasks` to regenerate `tasks.md`.
After tasks update, run `/speckit.analyze` until 🟢 GREEN. Only then proceed to
`/speckit.implement`.