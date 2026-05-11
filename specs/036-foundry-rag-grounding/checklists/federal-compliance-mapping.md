# Federal Compliance Mapping Checklist: Microsoft Foundry-Based RAG Grounding

**Purpose**: Validate that the federal-compliance requirements (Privacy Act 1988 APPs, ISM 2024 controls, PSPF audit export, COMDISPLAN activation ranking) are specified to a level a federal compliance reviewer (AGD / OAIC / ASD / NEMA aligned) can verify before planning, including the HUMAN-IN-LOOP sign-off chain.
**Created**: 2026-05-09 (post R3 amend loop Sessions 3 + 4 + 5)
**Feature**: [spec.md](../spec.md)
**Cluster**: A6 (Federal compliance [partial HUMAN-IN-LOOP])
**Companion checklists**:
- [requirements.md](./requirements.md) — Spec quality fundamentals
- [compliance.md](./compliance.md) — Constitution alignment, data residency, opt-out audit, index lifecycle, offline cache (extended for A4/A7/A8)
- [audit-and-approval-workflow.md](./audit-and-approval-workflow.md) — AG-02 audit-shape extensions
- [cultural-authority-protocols.md](./cultural-authority-protocols.md) — Constitution VI-C cultural authority

> **Scope of this file**: The four FR families that bind the platform to **federal regulatory baselines**: **Privacy Act 1988** (FR-RAG-COMP-01: APPs 1, 3, 5, 6, 11), **ISM 2024** (FR-RAG-COMP-02: ISM-0468 TLS 1.2+; ISM-1552 cosign + detached signature), **PSPF** (FR-RAG-COMP-03: audit export endpoint with PSPF-mandated CSV columns), **COMDISPLAN** (FR-RAG-COMP-04: retrieval ranking change on `national_emergency_active`).

> **Item numbering**: Continues from `cultural-authority-protocols.md` (CHK187+).

