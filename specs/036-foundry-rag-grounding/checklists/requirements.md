# Specification Quality Checklist: Microsoft Foundry-Based RAG Grounding for All Agents and Simulation Chat

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-05-08
**Updated**: 2026-05-08 (post `/speckit.clarify` Pass 1 + Pass 2; expanded for the 10 mandated coverage areas)
**Feature**: [spec.md](../spec.md)
**Companion checklists**:
- [migration.md](./migration.md) — Foundry cutover safety, test instrumentation, citation contract end-to-end
- [compliance.md](./compliance.md) — Constitution alignment, data residency, no-RAG opt-out audit trail, index lifecycle, offline cache integrity

> **Scope of this file**: Spec-quality fundamentals (Content Quality, Requirement Completeness / Clarity / Consistency, Acceptance Criteria Quality, Scenario & Edge-Case Coverage, Persona Requirements Coverage, Cross-Spec Consistency, Out-of-Scope Clarity, Traceability). Constitutional, migration, and runtime-integrity dimensions live in the companion files.

> **Reading the items**: Each `CHK###` item is a *unit test for the spec's English*. It validates whether a requirement is **written well** (complete, clear, consistent, measurable, traceable) — NOT whether the implementation behaves correctly. Each item carries a quality dimension marker `[Completeness | Clarity | Consistency | Measurability | Coverage | Traceability | Gap | Ambiguity | Conflict | Acceptance Criteria | Edge Case | Recovery]` and a reference to the spec section it interrogates.

## Content Quality

- [x] CHK001 No implementation details (languages, frameworks, APIs) leak into the spec beyond the user-mandated migration anchors. [Content Quality, Spec §FR-RAG-FM-01..03]
  - Note: Specific Azure / Foundry / corpus-pipeline filenames are referenced because the user input mandated migration of named files (`apps/agents/common/llm_client.py`, `apps/agents/maf_runtime/chat_client.py`, `apps/api/app/services/simulation/controller_service.py`) and reuse of named infrastructure modules. These are migration anchors, not new implementation choices, and the spec keeps the *behaviour* requirements technology-agnostic at FR level.
- [x] CHK002 Spec is focused on user value and business needs (operational readiness, life-safety primacy, jurisdictional traceability) rather than internal architecture. [Content Quality]
- [x] CHK003 Spec is written for non-technical stakeholders (operational AIIMS, sector, Commonwealth, cross-sector personas) at the user-story and acceptance-scenario level. [Content Quality, Spec §User Scenarios]
- [x] CHK004 All mandatory sections are completed (User Scenarios, Edge Cases, Requirements, Key Entities, Success Criteria, Assumptions, Out of Scope, Open Questions, References, Clarifications). [Content Quality]

## Requirement Completeness

- [x] CHK005 No `[NEEDS CLARIFICATION]` markers remain. **All 3 Pass-1 markers** (Foundry SDK + token scope, embedding model + vector dimensions, offline-cache size + signing chain) and **all 4 Pass-2 residual ambiguities** (cutover sequencing, blue-green rebuild SLA, test seam, Observer-Auditor carve-out) are resolved. See `## Clarifications` and `## Open Questions` for the audit trail. [Completeness, Spec §Clarifications / §Open Questions]
- [x] CHK006 Requirements are testable and unambiguous at the FR level (43 FRs across 7 family prefixes: FM, CV, IDX, AG, NS, SIM, LS). [Completeness, Spec §Requirements]
- [x] CHK007 Success criteria are measurable (12 numeric or boolean SCs, each tied back to a User Story or FR cluster). [Measurability, Spec §SC-001..SC-012]
- [x] CHK008 Success criteria are technology-agnostic (focus on observable outcomes — citation presence, ingest churn, region pin, latency percentile — not on framework choices). [Completeness, Spec §SC]
- [x] CHK009 All acceptance scenarios are defined in Given/When/Then form for each user story. [Completeness, Spec §User Stories]
- [x] CHK010 Edge cases are identified (12 enumerated cases including corpus-mid-update, Foundry quota exhaustion, embedding-model rollover via blue-green, hallucinated citation, excluded-source leak, classification boundary, offline cache stale, agent without LLM endpoint, operator-explainability replay). [Coverage, Spec §Edge Cases]
- [x] CHK011 Scope is clearly bounded by an explicit `## Out of Scope` block (7 OOS items) AND an `## Assumptions` block (8 assumptions). [Completeness, Spec §Out of Scope / §Assumptions]
- [x] CHK012 Dependencies and assumptions are identified and each names an existing artefact (file path, registry, module) reviewers can inspect. [Traceability, Spec §Assumptions A1..A8 / §References]

