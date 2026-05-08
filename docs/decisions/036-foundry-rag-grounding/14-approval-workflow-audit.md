# ADR 14 — Approval Workflow Audit (Operator Override + Field-Coordinator Offline-Decision Boundaries)

**FR**: FR-RAG-AG-02 (audit field extensions), FR-RAG-LS-02 (Field Coordinator offline-decision boundaries)
**Cluster**: A5 — Audit log capture for operator override + approval workflow + offline autonomy
**Persona memo citation**: `personas-input/r3-operational.md` §"Observer-Auditor — operator-override traceability"; `personas-input/r3-sectors-territories.md` §"Field Coordinator offline autonomy"
**Approver**: AMA Spec-036 Architecture Review + Compliance Auditor
**Date**: 2026-05-08
**Status**: Accepted — body authored 2026-05-15 (Phase F-A5)

## Context

The Phase D `AuditRecord` shape was sufficient for raw retrieval and inference traceability but missed four operator-facing concerns that surfaced in the R3 amend loop:

1. **Operator-override traceability** (Constitution Principle IV — "human override remains explainable"). A handler who modifies or rejects an LLM recommendation must leave a typed rationale, not just a free-text comment, so Observer-Auditor reviews can aggregate override patterns.
2. **Approval-workflow state for public-facing outputs** (FR-RAG-LS-03). Public-warning text drafted by an LLM must traverse a `pending → approved | rejected` state with a named PIO/IC approver before egress.
3. **Downgrade rationale.** When an Incident Controller reduces an incident level (AIIMS step-down), the rationale needs to be machine-readable for after-action review.
4. **Field-Coordinator offline boundaries** (FR-RAG-LS-02 extension; Constitution NN-5). Offline operation enables continuity but must not be a path to public-warning issuance, mutual-aid requests, or AIIMS escalation without later IC reconciliation.

Pass 2 Q-P2-01 settled the migration policy as additive-nullable (no in-place rewrite) — Cosmos tolerates missing fields on legacy rows, so a long migration window is unnecessary.

## Decision

1. **Eight new nullable fields** on `AuditRecord` (additive — see `contracts/audit-record-llm-call.json` extension):
   - `operator_override_rationale` (string, nullable). Captured when the operator modifies or rejects the LLM recommendation.
   - `operator_override_action` (enum, nullable: `modify | reject | accept-with-comment`).
   - `approval_workflow_state` (enum: `pending | approved | rejected`, nullable). Tracks PIO/IC approval for public-warning outputs.
   - `approval_authority` (string, nullable). Identity of the approving IC/PIO (employee identifier).
   - `approval_decided_at` (ISO-8601, nullable).
   - `downgrade_justification` (string, nullable). Captured when an IC reduces an incident level.
   - `field_coordinator_offline_decision` (boolean, default `false`). True when the audit row was emitted by an offline Field Coordinator using cached doctrine.
   - `retrieval_index_name` (string). Concrete AI Search index name resolved at query start (FR-RAG-IDX-04a; required for blue-green replay).
2. **Migration**: additive in place via the existing `infra/scripts/migrate-audit-record-036.ps1` script (Phase D2 / T082). No data is rewritten; legacy rows continue to read with the new fields as `null`. Schema-on-read.
3. **Field-Coordinator offline boundaries** (FR-RAG-LS-02 extension):
   - **MAY** while offline: resource allocation, safety escalation, evacuation-centre setup using cached doctrine.
   - **MUST NOT** while offline: public-warning issuance, cross-jurisdiction mutual-aid requests, AIIMS escalation to state/national level. These require IC approval on reconnect.
   - Each offline decision is audited with `field_coordinator_offline_decision: true` and an `approval_workflow_state: "pending"` placeholder so the IC can reconcile on reconnect.
4. **Audit emitter** (`apps/api/app/repositories/audit_repository.py` + `apps/api/app/services/audit_emitter.py`) is the single writer; producers (RetrievalService, FoundryClient, conflict-detector, escalation chain) all flow through it so the new fields are populated consistently.

## Rationale

- **Why eight fields, not one omnibus dict?** Cosmos containers index fields by name; flattening into a `metadata: dict` blob breaks the indexed-query path used by Observer-Auditor dashboards.
- **Why nullable, not required?** Required fields would force a backfill of millions of legacy rows. Pass 2 Q-P2-01 explicitly rejected this in favour of schema-on-read.
- **Why split `approval_workflow_state` from `approval_authority` from `approval_decided_at`?** Aggregations need to ask different questions ("how many pending?", "who approved most last week?", "what is the median pending-to-approved latency?") that one field cannot answer simultaneously.
- **Why bake offline boundaries into the audit shape rather than a service guard?** The audit shape *is* the contract — anything the rest of the system observes must be consistent with what audit captures. Putting the boundary in the audit-record schema makes "MAY/MUST NOT while offline" enforceable at write time.
- **Why include `retrieval_index_name`?** Spec 014 SC-011 byte-identical replay requires resolving the *exact* index that served the query, not the alias. F-A7 (T166–T172) pins the resolved name; this field is the audit-side counterpart.

## Consequences

**Positive**
- SC-017 (Observer-Auditor traceability) becomes measurable: `operator_override_rationale` non-null in 100 % of override events; `approval_workflow_state` non-null in 100 % of public-warning events.
- Constitution Principle IV gap closed on operator overrides.
- Field Coordinator offline autonomy preserved without ambiguity (FR-RAG-LS-02 + Constitution NN-5 + persona memo align).
- Replay path is unambiguous: `retrieval_index_name` plus `corpus_build_sha` plus `embedding_model_id` is sufficient to reproduce any retrieval byte-identically.

**Negative / mitigations**
- ~ 200 bytes/record added when fields are populated. Acceptable: ≈ 250 MB/year at 5 RPS.
- Eight new fields multiplies the surface for typos in producers. Mitigated by a strict pydantic model in `packages/domain/src/domain/audit_record.py` and by the contract test `tests/contract/test_audit_record_llm_call.py` (T156–T159) that runs on every PR.
- Observer-Auditor dashboards must learn the new fields. Mitigated by ADR cross-reference in the dashboard docs and by SC-017 acceptance criteria already exercising every field.

## Cross-references

- Cluster A5 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 2 Q-P2-01 in spec.md Session 5.
- Existing migration script `infra/scripts/migrate-audit-record-036.ps1` (Phase D2 / T082).
- Tasks T156–T165; producers wired in F-A7 (T166–T172) for `retrieval_index_name`, F-A9 (T225–T231) for conflict-detector audits, F-A11 (T232–T238) for OTel correlation.
- Plan phase F-A5 in `specs/036-foundry-rag-grounding/plan.md`.
- ADR 18 (multi-agent conflict) consumes `approval_workflow_state` for AIIMS escalation reconciliation.
