# Audit & Approval-Workflow Checklist: Microsoft Foundry-Based RAG Grounding

**Purpose**: Validate that the FR-RAG-AG-02 audit-shape extensions (operator override rationale, approval workflow state, downgrade justification, retrieval index name) and the FR-RAG-LS-02 Field Coordinator offline-decision boundaries are specified to a level the Observer-Auditor + Compliance Auditor + Field Coordinator personas can verify before planning.
**Created**: 2026-05-09 (post R3 amend loop Sessions 3 + 4 + 5)
**Feature**: [spec.md](../spec.md)
**Cluster**: A5 (Audit/approval workflow) + A10 (T082 additive migration) + A12 (Locked-on flag class for AG-02)
**Companion checklists**:
- [compliance.md](./compliance.md) — Constitution alignment, data residency, opt-out audit, index lifecycle, offline cache
- [federal-compliance-mapping.md](./federal-compliance-mapping.md) — Privacy Act / ISM / PSPF / COMDISPLAN
- [multi-agent-coordination.md](./multi-agent-coordination.md) — FR-RAG-COORD-* conflict + escalation chain (consumes AG-02 audit shape)

> **Scope of this file**: The audit-and-approval surface added by the R3 amend loop: **AuditRecord field extensions** (FR-RAG-AG-02 new fields), **operator override rationale capture**, **approval workflow state machine**, **Field Coordinator offline decision boundaries** (FR-RAG-LS-02 extensions), **schema migration strategy** (T082 additive in-place), **feature-flag reversibility** (AG-02 fields are Locked-on in prod).

> **Item numbering**: Continues from `federal-compliance-mapping.md` (CHK207+).

## AuditRecord Field Extensions

> **Authority**: FR-RAG-AG-02 (R3 Cluster A5); Pass 2 Q-P2-01 (T082 additive migration); Constitution Principle IV.

- [ ] CHK207 Are the new AG-02 fields (`operator_override_rationale`, `approval_workflow_state`, `approval_authority`, `downgrade_justification`, `retrieval_index_name`) listed with type, nullability, and emission trigger (when populated, when null) so a Cosmos schema is implementable from the spec alone? [Completeness, Spec §FR-RAG-AG-02]
- [ ] CHK208 Is `approval_workflow_state` enum (`pending|approved|rejected`) closed and exhaustive — or is a `withdrawn` / `expired` / `superseded` state intentionally absent (with rationale)? [Clarity, Spec §FR-RAG-AG-02]
- [ ] CHK209 Is the new `retrieval_index_name` field (recording the concrete index name resolved at query start, FR-RAG-IDX-04a) consistent with the existing `corpus_build_sha` provenance pair so blue-green replay reconstruction is unambiguous? [Consistency, Spec §FR-RAG-AG-02 vs §FR-RAG-IDX-04a]
- [ ] CHK210 Are the AuditRecord field additions reflected in the `Key Entities › AuditRecord (LLM-call)` block, or is the spec inconsistent between FR-RAG-AG-02 prose and §Key Entities listing? [Consistency, Spec §FR-RAG-AG-02 vs §Key Entities]

## Operator Override Rationale Capture

> **Authority**: FR-RAG-AG-02 + SC-017 + Constitution Principle IV.

- [ ] CHK211 Is the trigger for `operator_override_rationale` capture defined precisely — does "modifies or rejects LLM recommendation" include partial edits, full rejection, accept-with-comment, accept-and-defer, or only one of those? [Clarity, Spec §FR-RAG-AG-02]
- [ ] CHK212 Is the rationale-text validation specified (minimum length, free-text vs. structured, mandatory vs. optional) so audit reviewers can rely on its informativeness rather than receiving empty strings? [Gap, Spec §FR-RAG-AG-02]
- [ ] CHK213 Is SC-017's "100% of override events" measurable from the audit log alone (e.g., a query that joins override events to the rationale field returns no nulls)? [Measurability, Spec §SC-017 vs §FR-RAG-AG-02]
- [ ] CHK214 Is the override-rationale field's relationship to PSPF "Justification" column (FR-RAG-COMP-03) defined — same field, derived field, or distinct fields? [Consistency, Spec §FR-RAG-AG-02 vs §FR-RAG-COMP-03]

## Approval Workflow State Machine

> **Authority**: FR-RAG-AG-02 + FR-RAG-LS-03 (public-facing outputs) + Constitution Quality Gates.