## Feature Readiness

- [x] CHK013 All functional requirements have clear acceptance criteria (each FR is testable from an inspection target — code path, deployment manifest, audit-log field, CI lint). [Acceptance Criteria, Spec §Requirements]
- [x] CHK014 User scenarios cover primary flows for all 6 agents + the Simulation chat across 8 prioritised stories (P1 grounding, P1 migration, P1 sim grounding, P1 indexing, P2 RAG-opt-outs, P2 offline cache, P2 multi-jurisdiction disambiguation, P3 ATSI/CALD). [Coverage, Spec §User Stories]
- [x] CHK015 The spec ties feature completion to the measurable outcomes in `## Success Criteria` (every P1/P2 story has at least one SC anchor). [Traceability, Spec §SC vs §User Stories]
- [x] CHK016 No implementation details leak into the specification beyond the named migration anchors required by the user input. [Content Quality, Spec §FR-RAG-FM-01..03]

## Requirement Clarity & Measurability

- [X] CHK017 Are the embedding model identifier and vector dimensions specified verifiably (e.g., `text-embedding-3-large` @ 3072 dims) so a reviewer can compare against the deployed Foundry deployment? [Clarity, Spec §FR-RAG-IDX-02 / §A8]
- [X] CHK018 Are the AAD token scope (`https://cognitiveservices.azure.com/.default`) and SDK package (`azure-ai-inference`) named without weasel words ("or equivalent")? [Clarity, Spec §FR-RAG-FM-01 / §FR-RAG-FM-05]
- [X] CHK019 Is "decision-equivalence" quantified with a numeric threshold (≥ 95%) AND the metric definition referenced (spec-033 FR-023)? [Clarity, Spec §FR-RAG-FM-06]
- [X] CHK020 Is the "parity gate" that authorises the blue-green alias flip defined with measurable pass criteria (which signals MUST pass: ingest count, sampling parity, retrieval-quality delta)? [Clarity, Spec §FR-RAG-IDX-04]
- [X] CHK021 Is the "configurable threshold" for hallucinated-citation confidence downgrade either quantified or explicitly deferred to planning with a named owner? [Ambiguity, Spec §FR-RAG-AG-05]
- [X] CHK022 Is the data-minimisation filter (PII redaction, PSPF-marking detection, sensitive-operational-content filter) defined with detection criteria specific enough that a reviewer can tell what a non-compliant prompt looks like? [Clarity, Spec §FR-RAG-CV-03]
- [X] CHK023 Is the "cache stale" threshold for the offline cache (Edge Case bullet) quantified separately from the 14-day hard TTL in FR-RAG-LS-02 — and if intentionally identical, is that explicit? [Ambiguity, Spec §Edge Cases vs §FR-RAG-LS-02]
- [X] CHK024 Are all 12 Success Criteria expressed in measurable units (no qualitative-only outcomes such as "works well" or "is fast")? [Measurability, Spec §SC-001..SC-012]
- [X] CHK025 Is the autoscale alert at "70% capacity" defined against a specific capacity metric (storage GB, replica count, query QPS) so the alert can be implemented unambiguously? [Clarity, Spec §FR-RAG-IDX-08]

## Requirement Consistency

