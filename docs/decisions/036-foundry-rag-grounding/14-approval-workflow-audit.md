# ADR 14 — Approval Workflow Audit (Operator Override + Field-Coordinator Offline-Decision Boundaries)

**FR**: FR-RAG-AG-02 (audit field extensions), FR-RAG-LS-02 (Field Coordinator offline-decision boundaries)
**Cluster**: A5 — Audit log capture for operator override + approval workflow + offline autonomy
**Persona memo citation**: `personas-input/r3-operational.md` §"Observer-Auditor — operator-override traceability"; `personas-input/r3-sectors-territories.md` §"Field Coordinator offline autonomy"
**Approver**: AMA Spec-036 Architecture Review + Compliance Auditor
**Date**: 2026-05-08
**Status**: Stub — body authored in `/speckit.implement` (Phase F-A5 task)

## Stub placeholder

> Detailed rationale to land in implement-phase task `T-A5-ADR14` (planned). Body resolves the [NEEDS ADR] marker on FR-RAG-AG-02 and FR-RAG-LS-02.

## Skeleton (to be filled in `/speckit.implement`)

- **Context** — Audit shape needs (a) operator-override traceability when human modifies/rejects an LLM recommendation (Constitution Principle IV), (b) approval-workflow state machine for public-warning outputs (FR-RAG-LS-03), (c) downgrade rationale when IC reduces incident level, (d) Field Coordinator offline-decision boundaries (Constitution NN-5 graceful degradation).
- **Decision — Audit field extensions (FR-RAG-AG-02)** — Add to `AuditRecord`:
  - `operator_override_rationale` (nullable string; captured when operator modifies or rejects LLM recommendation)
  - `approval_workflow_state` (enum: `pending | approved | rejected`; tracks PIO/IC approval for public-facing outputs)
  - `approval_authority` (nullable string; identity of approving IC/PIO)
  - `downgrade_justification` (nullable string; captured when IC downgrades incident level)
  - `retrieval_index_name` (string; concrete AI-Search index name resolved at query start per FR-RAG-IDX-04a)
- **Decision — Migration (Pass 2 Q-P2-01)** — Additive, in-place, schema-on-read via existing `infra/scripts/migrate-audit-record-036.ps1` (Phase D2 task **T082** "additive fields only; preserve existing rows"); Cosmos tolerates missing fields on legacy rows so no migration window is required.
- **Decision — Field-Coordinator offline-decision boundaries (FR-RAG-LS-02 extension)** — Field Coordinator MAY make resource-allocation, safety-escalation, and evacuation-centre setup decisions while offline using cached doctrine (per persona memo + Constitution NN-5). Field Coordinator MUST NOT issue public warnings, request mutual aid across jurisdictions, or escalate to state/national level while offline (requires IC approval on reconnect). Each offline decision audited with `field_coordinator_offline_decision: true` and reconciled with `approval_workflow_state: "pending"` for IC review on reconnect.
- **Consequences** — Adds ≤5 nullable fields to `AuditRecord`; SC-017 measurable (`operator_override_rationale` in 100% of override events; `approval_workflow_state` in 100% of public-warning events). Closes Constitution Principle IV gap on operator overrides while preserving FR-RAG-LS-02 offline autonomy.

## Cross-references

- Cluster A5 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 2 Q-P2-01 in `specs/036-foundry-rag-grounding/spec.md` Session 5.
- Existing migration script `infra/scripts/migrate-audit-record-036.ps1` (Phase D2 task T082).
- Plan phase `F-A5` in `specs/036-foundry-rag-grounding/plan.md`.
