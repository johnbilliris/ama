# Multi-Agent Coordination Checklist: Microsoft Foundry-Based RAG Grounding

**Purpose**: Validate that the multi-agent conflict-detection (FR-RAG-COORD-01) and escalation chain (FR-RAG-COORD-02) requirements are specified to a level the AIIMS-aligned reviewer (Ops Officer + IC + FC personas) can verify before planning, including the four conflict classes, the AIIMS escalation chain (Ops Officer → IC unack 5 min → FC offline queue), and the Reversible-class feature-flag taxonomy.
**Created**: 2026-05-09 (post R3 amend loop Sessions 3 + 4 + 5)
**Feature**: [spec.md](../spec.md)
**Cluster**: A9 (Multi-agent conflict) + Pass 1 Q-P1-03 (escalation chain) + Pass 2 Q-P2-06 (4 conflict classes) + Pass 2 Q-P2-08 (Reversible flag class)
**Companion checklists**:
- [audit-and-approval-workflow.md](./audit-and-approval-workflow.md) — AG-02 audit-shape extensions (`conflict_group_id` consumer)
- [compliance.md](./compliance.md) — Constitution alignment (Principle I no-silencing; Principle IV deterministic replay)
- [accessibility.md](./accessibility.md) — Conflict-resolution UI accessibility (FR-RAG-UI-01 cross-ref)

> **Scope of this file**: The multi-agent surface added by R3 Cluster A9: **Conflict detection** (reactive, post-return, deterministic, rule-based; rejected pre-emptive divergence detection), **four conflict classes** (Resource / Spatial / Temporal / Severity), **audit linkage** via `conflict_group_id`, **AIIMS escalation chain** (Ops Officer → IC → FC offline queue), **human-in-loop resolution invariant** (no AI auto-resolve), **feature-flag reversibility** (Reversible class with single-agent-fallback semantics).

> **Item numbering**: Continues from `audit-and-approval-workflow.md` (CHK230+).

## Conflict Detection — Mode & Timing

> **Authority**: FR-RAG-COORD-01 + Pass 2 Q-P2-06; spec 033 MAF agent-isolation model; Constitution Principle IV.

- [ ] CHK230 Is the detection mode ("**reactive, post-return, deterministic, rule-based** — runs in the recommendation-aggregation layer NOT inside any individual agent and NOT in real-time streaming") stated inside FR-RAG-COORD-01 — not only inside Pass 2 Q-P2-06 narrative? [Clarity, Spec §FR-RAG-COORD-01]
- [ ] CHK231 Are the rejected alternatives (pre-emptive divergence detection during inference; inter-agent message-passing) explicitly ruled out so a future contributor cannot silently introduce them? [Coverage, Spec §FR-RAG-COORD-01]
- [ ] CHK232 Is the "recommendation-aggregation layer" that runs the detector named with a concrete component / file path, or only described in prose (i.e., is the home for the detector under-specified)? [Gap, Spec §FR-RAG-COORD-01]
- [ ] CHK233 Is the rationale for rejecting pre-emptive detection (would require inter-agent message-passing — contradicts spec-033 MAF agent-isolation; would break Constitution Principle IV deterministic replay) preserved as a normative constraint, not just narrative? [Consistency, Spec §FR-RAG-COORD-01 vs `specs/033-maf-adoption/spec.md` + Constitution §IV]

## Conflict Classes — Definition & Detection Rules

> **Authority**: Pass 2 Q-P2-06 (four conflict classes); FR-RAG-AG-04 disambiguation fields.

- [ ] CHK234 Are all four conflict classes (**Resource, Spatial, Temporal, Severity**) defined with the exact tuple of compared fields (Resource: `resource_id` + `(start_time, end_time)`; Spatial: `(geo_bbox, time_window)`; Temporal: action verb + deadline; Severity: hazard severity bucket + AIIMS level delta)? [Completeness, Spec §FR-RAG-COORD-01]
- [ ] CHK235 Is the "Severity conflict" delta threshold ("≥1 AIIMS incident level") consistent with the AIIMS incident-level scale used elsewhere in the codebase / spec set? [Consistency, Spec §FR-RAG-COORD-01]
- [ ] CHK236 Is "action verb" (Temporal class) bounded to a closed enum (e.g., `evacuate`, `shelter-in-place`, `withhold-pending-verification`, `issue-warning`) — or is free-text comparison permitted (which would harm determinism)? [Clarity / Measurability, Spec §FR-RAG-COORD-01]
- [ ] CHK237 Are non-conflicts (e.g., compatible recommendations covering disjoint geo_bbox; same-resource sequential allocation in non-overlapping windows) explicitly excluded so the detector cannot false-positive? [Coverage, Spec §FR-RAG-COORD-01]
- [ ] CHK238 Is the canonical "same-resource" / "same-hazard" signal source (FR-RAG-AG-04 disambiguation fields: `agency`, `agency_role`, `authority_level`, `precedence_rank`) cited as the input to all four detector classes? [Traceability, Spec §FR-RAG-COORD-01 vs §FR-RAG-AG-04]

## Audit-Log Linkage (`conflict_group_id`)