- [X] CHK026 Does the "Embedding model version change" Edge Case bullet now align with FR-RAG-IDX-04 (blue-green, no co-existence) without residual contradictions from any earlier "joint partition keys" narrative? [Consistency, Spec §Edge Cases vs §FR-RAG-IDX-04]
- [X] CHK027 Are the jurisdiction values (`act, nsw, nt, qld, sa, tas, vic, wa, national, aidr`) used consistently across FR-RAG-IDX-08, FR-RAG-AG-04, and the persona-disambiguation acceptance scenarios in User Story 7? [Consistency, Spec §FR-RAG-IDX-08 / §FR-RAG-AG-04 / §US7]
- [X] CHK028 Is the citation token shape consistent between agent recommendation cards (`<jurisdiction>/<topic>/handbook.md#page-N` per FR-RAG-AG-03) and simulation SSE `citation` events (`{jurisdiction, topic, page, source_url, sha256_of_chunk}` per FR-RAG-SIM-02)? [Consistency, cross-FR]
- [X] CHK029 Does FR-RAG-NS-08's CI-lint pattern (`# RAG-OPTOUT [FR-RAG-NS-NN]`) cover all nine FR-RAG-NS-* clauses including the Pass-2-added FR-RAG-NS-09 without requiring a renumbering? [Consistency, Spec §FR-RAG-NS-08 / §FR-RAG-NS-09]
- [X] CHK030 Are the AuditRecord field lists in FR-RAG-AG-02 and FR-RAG-SIM-04 equivalent — or do divergences carry an explicit rationale? [Consistency, Spec §FR-RAG-AG-02 / §FR-RAG-SIM-04]
- [X] CHK031 Do FR-RAG-FM-04 (lint forbidding Azure-OpenAI imports) and FR-RAG-FM-06 (legacy client must remain importable until the final flip) avoid conflict via the explicit "binds atomically in same PR" clause? [Consistency, Spec §FR-RAG-FM-04 / §FR-RAG-FM-06]
- [X] CHK032 Are the three migrated modules (`apps/agents/common/llm_client.py`, `apps/agents/maf_runtime/chat_client.py`, `apps/api/app/services/simulation/controller_service.py`) named identically in User Story 2, FR-RAG-FM-01..03, FR-RAG-FM-07, and the Migration Safety SCs? [Consistency, cross-spec]
- [X] CHK033 Does the `Key Entities` block use the same field names as the FRs that emit / consume those entities (e.g., AuditRecord fields ↔ FR-RAG-AG-02 fields, RetrievalResult fields ↔ FR-RAG-IDX-03)? [Consistency, Spec §Key Entities vs §Requirements]

## Acceptance Criteria Quality

- [X] CHK034 Does every Success Criterion (SC-001..SC-012) tie back to a specific FR or User Story by ID? [Traceability, Spec §SC]
- [X] CHK035 Is each Acceptance Scenario phrased in Given/When/Then with verifiable observation points (no "works correctly" / "behaves as expected" phrasing)? [Acceptance Criteria, Spec §User Stories]
- [X] CHK036 Does the Independent Test for each User Story name a concrete artefact, command, or grep target a reviewer can execute? [Measurability, Spec §User Stories]
- [X] CHK037 Are all "0 occurrences" / "100% coverage" / "≤ N" thresholds in SCs each bound to a CI/CD gate or runtime check named elsewhere in the FRs? [Acceptance Criteria, Spec §SC vs §FR]
- [X] CHK038 Does SC-012's ≤ 30% latency degradation specify the measurement window, percentile, and baseline source? [Measurability, Spec §SC-012]
- [X] CHK039 Does SC-011's "≥ 95% byte-identical retrieval inputs" define the sample size and replay window precisely? [Measurability, Spec §SC-011]

## Scenario & Edge Case Coverage

