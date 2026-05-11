# Accessibility Checklist: Microsoft Foundry-Based RAG Grounding

**Purpose**: Validate that the FR-RAG-UI-01 WCAG 2.2 AA requirements (citation card aria-label, keyboard navigation, screen-reader announcements) are specified to a level an accessibility advisor (ARC + Auslan + Easy-Read consultants) can verify before planning, including how accessibility extends to the new amend-loop UI surfaces (precedence badges, conflict indicators, corpus-freshness states).
**Created**: 2026-05-09 (post R3 amend loop Sessions 3 + 4 + 5)
**Feature**: [spec.md](../spec.md)
**Cluster**: A12 (Accessibility) + cross-refs FR-RAG-AG-04 (precedence badges), FR-RAG-COORD-02 (conflict-resolution UI), FR-RAG-FRESH-01 (corpus-freshness UI states), FR-RAG-AG-06 (ATSI/CALD/Auslan/Easy-Read/TIS-National)
**Companion checklists**:
- [requirements.md](./requirements.md) — Spec quality fundamentals (US8 ATSI/CALD/accessibility-aware retrieval cross-ref)
- [multi-agent-coordination.md](./multi-agent-coordination.md) — Conflict-resolution UI accessibility (FR-RAG-COORD-02 cross-ref)
- [audit-and-approval-workflow.md](./audit-and-approval-workflow.md) — Override-rationale UI accessibility (FR-RAG-AG-02 cross-ref)

> **Scope of this file**: The accessibility surface added by R3 Cluster A12: **WCAG 2.2 AA scope** (SHOULD vs MUST; not blocking Step 9), **citation card** (`aria-label` template), **recommendation card** (screen-reader announcement template), **keyboard navigation** (tab order, Enter to open source), **interactions with new amend-loop UI** (precedence badges, conflict indicators, corpus-freshness states), **HUMAN-IN-LOOP sign-off chain** (ARC accessibility advisor + Auslan / Easy-Read consultants).

> **Item numbering**: Continues from `observability.md` (CHK285+).

## WCAG 2.2 AA Scope (SHOULD vs MUST)

> **Authority**: FR-RAG-UI-01 (R3 Cluster A12); Constitution V (Warning and Public Information); ARC + PIO persona memos.

- [ ] CHK285 Is the **SHOULD** vs **MUST** classification of FR-RAG-UI-01 ("not MUST; not blocking Step 9") consistent with how the SC set treats it (no SC binds it as MUST)? [Consistency, Spec §FR-RAG-UI-01 vs §SC]
- [ ] CHK286 Is the WCAG 2.2 AA scope bounded — does it apply to citation cards + recommendation cards only, or to the whole UI (and is the boundary measurable)? [Clarity, Spec §FR-RAG-UI-01]

## Citation Card Accessibility Requirements

> **Authority**: FR-RAG-UI-01 + FR-RAG-AG-03 (citation token shape).

- [ ] CHK287 Is the `aria-label` content template (`Cite: <jurisdiction>/<topic>/handbook.md#page-N`) consistent with the citation token shape in FR-RAG-AG-03 (so screen readers announce the same string the audit log records)? [Consistency, Spec §FR-RAG-UI-01 vs §FR-RAG-AG-03]
- [ ] CHK288 Are accessibility requirements specified for citations whose page anchor is missing (e.g., `mode: metadata-only` entries with no page; front-matter chunks with no page anchor) — does the `aria-label` degrade gracefully? [Edge Case, Gap, Spec §FR-RAG-UI-01 vs §FR-RAG-IDX-02]

## Recommendation Card Accessibility Requirements

> **Authority**: FR-RAG-UI-01 + FR-RAG-AG-05 (hallucinated-citation suppression) + FR-RAG-SIM-03 (`citations: []` no-corpus-match path).

- [ ] CHK289 Is the screen-reader announcement template (`Grounded recommendation with N citations`) quantified — what value does **N** take when `citations: []` (per FR-RAG-SIM-03 simulation no-match reply)? [Edge Case, Spec §FR-RAG-UI-01 vs §FR-RAG-SIM-03]
- [ ] CHK290 Are accessibility requirements specified for **hallucinated-citation suppression** (FR-RAG-AG-05) — does the screen-reader announce the suppression event, or stay silent (and which choice better serves the operator)? [Gap, Spec §FR-RAG-UI-01 vs §FR-RAG-AG-05]

