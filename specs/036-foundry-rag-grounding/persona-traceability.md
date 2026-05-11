# Persona traceability — Spec 036 (Foundry RAG grounding)

This report cross-references the **Top-N priorities** from each of the 9
persona memos (`personas-input/`) to the task IDs that deliver them in
`tasks.md`. T137 / FR-RAG-AG-04. Owner: Lead Architect (J.B.).

The persona-input source documents (read-only) live at
`personas-input/{operational, sectors-commonwealth, sectors-crosssector,
sectors-eastern, sectors-southern-western, sectors-territories,
technical-architecture, technical-delivery, technical-quality}.md`. Each row
below identifies a single concern raised by a persona, the FR clause(s) it
maps to, and the task IDs that close the loop.

Coverage score: 9/9 personas linked to ≥ 1 deliverable per Top-N item
(verified manually 2026-05-08).

## 1. Operational personas (Field-Coordinator, Planning Officer, Incident Controller)

| # | Concern | FR clause | Tasks |
|---|---------|-----------|-------|
| 1 | "Citations must be doctrine-grounded — no hallucination on life-safety paths" | FR-RAG-AG-01..03, FR-RAG-CV-03 | T058–T064, T070–T075, T084 |
| 2 | "Field Coordinator needs offline cache when satellite link drops" | FR-RAG-LS-02 | T046–T047, T112, T129–T131, T136 |
| 3 | "Planning collection step must stay deterministic and fast" | FR-RAG-NS-04 | T120 (ADR-04, code-marker-optional) |
| 4 | "Operator must see when AI is operating in degraded mode" | FR-RAG-UX-04 | T085, T116, T133 |
| 5 | "Audit must reproduce a recommendation byte-for-byte for retro" | FR-RAG-FM-04, FR-RAG-NS-09 | T067–T068, T117, T125 |

## 2. Sector — Commonwealth (NEMA, AGD, ABC EMA, ADF)

| # | Concern | FR clause | Tasks |
|---|---------|-----------|-------|
| 1 | "Cross-jurisdiction handoff must surface AIDR + national doctrine" | FR-RAG-AG-04 / US7 | T065, T134, fixture `multi_jurisdiction.jsonl` rows `national-001..005`, `aidr-001..005` |
| 2 | "Classified ADF/AFP traffic NEVER hits the public RAG" | FR-RAG-NS-07 | T123 (ADR-07), T127 (model_gateway marker), T128 (lint) |
| 3 | "ABC EMA broadcast pre-empt has its own audit trail" | FR-RAG-OB-04 | T030, T132 |
| 4 | "AGD CIC dependency-cascade is a non-RAG signal flow" | FR-RAG-NS-01 | T117 (ADR-01, code-marker-optional), T128 (lint) |
| 5 | "NEMA must see per-tenant retrieval quotas" | FR-RAG-AG-01 | T030, T093, T135 (`foundry-agent-quotas.yaml`) |

## 3. Sector — Cross-sector (Health, Telco, Energy)

| # | Concern | FR clause | Tasks |
|---|---------|-----------|-------|
| 1 | "Critical-infrastructure signals must NOT be re-grounded by an LLM" | FR-RAG-NS-01 | T117 (ADR-01), T127 |
| 2 | "Cascade events need multi-hazard correlation thresholds" | FR-RAG-AG-04 | T134, fixture `aidr-005` |
| 3 | "Energy-network telemetry is read-only; observer-auditor only" | FR-RAG-NS-09 | T125 (ADR-09), T127 (audit_export marker) |
| 4 | "Health/CALD inclusion checklist for warnings" | FR-RAG-CV-03 | T103 (Communication agent grounding), T134 fixture `qld-003`, `vic-003`, `wa-003` |

## 4. Sector — Eastern (NSW, VIC, ACT)

| # | Concern | FR clause | Tasks |
|---|---------|-----------|-------|
| 1 | "NSW–VIC border NSP/CFA-VIC vs RFS doctrine must NOT silently conflate" | FR-RAG-AG-04 / US7 | T065, T134 fixture rows `nsw-001..005`, `vic-001..005`, `act-001..005` |
| 2 | "RFS Section-44 declaration triggers MUST be cited" | FR-RAG-CV-03 | T134 `nsw-001`, T084 |
| 3 | "Eastern-state operators expect AEST timestamps in degraded-mode banner" | FR-RAG-UX-04 | T133 (`degraded-mode-badge.tsx` `formatAbsolute`) |
| 4 | "Storm-surge / dam-spill coordination must surface SES handbook" | FR-RAG-CV-03 | T134 fixture `nsw-002`, `vic-002` |

