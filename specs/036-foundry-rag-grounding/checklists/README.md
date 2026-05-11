# Checklist Index — Microsoft Foundry-Based RAG Grounding (spec 036)

**Feature**: [spec.md](../spec.md)
**Last refreshed**: 2026-05-09 (post-R3 amend loop Sessions 3 + 4 + 5)

This directory contains 10 checklists totalling **339 items** that validate the **requirements quality** ("unit tests for English") of `spec.md`. Items are numbered globally (CHK001–CHK339) and never collide between files.

> **Reading principle**: Each `CHK###` item interrogates whether a requirement is **written well** (complete, clear, consistent, measurable, traceable) — NOT whether the implementation behaves correctly. Markers like `[Gap]`, `[Ambiguity]`, `[Conflict]`, `[Assumption]`, `[Edge Case]`, `[HUMAN-IN-LOOP — <Authority>]` flag the quality dimension under test.

## Pre-R3 Checklists (CHK001–CHK165) — Phase E resolved at T149

| File | Range | Items | Scope |
|---|---|---|---|
| [requirements.md](./requirements.md) | CHK001–CHK082 + CHK297–CHK309 | 82 + 13 | Spec quality fundamentals (Content / Completeness / Clarity / Consistency / Acceptance / Coverage / Persona / Cross-Spec / OOS / Traceability) **+ post-R3 spec-quality items** |
| [migration.md](./migration.md) | CHK083–CHK113 + CHK310–CHK319 | 31 + 10 | Foundry cutover safety (FR-RAG-FM-06), test instrumentation (FR-RAG-FM-07), citation contract end-to-end (token shape, audit doc → UI → SSE) **+ post-R3 citation/audit contract under new fields** |
| [compliance.md](./compliance.md) | CHK114–CHK165 + CHK320–CHK339 | 52 + 20 | Constitution alignment (Principle I / IV / V / VI-C / NN-2), data residency, no-RAG opt-out audit trail, index lifecycle, offline cache integrity **+ post-R3 OPA carve-out quorum / alias atomicity / corpus freshness** |

## Post-R3 Domain Checklists (CHK166–CHK296) — created 2026-05-09

These checklists were created to validate the **25 new FRs**, **2 new User Stories**, **7 new Success Criteria**, **1 new OOS**, and **4 new Assumptions** added by the R3 Persona Review Amend Loop (Session 3) plus its Pass 1 (Session 4) and Pass 2 (Session 5) refinements.

| File | Range | Items | Cluster | Authority chain (HUMAN-IN-LOOP) |
|---|---|---|---|---|
| [cultural-authority-protocols.md](./cultural-authority-protocols.md) | CHK166–CHK186 | 21 | A2 + Pass 1 Q-P1-01 + Pass 2 Q-P2-02 / Q-P2-08 | NEMA + AFAC + AIATSIS + ALT + APY + Land Councils + Indigenous community representatives |
| [federal-compliance-mapping.md](./federal-compliance-mapping.md) | CHK187–CHK206 | 20 | A6 | AGD + OAIC (Privacy Act) + ASD (ISM) + NEMA (COMDISPLAN) + AFP (classification) |
| [audit-and-approval-workflow.md](./audit-and-approval-workflow.md) | CHK207–CHK229 | 23 | A5 + A10 + A12 | Compliance Auditor + Observer-Auditor (audit-shape change sign-off) |
| [multi-agent-coordination.md](./multi-agent-coordination.md) | CHK230–CHK249 | 20 | A9 + Pass 1 Q-P1-03 + Pass 2 Q-P2-06 / Q-P2-08 | (No HUMAN-IN-LOOP authority — runtime escalation Ops Officer → IC → FC offline queue) |
| [test-coverage-windows.md](./test-coverage-windows.md) | CHK250–CHK269 | 20 | A10 + Pass 1 Q-P1-07/08 + Pass 2 Q-P2-04 | (No HUMAN-IN-LOOP — QA + Principal Engineer reviewer scope) |
| [observability.md](./observability.md) | CHK270–CHK284 | 15 | A11 + Pass 1 Q-P1-06 + Pass 2 Q-P2-05 | (No HUMAN-IN-LOOP — Solution Architect + Principal Engineer reviewer scope) |
| [accessibility.md](./accessibility.md) | CHK285–CHK296 | 12 | A12 | ARC accessibility advisor + Auslan / Easy-Read / TIS-National consultants |

