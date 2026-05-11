# ADR 15 — Federal Compliance Mapping (Privacy Act 1988 / ISM 2024 / PSPF / COMDISPLAN)

**FR**: FR-RAG-COMP-01, FR-RAG-COMP-02, FR-RAG-COMP-03, FR-RAG-COMP-04
**Cluster**: A6 — Federal Compliance
**Persona memo citation**: `personas-input/r3-sectors-commonwealth.md` §"NEMA / AGD / AFP federal alignment"; `personas-input/r3-operational.md` §"Observer-Auditor PSPF export"
**Approver**: HUMAN-IN-LOOP — NEMA + AGD + AFP federal sign-off (per A9)
**Date**: 2026-05-08
**Status**: Stub — body authored in `/speckit.implement` (Phase F-A6 task) AND federal sign-off

## Stub placeholder

> Detailed rationale to land in implement-phase task `T-A6-ADR15` (planned). Body authoring is GATED by federal sign-off (HUMAN-IN-LOOP per Assumption A9). This stub exists per Assumption **A11** so `[NEEDS ADR]` markers on FR-RAG-COMP-01..04 resolve to a real path at plan-review time.

## Skeleton (to be filled in `/speckit.implement` + federal sign-off)

- **Privacy Act 1988 mapping (FR-RAG-COMP-01)** — APP 1 (privacy policy published), APP 3 (operator PII collected only with consent), APP 5 (LLM output anonymised before logging where PII present), APP 6 (audit log accessible via SAR workflow), APP 11 (7-year retention with encryption at rest — already present per spec 030; citation added here).
- **ISM 2024 mapping (FR-RAG-COMP-02)** — ISM-0468 (TLS 1.2+ for all Foundry + AI Search connections — verified by Bicep-side `minTlsVersion: '1.2'`), ISM-1552 (audit log cryptographic integrity via cosign keyless + age detached signatures — already covered by spec 032 FR-AI09 + FR-RAG-LS-02 dual-signature pattern). Citation document: `docs/compliance/ISM-2024-mapping.md` (NEW, body authored in implement phase).
- **PSPF compliance (FR-RAG-COMP-03)** — Observer-Auditor MUST be able to export audit logs in PSPF-compliant CSV format with mandated column headers: `Timestamp, User, Action, Resource, Outcome, Justification`. Export endpoint: `GET /api/audit/export?format=pspf&start=...&end=...`. Existing audit shape (FR-RAG-AG-02 + ADR-14 amend-loop additions) provides every column without further schema change.
- **COMDISPLAN activation flow (FR-RAG-COMP-04)** — Retrieval scope prioritisation when `national_emergency_active` flag is set: Commonwealth COMDISPLAN doctrine ranked above state/territory guidance for the declared hazard type + impacted jurisdictions. Implemented via the precedence-ranking mechanism in ADR-13 by elevating `authority_level=commonwealth` chunks to `precedence_rank=1` for the duration of the activation. Activation signal comes from existing `national_emergency_active` flag in the incident context (per spec 029).
- **HUMAN-IN-LOOP gates** — Per Assumption A9: federal compliance attestations (Privacy Act + ISM 2024 + PSPF) require human-in-loop sign-off (NEMA, AGD, AFP, AIATSIS) which the codebase scaffolds but does not autonomously complete. Tasks for sign-off acquisition are tracked in `tasks.md` Phase F-A6.

## Cross-references

- Cluster A6 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- New compliance doc `docs/compliance/ISM-2024-mapping.md` (created in implement phase).
- ADR-13 (authority precedence) for COMDISPLAN ranking interlock.
- ADR-14 (audit shape) for PSPF column coverage.
- Plan phase `F-A6` in `specs/036-foundry-rag-grounding/plan.md`.