- [ ] CHK215 Is the state-machine for `approval_workflow_state` defined — allowed transitions (pending→approved, pending→rejected; can rejected→pending be reopened?) and authority required for each transition? [Coverage, Spec §FR-RAG-AG-02]
- [ ] CHK216 Is `approval_authority` (identity of approving IC/PIO) tied to a role-based authoritative list, or any logged-in operator? [Clarity, Spec §FR-RAG-AG-02]
- [ ] CHK217 Is SC-017's "100% of public-warning events have approval_workflow_state" tied to which public-warning emission paths (FR-RAG-AG-06 Communication agent, FR-RAG-LS-03 public-facing outputs, FR-RAG-SIM-05 simulation watermarking)? [Coverage, Spec §SC-017 vs §FR-RAG-AG-06 / §FR-RAG-LS-03 / §FR-RAG-SIM-05]
- [ ] CHK218 Is `downgrade_justification` triggered only when "IC downgrades incident level" — and is "incident level" defined (AIIMS levels 1-3, plus extension to spec-029 emergency tiers)? [Clarity, Spec §FR-RAG-AG-02]
- [ ] CHK219 Is the draft-vs-final audit chain (FR-RAG-LS-03) preserved with the new approval fields — i.e., does the audit record both the LLM-grounded draft AND the human-approved final, with `approval_workflow_state` tracking the transition? [Consistency, Spec §FR-RAG-LS-03 vs §FR-RAG-AG-02]

## Field Coordinator Offline Decision Boundaries

> **Authority**: FR-RAG-LS-02 (R3 Cluster A5); Pass 1 Q-P1-03 (offline conflict queue); Constitution Principle I + Principle IV.

- [ ] CHK220 Are the FC's permitted-offline decisions (resource allocation, safety escalation, evacuation centre setup) and prohibited-offline decisions (public warnings, mutual-aid requests across jurisdictions, state/national escalation) listed exhaustively in FR-RAG-LS-02 — no "etc." that could re-admit excluded scope? [Completeness, Spec §FR-RAG-LS-02]
- [ ] CHK221 Is the reconnect-time IC review flow specified — the event shape, the queue location, the SLA for IC review before queued decisions become operational? [Acceptance Criteria, Spec §FR-RAG-LS-02]
- [ ] CHK222 Is the boundary between FR-RAG-LS-02 offline decisions and FR-RAG-COORD-02 conflict escalation defined — i.e., when offline FC encounters a conflict (per Pass 1 Q-P1-03), is the queue-then-escalate path consistent across both FRs? [Consistency, Spec §FR-RAG-LS-02 vs §FR-RAG-COORD-02]
- [ ] CHK223 Is the offline cache TTL (14 days, per FR-RAG-LS-02 dual-signature requirement) consistent with the offline-decision-window the FC is permitted to act within (does the 14-day TTL bound the offline decision authority)? [Consistency, Spec §FR-RAG-LS-02 internal]

## Schema Migration Strategy (T082 additive)

> **Authority**: Pass 2 Q-P2-01 (three-tier strategy); Assumption A10; existing T082 migration script.

- [ ] CHK224 Is the T082 migration script's "additive fields only; preserve existing rows" guarantee restated in FR-RAG-AG-02 itself — not just in Assumption A10 narrative? [Clarity, Spec §FR-RAG-AG-02 vs §A10]
- [ ] CHK225 Is the schema-on-read tolerance for legacy nullable fields explicit so Cosmos readers cannot crash on missing fields (a contract test that asserts a legacy AuditRecord without the new fields can be read without throwing)? [Measurability, Spec §FR-RAG-AG-02 / §A10]
- [ ] CHK226 Is the no-migration-window guarantee testable — i.e., does the spec mandate a regression test that exercises read paths over both legacy and amended row shapes? [Coverage, Spec §FR-RAG-AG-02]

## Feature-Flag Reversibility (Locked-on for AG-02)

> **Authority**: Assumption A12 (Locked-on class); Constitution Principle IV provable provenance.

- [ ] CHK227 Are AG-02's audit-field additions classified as "**Locked-on**" in A12 — and is the Locked-on rationale (Constitution Principle IV provable provenance) explicit so a future contributor cannot silently demote them to Reversible? [Traceability, Spec §A12 vs Constitution §IV]
- [ ] CHK228 Is the `audit.feature_flag_change` event for any AG-02-affecting flag flip specified with required fields (`flag_name`, `old_value`, `new_value`, `actor_id`, `change_reason`)? [Completeness, Spec §A12]
- [ ] CHK229 [HUMAN-IN-LOOP — Compliance Auditor] Is there a stated compliance-auditor sign-off requirement for any change to AG-02 audit-shape (flag flip, new field, removed field) so audit-chain stability is governed and not informal? [Gap, Spec §FR-RAG-AG-02 / §A12]

## Notes

- **Item count (this file)**: 23 items across 6 sections (CHK207–CHK229).
- **Cross-references**: Items in this file frequently cite FR-RAG-AG-02 (extended), FR-RAG-LS-02 (extended), FR-RAG-LS-03, FR-RAG-IDX-04a, FR-RAG-COMP-03, FR-RAG-COORD-02, SC-017, Assumptions A10 + A12, the existing `infra/scripts/migrate-audit-record-036.ps1` script (T082), and Constitution Principles I + IV.
- **Why this file is separate**: The audit-and-approval surface is consumed by **multiple downstream checklists** (federal-compliance for PSPF export shape; multi-agent-coordination for `conflict_group_id` linkage; cultural-authority for `cultural_authority_*` events). Centralising it here means each downstream file references a single source of truth instead of redefining the AG-02 shape.
- **Plan-phase deliverable**: ADR `14-approval-workflow-audit.md` stub at `docs/decisions/036-foundry-rag-grounding/` (per Assumption A11).