## Post-R3 Extension Sections (CHK297–CHK339)

These sections **append** to the three pre-R3 checklists; pre-R3 item numbers (CHK001–CHK165) remain unchanged.

| File | Extension Range | Items | Scope |
|---|---|---|---|
| `requirements.md` | CHK297–CHK309 | 13 | US9/US10 priority quality, SC-013..SC-019 traceability, new FR family headings, A9–A12 testability, ADR lifecycle (A11), deterministic-replay invariant (SC-011) |
| `migration.md` | CHK310–CHK319 | 10 | Citation contract under new chunk-metadata fields (`agency`, `agency_role`, `authority_level`, `precedence_rank`); audit contract under new AuditRecord fields (`retrieval_index_name`, `conflict_group_id`); test-seam compatibility; cutover compatibility with T082 + blue-green schema migration |
| `compliance.md` | CHK320–CHK339 | 20 | OPA carve-out quorum (A4: prod ≥3 / dev ≥2), blue-green alias atomicity (A7: in-flight queries + 5-min rollback SLO), corpus freshness (A8: nightly drift detection + UI/alert thresholds) |

## R3 Cluster → Checklist Coverage Map

| Cluster | Description | Primary Checklist | Extends | New FRs Covered |
|---|---|---|---|---|
| **A1** | Agency disambiguation | `requirements.md` post-R3 (CHK297–CHK309) + `migration.md` post-R3 (CHK310) | requirements.md, migration.md | FR-RAG-AG-04 fields |
| **A2** | Cultural authority [HUMAN-IN-LOOP] | `cultural-authority-protocols.md` (CHK166–CHK186) | (new file) | FR-RAG-CA-01..05 |
| **A3** | ACT–Commonwealth precedence | `requirements.md` post-R3 + `multi-agent-coordination.md` (CHK238) | requirements.md | FR-RAG-AG-04 fields, FR-RAG-AC-01 |
| **A4** | Carve-out quorum fix | `compliance.md` post-R3 (CHK320–CHK325) | compliance.md | FR-RAG-CV-01 |
| **A5** | Audit/approval workflow | `audit-and-approval-workflow.md` (CHK207–CHK229) | (new file) | FR-RAG-AG-02 fields, FR-RAG-LS-02 ext |
| **A6** | Federal compliance [partial HUMAN-IN-LOOP] | `federal-compliance-mapping.md` (CHK187–CHK206) | (new file) | FR-RAG-COMP-01..04 |
| **A7** | Blue-green alias atomicity | `compliance.md` post-R3 (CHK326–CHK332) | compliance.md | FR-RAG-IDX-04a, FR-RAG-IDX-09 |
| **A8** | Corpus staleness | `compliance.md` post-R3 (CHK333–CHK339) | compliance.md | FR-RAG-IDX-05a, FR-RAG-FRESH-01/02 |
| **A9** | Multi-agent conflict | `multi-agent-coordination.md` (CHK230–CHK249) | (new file) | FR-RAG-COORD-01/02 |
| **A10** | Test coverage | `test-coverage-windows.md` (CHK250–CHK269) | (new file) | FR-RAG-TEST-01..04 |
| **A11** | Observability | `observability.md` (CHK270–CHK284) | (new file) | FR-RAG-OBS-01..03 |
| **A12** | Accessibility | `accessibility.md` (CHK285–CHK296) | (new file) | FR-RAG-UI-01 |

## Per-FR Coverage Map (new FRs only)