## 5. Sector — Southern-Western (SA, WA, TAS, NT remoteness)

| # | Concern | FR clause | Tasks |
|---|---------|-----------|-------|
| 1 | "Remote ATSI community engagement requires the Aboriginal Interpreter Service" | FR-RAG-CV-03, FR-RAG-UX-04 | T103, T133, T134 fixture `wa-003`, `nt-002`, `nt-003` |
| 2 | "Heatwave-doctrine for APY Lands must reach SA Health" | FR-RAG-AG-04 | T134 fixture `sa-002` |
| 3 | "DFES single-agency edge — must NOT pull NSW RFS chunks" | FR-RAG-AG-04 / US7 | T065 `test_dfes_wa_does_not_pull_nsw_rfs`, T134 fixture `wa-001..005` |
| 4 | "Last-resort refuge protocols (CFS, TFS) must be retrievable" | FR-RAG-CV-03 | T134 fixture `sa-001`, `tas-001` |

## 6. Sector — Territories (NT, ACT — remoteness + monsoonal)

| # | Concern | FR clause | Tasks |
|---|---------|-----------|-------|
| 1 | "Cyclone shelter activation triggers (NT Code Blue)" | FR-RAG-CV-03 | T134 fixture `nt-001`, `nt-005` |
| 2 | "Tiwi Islands monsoon-flooding cultural-aware risk" | FR-RAG-CV-03 | T134 fixture `nt-002` |
| 3 | "Top End remote-community resupply ADF MOU coordination" | FR-RAG-AG-04 | T134 fixture `nt-004` |
| 4 | "ACT–NSW handoff doctrine (Queanbeyan smoke event)" | FR-RAG-AG-04 / US7 | T134 fixture `act-002` |

## 7. Technical — Architecture (J.B., systems-architect)

| # | Concern | FR clause | Tasks |
|---|---------|-----------|-------|
| 1 | "Per-agent grounding wiring must be feature-flagged + reversible" | FR-RAG-FM-04, FR-RAG-FM-06 | T058–T064, T093 |
| 2 | "Test seam — never hit live Foundry / AI Search in unit tests" | FR-RAG-FM-07 | T034 (FakeRetrievalService), T110–T117 |
| 3 | "Carve-outs MUST be ADR-backed and lint-enforced" | FR-RAG-NS-08 | T110, T118–T126, T127–T128 |
| 4 | "Bicep blue-green for AI Search (R-04 corpus replay)" | FR-RAG-IDX-05 | T028, T030 |
| 5 | "Observability: KQL + workbook for grounded vs opt-out ratios" | FR-RAG-OB-04 | T030, T132 |

## 8. Technical — Delivery (R.D., delivery lead)

| # | Concern | FR clause | Tasks |
|---|---------|-----------|-------|
| 1 | "CI gates must catch RAG-OPTOUT drift before merge" | FR-RAG-NS-08 | T128 (`rag-optout-binding-lint` step) |
| 2 | "Per-agent canary harness with rollback drill" | FR-RAG-FM-06 | T091, T093 |
| 3 | "Quarterly chaos drill includes offline-cache exhaustion" | FR-RAG-LS-02 | T132, T138–T140 game-day runbook |
| 4 | "Eval-runner runs golden set on every cutover" | FR-RAG-FM-06 | T134 fixture, T093 per-agent canary gate |

## 9. Technical — Quality (V.Q., quality lead)

| # | Concern | FR clause | Tasks |
|---|---------|-----------|-------|
| 1 | "WCAG 2.2 AA on every operator-visible component" | FR-RAG-UX-04 | T085, T115, T116, T133 |
| 2 | "Citation precision SC-007 ≥ 0.85 across all 50 golden queries" | FR-RAG-CV-03 | T134 fixture (`min_citation_precision` per row) |
| 3 | "R10 — confidence_downgrade_threshold per agent revisitable" | FR-RAG-AG-04 | T135 (`foundry-agent-quotas.yaml`) |
| 4 | "60-second audit-spool drain SLA on offline → online sync (SC-009)" | FR-RAG-LS-02 | T112 (integration test), T131 (`AuditSpool.drain`) |
| 5 | "Embedding-model parity across the golden set" | FR-RAG-IDX-05 | T134 (`test_embedding_model_parity`) |

## Verification

Re-run this report by mapping every Top-N entry of every persona memo to a
deliverable. Drift is caught by CI (T128 lint catches missing markers; T134
fixture test catches missing jurisdictions; T030/T132 alerts catch missing
observability hooks). The compliance checklist
(`specs/036-foundry-rag-grounding/checklists/compliance.md`) tracks per-FR
outcome verification at runtime.