> **Authority**: FR-RAG-COORD-01 + FR-RAG-AG-02 (audit shape) + Constitution Principle IV deterministic replay.

- [ ] CHK239 Is the `conflict_group_id` field shape specified (UUID? structured key? scope: per-incident, per-agent-pair, per-recommendation-batch?) and consistent with the AuditRecord schema in FR-RAG-AG-02? [Consistency, Spec §FR-RAG-COORD-01 vs §FR-RAG-AG-02]
- [ ] CHK240 Is the audit shape for a `conflict_detected` event listed (which fields, when emitted, what triggers reconciliation on resolution, how the event resolves to a closed state)? [Coverage, Spec §FR-RAG-COORD-01]
- [ ] CHK241 Is the determinism invariant ("every conflict event must be reproducible from `retrieved_chunks[] + prompt_sha`") testable from a replay run — i.e., does the spec mandate a replay test against historical conflict events? [Measurability / Acceptance Criteria, Spec §FR-RAG-COORD-01 vs §SC-011]

## AIIMS Escalation Chain (Ops Officer → IC → FC offline queue)

> **Authority**: FR-RAG-COORD-02 + Pass 1 Q-P1-03; AIIMS §II-A Control / Operations split; spec 029 FR-008 5-minute SLO pattern.

- [ ] CHK242 Is the AIIMS authority for first-recipient (**Ops Officer** owns Operations function for tactical resource arbitration) tied back to AIIMS §II-A Control / Operations split, with citation in FR-RAG-COORD-02? [Traceability, Spec §FR-RAG-COORD-02 vs Constitution §II-A]
- [ ] CHK243 Is the **5-minute unack timeout** measurable (clock start = `conflict_detected` event emission; clock stop = ack received OR escalation fires) and consistent with the spec-029 FR-008 5-minute pattern (avoiding accidental drift)? [Measurability, Spec §FR-RAG-COORD-02 vs `specs/029-progressive-delivery-pipeline/spec.md`]
- [ ] CHK244 Is the offline-FC fallback (queue conflict for IC review on reconnect; FC MUST NOT auto-resolve cross-agent conflicts) consistent with FR-RAG-LS-02 offline boundaries (i.e., FC's prohibited-offline list includes cross-agent conflict resolution)? [Consistency, Spec §FR-RAG-COORD-02 vs §FR-RAG-LS-02]
- [ ] CHK245 Is the `escalation_unack_timeout` audit-event emission specified (when emitted, payload shape, where it lands, how it relates to `conflict_group_id`)? [Acceptance Criteria, Spec §FR-RAG-COORD-02]

## Human-in-Loop Resolution (no AI auto-resolve)

> **Authority**: Constitution Principle I (no-silencing); FR-RAG-LS-01 human approval authority.

- [ ] CHK246 Is the no-AI-auto-resolution invariant stated as an unconditional constraint (Constitution Principle I) inside both FR-RAG-COORD-01 and FR-RAG-COORD-02 — not implied by reference to LS-01? [Coverage, Spec §FR-RAG-COORD-01 / §FR-RAG-COORD-02 vs Constitution §I]
- [ ] CHK247 Are the operator's possible resolution actions (accept agent A; accept agent B; accept both; reject both with manual override; defer pending more info) defined as a closed set so the audit log can record (b) "operator's resolution decision" deterministically? [Clarity, Spec §FR-RAG-COORD-02]

## Feature-Flag Reversibility (Reversible class)

> **Authority**: Pass 2 Q-P2-08 (Reversible class taxonomy); Assumption A12; spec 029 FR-008 5-minute reversibility SLO.

- [ ] CHK248 Is `feature.multi_agent_conflict_detection.enabled` (Reversible) classified consistently in FR-RAG-COORD-01 and Assumption A12 (no class drift between FR body and assumption)? [Consistency, Spec §FR-RAG-COORD-01 vs §A12]
- [ ] CHK249 Does the disable path preserve the no-silencing invariant — i.e., disabling coordination falls back to **single-agent behaviour**, never to a no-op (`conflict_group_id` not populated, but agents still emit recommendations)? [Coverage, Spec §FR-RAG-COORD-01 vs Constitution §I]

## Notes

- **Item count (this file)**: 20 items across 6 sections (CHK230–CHK249).
- **Cross-references**: Items in this file frequently cite FR-RAG-COORD-01/02, FR-RAG-AG-02 (`conflict_group_id` lands in AuditRecord), FR-RAG-AG-04 (disambiguation fields are the canonical "same-resource" signal), FR-RAG-LS-02 (offline FC boundaries), Assumption A12, spec 029 FR-008, spec 033 MAF agent-isolation model, AIIMS §II-A, and Constitution Principles I + IV.
- **Why this file is separate**: Multi-agent coordination is the **only** surface where a deterministic rule-based detector replaces what would naively be an AI-driven reconciliation. Splitting it out lets a reviewer with deep AIIMS-doctrine knowledge clear it in one pass without context-switching to corpus / index / cultural-authority topics.
- **Plan-phase deliverable**: ADR `18-multi-agent-conflict.md` stub at `docs/decisions/036-foundry-rag-grounding/` (per Assumption A11).