| New FR | Primary Checklist | Item Range |
|---|---|---|
| FR-RAG-CA-01 | cultural-authority-protocols.md | CHK166, CHK168, CHK169 |
| FR-RAG-CA-02 | cultural-authority-protocols.md | CHK166, CHK167, CHK184 |
| FR-RAG-CA-03 | cultural-authority-protocols.md | CHK166, CHK169 |
| FR-RAG-CA-04 | cultural-authority-protocols.md | CHK170–CHK183, CHK186 |
| FR-RAG-CA-05 | cultural-authority-protocols.md | CHK173, CHK184–CHK185 |
| FR-RAG-AC-01 | multi-agent-coordination.md (CHK238) + requirements.md post-R3 | CHK238, CHK304, CHK307 |
| FR-RAG-COMP-01 | federal-compliance-mapping.md | CHK187–CHK191 |
| FR-RAG-COMP-02 | federal-compliance-mapping.md | CHK192–CHK196 |
| FR-RAG-COMP-03 | federal-compliance-mapping.md | CHK197–CHK201 |
| FR-RAG-COMP-04 | federal-compliance-mapping.md | CHK202–CHK206 |
| FR-RAG-IDX-04a | compliance.md post-R3 | CHK326–CHK327, CHK332; also migration.md CHK313 |
| FR-RAG-IDX-05a | compliance.md post-R3 | CHK333–CHK335 |
| FR-RAG-IDX-09 | compliance.md post-R3 | CHK328–CHK331 |
| FR-RAG-FRESH-01 | compliance.md post-R3 | CHK336; accessibility.md CHK292 |
| FR-RAG-FRESH-02 | compliance.md post-R3 | CHK336–CHK339 |
| FR-RAG-COORD-01 | multi-agent-coordination.md | CHK230–CHK241, CHK246, CHK248–CHK249 |
| FR-RAG-COORD-02 | multi-agent-coordination.md | CHK242–CHK247 |
| FR-RAG-TEST-01 | test-coverage-windows.md | CHK250–CHK253, CHK268 |
| FR-RAG-TEST-02 | test-coverage-windows.md | CHK254–CHK258, CHK268–CHK269 |
| FR-RAG-TEST-03 | test-coverage-windows.md | CHK259–CHK263, CHK268 |
| FR-RAG-TEST-04 | test-coverage-windows.md | CHK264–CHK269 |
| FR-RAG-OBS-01 | observability.md | CHK270–CHK278 |
| FR-RAG-OBS-02 | observability.md | CHK280–CHK282 |
| FR-RAG-OBS-03 | observability.md | CHK279, CHK283–CHK284 |
| FR-RAG-UI-01 | accessibility.md | CHK285–CHK296 |
| FR-RAG-AG-02 (extended) | audit-and-approval-workflow.md | CHK207–CHK229; also migration.md CHK313–CHK317 |
| FR-RAG-AG-04 (extended) | requirements.md post-R3 + migration.md post-R3 + multi-agent-coordination.md (CHK238) | CHK238, CHK301, CHK304, CHK310–CHK311 |
| FR-RAG-CV-01 (extended) | compliance.md post-R3 | CHK320–CHK325 |
| FR-RAG-IDX-04 (extended for blue-green schema migration) | compliance.md post-R3 + migration.md post-R3 | CHK326, CHK316 |
| FR-RAG-LS-02 (extended for FC offline boundaries) | audit-and-approval-workflow.md | CHK220–CHK223 |

## Per-SC Coverage Map (new SCs only)

