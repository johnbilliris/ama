# ADR 13 — Authority Precedence Ranking (Commonwealth-vs-State-Territory)

**FR**: FR-RAG-AG-04, FR-RAG-AC-01
**Cluster**: A1 (agency disambiguation) + A3 (Commonwealth precedence)
**Persona memo citation**: `personas-input/r3-sectors-territories.md` §"ACT national-institution precedence (Parliament House, Defence estates)"; `personas-input/r3-sectors-eastern.md` §"Multi-agency disambiguation NSW RFS vs FRNSW"; `personas-input/r3-sectors-commonwealth.md` §"COMDISPLAN activation"
**Approver**: AMA Spec-036 Architecture Review + NEMA liaison
**Date**: 2026-05-08
**Status**: Stub — body authored in `/speckit.implement` (Phase F-A1/F-A3 task)

## Stub placeholder

> Detailed rationale to land in implement-phase task `T-A3-ADR13` (planned). This stub exists per Assumption **A11** so the `[NEEDS ADR]` markers in FR-RAG-AG-04 and FR-RAG-AC-01 resolve at plan-review time.

## Skeleton (to be filled in `/speckit.implement`)

- **Context** — Multi-agency jurisdictions are operational reality (NSW: 2 fire agencies; ACT: dual state-territory/Commonwealth authority for national institutions; WA: DFES combined). Without agency-level disambiguation + authority-level ranking, retrieval surfaces contradictory guidance.
- **Decision** — Two new chunk fields: `agency` (e.g. NSW-RFS, FRNSW, DFES-WA, SAMFS) and `agency_role` (urban-fire | rural-fire | ses | combined). Two further chunk fields: `authority_level` (state-territory | commonwealth | national-institution) and `precedence_rank` (int 1=highest, 3=lowest); ACT-Commonwealth coexistence: Commonwealth=1, ACT=2 for national institutions.
- **Tie-break order (Pass 1 Q-P1-02)** — Deterministic order applied when chunks share `precedence_rank`: (1) `corpus_build_sha.generated_at` recency (newer wins), (2) `licence_mode` (`full-text` > `metadata-only`), (3) `embedding_model_id` lexicographic (newer wins on equal recency), (4) `chunk_id` lexicographic (final deterministic backstop). Trace recorded as `precedence_tiebreak_applied[]` in audit so SC-011 ≥95% byte-identical replay holds.
- **COMDISPLAN activation interlock** — When `national_emergency_active` (FR-RAG-COMP-04) is set, retrieval ranking prioritises Commonwealth COMDISPLAN doctrine over state/territory guidance for the declared hazard type + impacted jurisdictions; this is a *retrieval ranking* change, not a carve-out.
- **Disable path** — `feature.authority_precedence_ranking.enabled` (Reversible class per A12); when disabled, ranking falls back to `corpus_build_sha` recency only and recommendation-card UI hides precedence badges; chunk metadata remains populated (Locked-on for the fields themselves) — only the *ranking step* is flag-controlled. Reversible mid-incident per spec 029 FR-008 5-minute SLO.
- **Consequences** — Preserves deterministic audit replay (SC-011); enables SC-013 ≥95% on agency-disambiguation subset and SC-015 ≥95% Commonwealth-first-for-national-institution-in-ACT.

## Cross-references

- Clusters A1 + A3 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-02 in `specs/036-foundry-rag-grounding/spec.md` Session 4.
- Schema additions in `specs/036-foundry-rag-grounding/contracts/chunk-metadata.schema.json`.
- Plan phases `F-A1` + `F-A3` in `specs/036-foundry-rag-grounding/plan.md`.