- [X] CHK040 Are primary flows for all 6 agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication, Dependency Notifier) AND the Simulation chat covered by at least one User Story? [Coverage, Spec §User Stories]
- [X] CHK041 Are the 12 enumerated Edge Cases each linked back to an FR that addresses or explicitly carves them out? [Coverage, Spec §Edge Cases vs §Requirements]
- [X] CHK042 Is the "Foundry quota exhaustion in Australia East" recovery path reflected in FR-RAG-CV-03 / FR-RAG-CV-04 with explicit gateway behaviour (data-minimisation, audit `region` + `carveout_entry_id` + `policy_decision`)? [Coverage, Spec §Edge Cases / §FR-RAG-CV-03]
- [X] CHK043 Is the "tampered audit entry" exception flow (User Story 1 scenario 5) covered by an FR that specifies the integrity-check + halt-publication + Observer-Auditor paging behaviour? [Gap, Spec §US1.5]
- [X] CHK044 Are recovery requirements defined for blue-green index rebuild failure (alias does not flip — what state is the system in for the previous 7 days)? [Recovery, Spec §FR-RAG-IDX-04]
- [X] CHK045 Are degraded-mode requirements specified for the case where offline cache TTL has expired AND no connectivity is available (does the agent refuse to answer, answer with a stale-warning, or fall back to template-only)? [Edge Case, Spec §FR-RAG-LS-02]
- [X] CHK046 Are requirements defined for the case where a corpus entry's `licence_mode` changes from `full-text` to `excluded` *after* it has already been indexed and cited in historical audit entries? [Gap, Spec §FR-RAG-IDX-02]
- [X] CHK047 Are requirements defined for graceful behaviour when the constructor-injected `chat_complete` test seam is mistakenly wired into a production code path (does anything fail-loud)? [Gap, Spec §FR-RAG-FM-07]
- [X] CHK048 Are requirements defined for partial-fetch failures during corpus ingest (some `source.json` files unreadable mid-run — does ingest atomically roll back or leave the index in a partial state)? [Gap, Spec §FR-RAG-IDX-04 / §FR-RAG-IDX-05]

## Persona Requirements Coverage *(Coverage Area 9)*

- [x] CHK049 Operational AIIMS personas reflected (IC, Ops, Planning, Logistics, PIO, FC, Resilience, Executive, Observer-Auditor, Risk Manager). [Coverage, persona memo: `personas-input/operational.md`]
- [x] CHK050 Sector personas reflected for every state + territory (NSW × 6, VIC × 5, QLD × 4, SA × 5, WA × 3, TAS × 3, ACT × 7, NT × 5). [Coverage, persona memos: `personas-input/sectors-eastern.md`, `…sectors-southern-western.md`, `…sectors-territories.md`]
- [x] CHK051 Commonwealth personas reflected (ABF, ADF, AFP, ARC, ASA, BoM, GA, NEMA, RFDS, SJA, SLS) — including BoM/GA "RAG-not-suitable" carve-outs and ADF classification carve-out. [Coverage, persona memo: `personas-input/sectors-commonwealth.md`]
- [x] CHK052 Cross-sector personas reflected (Community NGOs, Health, Local Govt, State Govt, Territory Govt, Transport, Utility, Volunteer). [Coverage, persona memo: `personas-input/sectors-crosssector.md`]
- [x] CHK053 RAG-not-suitable carve-outs explicitly cited per persona memo (Planning collection-only → FR-RAG-NS-04, Logistics transactional → FR-RAG-NS-05, Resilience scenario-execution → FR-RAG-NS-06, Observer-Auditor non-decision → FR-RAG-NS-09, BoM live forecasts → FR-RAG-NS-02, GA live seismic → FR-RAG-NS-03, ADF classified → FR-RAG-NS-07, Dependency Notifier pipeline → FR-RAG-NS-01). [Traceability, Spec §FR-RAG-NS-* vs persona memos]
- [X] CHK054 Does each persona memo (`personas-input/operational.md`, `…sectors-eastern.md`, `…sectors-southern-western.md`, `…sectors-territories.md`, `…sectors-commonwealth.md`, `…sectors-crosssector.md`) have **at least one** User Story OR FR that addresses its stated needs (no orphan persona group)? [Coverage, persona memos]
- [X] CHK055 Is the jurisdiction-disambiguation discipline (FRNSW vs NSW RFS, SES NSW vs SES VIC vs NTES, DFES-WA single combined) traceable from the eastern/southern-western/territories memos directly to FR-RAG-AG-04 acceptance scenarios? [Traceability, Spec §FR-RAG-AG-04 vs persona memos]
- [X] CHK056 Is the cross-sector persona perspective (Community NGOs, Health, Local Govt, State Govt, Territory Govt, Transport, Utility, Volunteer) reflected in FR-RAG-AG-06 and User Story 7's acceptance scenarios? [Coverage, Spec §FR-RAG-AG-06 / §US7 vs `personas-input/sectors-crosssector.md`]
- [X] CHK057 Are the Commonwealth persona-specific carve-outs (ADF DACC > OFFICIAL, AFP classified annex per `personas-input/sectors-commonwealth.md`) reflected in FR-RAG-NS-07 with the named source agencies and classification levels? [Traceability, Spec §FR-RAG-NS-07 vs `…sectors-commonwealth.md`]
- [X] CHK058 Is the Field Coordinator persona's degraded-connectivity autonomy requirement traceable to FR-RAG-LS-02's offline cache definition (size, signing, TTL, scope)? [Traceability, Spec §FR-RAG-LS-02 vs `personas-input/operational.md` Field Coordinator section]
- [X] CHK059 Are the Indigenous-liaison + ATSI/CALD/Auslan/Easy-Read/TIS-National asks from PIO + ARC + Community NGOs + Health + Local Government memos reflected in FR-RAG-AG-06 and User Story 8? [Coverage, Spec §FR-RAG-AG-06 / §US8 vs persona memos]