## Screen-Reader Announcements for Amend-Loop UI Surfaces

> **Authority**: FR-RAG-UI-01 cross-refs FR-RAG-AG-04 (precedence badges), FR-RAG-COORD-01 (conflict indicators), FR-RAG-FRESH-01 (corpus-freshness states).

- [ ] CHK291 Are the `precedence_tiebreak_applied[]` trace and **conflict_detected indicators** (FR-RAG-AG-04, FR-RAG-COORD-01) accessible via screen-reader, OR is each explicitly out-of-scope for FR-RAG-UI-01 (with rationale)? [Coverage, Gap, Spec §FR-RAG-UI-01 vs §FR-RAG-AG-04 / §FR-RAG-COORD-01]
- [ ] CHK292 Are the corpus-freshness UI states (`Corpus last updated` timestamp; yellow >7d; red >14d per FR-RAG-FRESH-01) accompanied by screen-reader-accessible variants (text equivalents for colour-only signals)? [Coverage, Gap, Spec §FR-RAG-UI-01 vs §FR-RAG-FRESH-01]

## Keyboard Navigation

> **Authority**: FR-RAG-UI-01 + new amend-loop UI surfaces (override-rationale capture, conflict-resolution dialog).

- [ ] CHK293 Is keyboard-navigation scope (tab order, Enter to open source) defined for both citation cards AND for the conflict-resolution + override-rationale UIs introduced by FR-RAG-COORD-02 + FR-RAG-AG-02? [Coverage, Gap, Spec §FR-RAG-UI-01 vs §FR-RAG-COORD-02 / §FR-RAG-AG-02]
- [ ] CHK294 Are focus-trap / focus-restore requirements specified for modal interactions (e.g., conflict-resolution dialog, override-rationale capture)? [Edge Case, Gap, Spec §FR-RAG-UI-01]

## Acceptance Criteria & Step-9 Gating

> **Authority**: FR-RAG-UI-01 SHOULD classification; Assumption A9 HUMAN-IN-LOOP authorities.

- [ ] CHK295 Is "not blocking Step 9" interpreted consistently — i.e., is there a deferred-acceptance criterion (e.g., post-GA WCAG audit; quarterly accessibility review) tracked in `tasks.md` or a follow-on spec? [Coverage, Gap, Spec §FR-RAG-UI-01]
- [ ] CHK296 [HUMAN-IN-LOOP — ARC accessibility advisor + Auslan / Easy-Read consultants] Is the WCAG 2.2 AA validation authority chain identified (which advisor / consultant signs off the final UI; how that ties to FR-RAG-AG-06 ATSI/CALD/Auslan/Easy-Read/TIS-National retrieval surfacing)? [Clarity, Spec §FR-RAG-UI-01 vs §FR-RAG-AG-06 / §A9]

## Notes

- **Item count (this file)**: 12 items across 6 sections (CHK285–CHK296).
- **Cross-references**: Items in this file frequently cite FR-RAG-UI-01, FR-RAG-AG-03 (citation token shape), FR-RAG-AG-04 (precedence badges), FR-RAG-AG-05 (hallucinated-citation suppression), FR-RAG-AG-06 (ATSI/CALD/Auslan/Easy-Read), FR-RAG-COORD-01/02 (conflict indicators + dialog), FR-RAG-FRESH-01 (corpus-freshness UI states), FR-RAG-SIM-03 (`citations: []`), FR-RAG-IDX-02 (`mode: metadata-only`), and Constitution Principle V.
- **Why this file is separate**: Accessibility is the **only** SHOULD-class FR family in the amend loop; it benefits from a focused checklist that an accessibility advisor can clear independently of MUST-class compliance / coordination / cultural-authority reviews. The cross-references to amend-loop UI surfaces (precedence badges, conflict indicators, corpus-freshness states) are specifically called out so accessibility doesn't get retrofitted post-GA.
- **HUMAN-IN-LOOP authority**: ARC accessibility advisor + Auslan / Easy-Read / TIS-National consultants per FR-RAG-AG-06 + Assumption A9.