| SC | Primary Checklist | Item |
|---|---|---|
| SC-013 (agency disambiguation ≥95%) | test-coverage-windows.md | CHK261; also requirements.md CHK299 |
| SC-014 (cultural authority sign-offs) | cultural-authority-protocols.md | CHK185 |
| SC-015 (Commonwealth precedence ≥95%) | requirements.md post-R3 | CHK299 |
| SC-016 (OPA carve-out contract test) | compliance.md post-R3 | CHK323, CHK325 |
| SC-017 (override/approval audit 100%) | audit-and-approval-workflow.md | CHK213, CHK217 |
| SC-018 (ISM-2024-mapping.md exists) | federal-compliance-mapping.md | CHK193 |
| SC-019 (alias-flip consistency + 5-min rollback) | compliance.md post-R3 | CHK332 |

## Per-Assumption Coverage Map (new Assumptions only)

| Assumption | Primary Checklist | Item |
|---|---|---|
| A9 (HUMAN-IN-LOOP authorities consolidated) | federal-compliance-mapping.md (CHK189, CHK194, CHK202, CHK206) + cultural-authority-protocols.md (CHK167, CHK184) | (multiple) |
| A10 (schema migration field-class-aware) | audit-and-approval-workflow.md (CHK224–CHK226) + migration.md post-R3 (CHK316) | (multiple) |
| A11 (ADR lifecycle: markers → stubs → body) | requirements.md post-R3 (CHK305–CHK306) | CHK305–CHK306 |
| A12 (feature-flag taxonomy: Locked-on / Reversible / Manual) | audit-and-approval-workflow.md (CHK227) + multi-agent-coordination.md (CHK248–CHK249) + cultural-authority-protocols.md (CHK186) + compliance.md post-R3 (CHK331, CHK339) + migration.md post-R3 (CHK319) | (multiple) |

## Plan-phase ADR Stub Deliverables (per Assumption A11)

The 8 new amend-loop `[NEEDS ADR]` markers expect plan-phase stubs at `docs/decisions/036-foundry-rag-grounding/`:

- `12-cultural-authority-gating.md` — covered by `cultural-authority-protocols.md`
- `13-authority-precedence-ranking.md` — covered by `requirements.md` post-R3 + `multi-agent-coordination.md` (CHK238)
- `14-approval-workflow-audit.md` — covered by `audit-and-approval-workflow.md`
- `15-federal-compliance-mapping.md` — covered by `federal-compliance-mapping.md`
- `16-blue-green-atomicity.md` — covered by `compliance.md` post-R3
- `17-corpus-freshness.md` — covered by `compliance.md` post-R3
- `18-multi-agent-conflict.md` — covered by `multi-agent-coordination.md`
- `19-test-coverage-windows.md` — covered by `test-coverage-windows.md`

## Reading Order for Reviewers

1. **Compliance reviewer** (Constitution + federal): `compliance.md` → `cultural-authority-protocols.md` → `federal-compliance-mapping.md`
2. **Engineering reviewer** (migration + tests + observability): `migration.md` → `test-coverage-windows.md` → `observability.md` → `audit-and-approval-workflow.md`
3. **Operational AIIMS reviewer**: `multi-agent-coordination.md` → `audit-and-approval-workflow.md` (FC offline boundaries section)
4. **Accessibility reviewer**: `accessibility.md` → `requirements.md` post-R3 (US10/US9 quality items)
5. **Spec reviewer** (cross-cutting): `requirements.md` (full file including post-R3 extension)

## Notes

- **Each `/speckit.checklist` invocation creates files; this refresh added 7 new files plus appended sections to 3 existing files. Original CHK001–CHK165 items remain at their original numbers.**
- **HUMAN-IN-LOOP items** are explicitly tagged with their authority (NEMA, AFAC, AIATSIS, AGD, OAIC, ASD, AFP, ARC accessibility advisor, etc.) so `tasks.md` can route them to the correct external sign-off chain.
- **Items not yet ticked** (`- [ ]`) are the post-R3 surface; pre-R3 items (`- [X]`) were resolved at Phase E close (T149).
- **Post-R3 Phase resolution**: When the `/speckit.plan` phase lands the 8 new ADR stubs and the schema migrations, the `[ ]` items can be ticked individually as they pass review — the same convention as Phase E.