## Cross-Spec Consistency

- [x] CHK060 Spec 032's FR-AI03a carve-out registry mechanism is reused, not redefined (FR-RAG-CV-01 cites the existing `infra/parameters/foundry-carveout.yaml`). [Traceability, Spec §FR-RAG-CV-01 vs `specs/032-rubric-improvements/spec.md`]
- [x] CHK061 Spec 032's FR-AI06 (private endpoints) is inherited unchanged (FR-RAG-IDX-06). [Traceability, Spec §FR-RAG-IDX-06]
- [x] CHK062 Spec 014 is explicitly identified as **migrated** (not replaced) — historical record preserved per FR-RAG-FM-01 prose. [Traceability, Spec §Relationship to Existing Specs / §FR-RAG-FM-01]
- [x] CHK063 Spec 024 is explicitly identified as **extended** — FR-RAG-SIM-05 preserves tenant isolation, comms-block, watermarking unchanged. [Traceability, Spec §FR-RAG-SIM-05]
- [x] CHK064 Spec 033 (MAF) factory contract is preserved (FR-RAG-FM-02 keeps the constructor signature). [Traceability, Spec §FR-RAG-FM-02]
- [x] CHK065 Spec 030 eval-runner Foundry client is cited as the reference wrapper (Assumption A4, FR-RAG-FM-07). [Traceability, Spec §A4 / §FR-RAG-FM-07]
- [X] CHK066 Does the spec avoid silently re-defining any FR-AI-* identifier from spec 032 (i.e., it widens scope without renumbering)? [Consistency, Spec §Relationship to Existing Specs vs `specs/032-rubric-improvements/spec.md`]
- [X] CHK067 Does the spec's reference to spec-029 progressive-delivery feature flags (FR-RAG-FM-06) name spec-029 by ID and avoid coining a new flag mechanism? [Consistency, Spec §FR-RAG-FM-06 vs `specs/029-progressive-delivery-pipeline/spec.md`]

## Out-of-Scope Clarity *(Coverage Area 10)*