> **HUMAN-IN-LOOP markers**: Items prefixed `[HUMAN-IN-LOOP — <Authority>]` identify the responsible federal authority whose sign-off the AI workflow cannot autonomously close. Authorities recognised in Assumption A9: **AGD** (Attorney-General's Department), **OAIC** (Office of the Australian Information Commissioner — Privacy Act), **ASD** (Australian Signals Directorate — ISM), **NEMA** (National Emergency Management Agency — COMDISPLAN), **AFP** (classification carve-outs).

## Privacy Act 1988 APPs Coverage

> **Authority**: FR-RAG-COMP-01 + Constitution Principle IV; HUMAN-IN-LOOP per Assumption A9.

- [ ] CHK187 Are the five APPs (**APP 1** — privacy policy publication; **APP 3** — consent-gated PII collection; **APP 5** — PII anonymisation in LLM output before logging; **APP 6** — audit log accessible via Subject Access Request workflow; **APP 11** — 7-year encrypted retention) each tied to a measurable behaviour in FR-RAG-COMP-01? [Completeness, Spec §FR-RAG-COMP-01]
- [ ] CHK188 Is the "7-year retention with encryption at rest" (APP 11) requirement consistent with spec 030's existing retention policy — and is that citation traceable to a specific spec-030 FR? [Traceability, Spec §FR-RAG-COMP-01 vs `specs/030-llm-eval-framework/spec.md`]
- [ ] CHK189 [HUMAN-IN-LOOP — AGD / OAIC] Is the federal sign-off authority chain for FR-RAG-COMP-01 named (Office of the Australian Information Commissioner; AGD) so HUMAN-IN-LOOP work can be tracked in `tasks.md`? [Clarity, Spec §FR-RAG-COMP-01 vs §A9]
- [ ] CHK190 Is the SAR (Subject Access Request) workflow scope defined — endpoint name, response SLA, what data classes are included/excluded, and how PII anonymisation under APP 5 interacts with SAR fulfilment? [Gap, Spec §FR-RAG-COMP-01]
- [ ] CHK191 Is the consent boundary (APP 3) measurable — does the spec define what counts as "operator PII" (operator_id alone? plus name? plus role)? [Clarity, Spec §FR-RAG-COMP-01]

## ISM 2024 Controls Coverage

> **Authority**: FR-RAG-COMP-02 + Constitution NN-2; HUMAN-IN-LOOP per Assumption A9.

- [ ] CHK192 Are **ISM-0468** (TLS 1.2+ on Foundry + AI Search) and **ISM-1552** (cosign + detached-signature audit-log integrity) cited with explicit control IDs and not described in prose-only? [Traceability, Spec §FR-RAG-COMP-02]
- [ ] CHK193 Is the new document `docs/compliance/ISM-2024-mapping.md` named, scoped, and tied to a deliverable owner — and does SC-018 verify both its existence AND that the two named controls are referenced inside it? [Coverage, Spec §FR-RAG-COMP-02 / §SC-018]
- [ ] CHK194 [HUMAN-IN-LOOP — AGD / ASD / Defence] Is the ISM-2024 sign-off authority chain identified for the federal HUMAN-IN-LOOP step? [Clarity, Spec §FR-RAG-COMP-02 vs §A9]
- [ ] CHK195 Are ISM controls beyond ISM-0468 and ISM-1552 (e.g., ISM-1175 access logging, ISM-1379 cryptographic-protection-in-transit, ISM-1546 system-event logging) considered, OR is the scope explicitly limited to those two with rationale? [Coverage, Gap, Spec §FR-RAG-COMP-02]
- [ ] CHK196 Is the cryptographic-integrity tie between FR-RAG-COMP-02 (ISM-1552 audit-log integrity) and FR-RAG-LS-02 (offline cache dual-signature) consistent — same cosign keyless chain, same age-encrypted detached signature pattern? [Consistency, Spec §FR-RAG-COMP-02 vs §FR-RAG-LS-02]

## PSPF Audit Export Contract

> **Authority**: FR-RAG-COMP-03 + Observer-Auditor persona + Constitution Principle IV.

- [ ] CHK197 Is the PSPF export endpoint contract (`GET /api/audit/export?format=pspf&start=...&end=...`) specified with mandatory query parameters, response shape, content-type, and authentication? [Clarity, Spec §FR-RAG-COMP-03]
- [ ] CHK198 Are the PSPF-mandated CSV column headers (**Timestamp, User, Action, Resource, Outcome, Justification**) defined consistently with the AuditRecord field shape in FR-RAG-AG-02 (e.g., is `Justification` derived from `operator_override_rationale` or `downgrade_justification` or both)? [Consistency, Spec §FR-RAG-COMP-03 vs §FR-RAG-AG-02]
- [ ] CHK199 Is the export-time authorisation requirement specified — who can call the endpoint (Observer-Auditor only? PIO? IC?), and is RBAC mapped to a named role? [Gap, Spec §FR-RAG-COMP-03]
- [ ] CHK200 Are export-volume / pagination / streaming behaviours specified for large date ranges so a multi-month export does not exhaust the API node? [Edge Case, Gap, Spec §FR-RAG-COMP-03]
- [ ] CHK201 Is the export's PSPF classification level bounded — does the export support OFFICIAL only, or also OFFICIAL:Sensitive, and is the boundary aligned with the FR-RAG-NS-07 classification carve-out? [Coverage, Spec §FR-RAG-COMP-03 vs §FR-RAG-NS-07]

## COMDISPLAN Activation Ranking

> **Authority**: FR-RAG-COMP-04 + spec 029 progressive-delivery pattern; NEMA persona memo.

- [ ] CHK202 Is the `national_emergency_active` flag (per spec 029) consistently named and traceable from FR-RAG-COMP-04 to its source in spec 029? [Traceability, Spec §FR-RAG-COMP-04 vs `specs/029-progressive-delivery-pipeline/spec.md`]
- [ ] CHK203 Is FR-RAG-COMP-04's "retrieval ranking change, not a carve-out" disambiguated from the FR-RAG-NS-* RAG-opt-outs so reviewers do not conflate the two mechanisms? [Clarity, Spec §FR-RAG-COMP-04 vs §FR-RAG-NS-*]
- [ ] CHK204 Is the interaction between COMDISPLAN-prioritised ranking (FR-RAG-COMP-04) and FR-RAG-AG-04's authority-precedence ranking specified — does COMDISPLAN bump precedence, override it, or stack with it? [Consistency, Spec §FR-RAG-COMP-04 vs §FR-RAG-AG-04]
- [ ] CHK205 Is the deactivation behaviour specified — when `national_emergency_active` flips back to `false`, does retrieval ranking revert immediately, or is a grace window applied (and is that grace window auditable)? [Edge Case, Gap, Spec §FR-RAG-COMP-04]
- [ ] CHK206 [HUMAN-IN-LOOP — NEMA] Is NEMA's COMDISPLAN-activation authority cited as the trigger, with a clear interface contract (who flips the flag, where the audit lands)? [Traceability, Spec §FR-RAG-COMP-04 vs §A9]

## Notes

- **Item count (this file)**: 20 items across 4 sections (CHK187–CHK206).
- **Cross-references**: Items in this file frequently cite spec 029 (`specs/029-progressive-delivery-pipeline/spec.md`), spec 030 (`specs/030-llm-eval-framework/spec.md`), Assumptions A9 (HUMAN-IN-LOOP authorities) and A11 (ADR lifecycle), `docs/compliance/ISM-2024-mapping.md` (NEW), the AuditRecord shape in FR-RAG-AG-02, and FR-RAG-NS-07 classification carve-out.
- **Why this file is separate**: The federal-compliance authority chain (AGD + OAIC + ASD + NEMA) is distinct from the Constitution VI-C cultural-authority chain (AIATSIS + Land Councils + community representatives). Splitting these checklists means a federal compliance reviewer can clear FR-RAG-COMP-* in one pass without context-switching to cultural-authority gating.
- **Plan-phase deliverable**: ADR `15-federal-compliance-mapping.md` stub at `docs/decisions/036-foundry-rag-grounding/` (per Assumption A11).
- **Document deliverable**: `docs/compliance/ISM-2024-mapping.md` (NEW; HUMAN-IN-LOOP federal sign-off required per FR-RAG-COMP-02).