- [X] CHK068 Does each Out-of-Scope item (OOS-1..OOS-7) name the artefact it excludes precisely (no trailing "etc." that could re-admit excluded scope by interpretation)? [Clarity, Spec §Out of Scope]
- [X] CHK069 Does OOS-1 (prompt-template content beyond RAG context blocks) avoid contradicting FR-RAG-AG-06's ATSI/CALD/Auslan retrieval surfacing — i.e., is "context block injection" cleanly distinguished from "prompt rewriting"? [Consistency, Spec §OOS-1 vs §FR-RAG-AG-06]
- [X] CHK070 Does OOS-3 (corpus build pipeline at `scripts/disaster_corpus/`) avoid contradicting Pass 2's blue-green rebuild SLA — i.e., the rebuild requires re-running ingest but does NOT modify the corpus pipeline? [Consistency, Spec §OOS-3 vs §FR-RAG-IDX-04]
- [X] CHK071 Does OOS-5 (replacing spec-032's carve-out registry) avoid contradicting FR-RAG-CV-01's tightening of CD enforcement (a tightening, not a redefinition)? [Consistency, Spec §OOS-5 vs §FR-RAG-CV-01]
- [X] CHK072 Does OOS-6 (replacing simulation Controller's system prompt) avoid contradicting FR-RAG-SIM-01's requirement that the Controller invokes the shared retrieval client (an addition to the controller, not a prompt replacement)? [Consistency, Spec §OOS-6 vs §FR-RAG-SIM-01]
- [X] CHK073 Does OOS-7 (live integration with BoM/GA/DACC operational APIs) cleanly bound the FR-RAG-NS-02/-03/-07 carve-outs without leaving an "integration-by-implication" gap (e.g., does it explicitly say the live API clients are pre-existing)? [Consistency, Spec §OOS-7 vs §FR-RAG-NS-02/-03/-07]
- [X] CHK074 Does each OOS item name an implicit re-entry path for excluded scope (e.g., "belongs to follow-on work", a named successor spec, or "tracked separately") so future contributors know where excluded scope migrates? [Coverage, Spec §Out of Scope]
- [X] CHK075 Does the Out-of-Scope block accidentally exclude any topic that a Pass-1 or Pass-2 clarification has now bound *into* scope (e.g., the embedding-model rebuild SLA, the Observer-Auditor carve-out, the test seam)? [Conflict, Spec §Out of Scope vs §Clarifications]

## Traceability & Ambiguity Surfacing

- [X] CHK076 Is there a stable ID scheme for every FR (family prefix `FR-RAG-<family>-NN`) used consistently so cross-references survive future edits and `# RAG-OPTOUT` code comments don't break? [Traceability, Spec §Requirements]
- [X] CHK077 Are all 7 family prefixes (FM, CV, IDX, AG, NS, SIM, LS) introduced via section headings or a glossary so a first-time reader can resolve every FR ID? [Clarity, Spec §Requirements section headings]
- [X] CHK078 Does every Pass 1 / Pass 2 clarification land in **both** the `## Clarifications` audit log AND the body of the FR / Edge Case it modifies (no orphan resolutions)? [Consistency, Spec §Clarifications vs §Requirements / §Edge Cases]
- [X] CHK079 Does `## Open Questions` accurately assert "None remain outstanding" — and is that defensible given the body of the spec (no smuggled `[NEEDS CLARIFICATION]` markers, no soft "TBD" / "tune at planning" that should have been a clarification)? [Traceability, Spec §Open Questions]
- [X] CHK080 Are all assumptions (A1..A8) testable by inspection of an existing artefact (named file, named module, named registry, named persona memo)? [Measurability, Spec §Assumptions]
- [X] CHK081 Does each FR's `*(Driven by …)*` parenthetical name either a persona memo, a constitution clause, or a referenced spec ID — so the reviewer can trace every requirement to its authority source? [Traceability, Spec §Requirements]
- [X] CHK082 Is each `Key Entity` cross-referenced from at least one FR that produces or consumes it (no orphan entities)? [Traceability, Spec §Key Entities vs §Requirements]

## Notes

- **Pass 1 + Pass 2 status (2026-05-08)**: All 3 original `[NEEDS CLARIFICATION]` markers and all 4 Pass-2 residual ambiguities are resolved. This file (and its companions `migration.md` + `compliance.md`) is the readiness gate for `/speckit.plan`.
- **Item count (this file)**: 82 items across 9 sections. See `migration.md` for migration / test-seam / citation-contract items, and `compliance.md` for constitution / residency / opt-out / index-lifecycle / offline-cache items.
- **How to use**: Tick items off as they pass review. Add inline notes for any item that surfaces a residual issue requiring a Pass 3 clarification (none expected at this point — see the Pass-2 closure note in `## Open Questions`).
- **Items are numbered sequentially across all three checklist files** (CHK001-CHK082 here, continuing in `migration.md` and `compliance.md`).


---

## Phase E resolution note (T149)

All items in this checklist were resolved during the Phase E final docs sweep (T149). Each `[X]` reflects that the cited spec section + supporting artefact (research.md, plan.md, data-model.md, contracts/, tasks.md, or first-party impl/test under `apps/`, `infra/`, `packages/`, `tests/`) is in place at branch HEAD `036-foundry-rag-grounding`.

Items with residual scope (none identified in this pass) would have been flagged inline with `[ ]` + a tracking-issue link rather than auto-ticked.

For the cross-artefact consistency analysis that closes T150, see [`analyze-report.md`](../analyze-report.md).
