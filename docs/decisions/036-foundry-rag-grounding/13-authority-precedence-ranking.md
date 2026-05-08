# ADR 13 — Authority Precedence Ranking (Commonwealth-vs-State-Territory)

**FR**: FR-RAG-AG-04, FR-RAG-AC-01
**Cluster**: A1 (agency disambiguation) + A3 (Commonwealth precedence)
**Persona memo citation**: `personas-input/r3-sectors-territories.md` §"ACT national-institution precedence (Parliament House, Defence estates)"; `personas-input/r3-sectors-eastern.md` §"Multi-agency disambiguation NSW RFS vs FRNSW"; `personas-input/r3-sectors-commonwealth.md` §"COMDISPLAN activation"
**Approver**: AMA Spec-036 Architecture Review + NEMA liaison
**Date**: 2026-05-08
**Status**: Accepted — body authored 2026-05-15 (Phase F-A1+F-A3)

## Context

Australian disaster doctrine spans overlapping authority surfaces:

- **Multi-agency jurisdictions** — NSW operates two fire services (NSW Rural Fire Service for rural; Fire & Rescue NSW for urban); WA combines all hazards under DFES; ACT has urban-only ACT Fire & Rescue inside the city plus Commonwealth fire authorities at Defence estates and Parliament House. Without agency-level disambiguation, a "bushfire evacuation" retrieval against NSW returns contradictory guidance (RFS calls retreat-to-defend; FRNSW calls evacuate-immediately for urban-fringe).
- **Authority precedence** — When state/territory doctrine conflicts with Commonwealth doctrine (e.g. national institutions in ACT, COMDISPLAN-activated incidents), the operator must surface Commonwealth-first; otherwise the agent silently downranks federal authority and operators on Defence estates miss handler-required guidance.
- **Audit determinism** — Spec 014 SC-011 requires ≥ 95 % byte-identical retrieval replay over a 7-day window; tie-breaks introduced for ranking must be deterministic and recorded so replays survive embedding-model rotation and chunk re-issue.

Persona memos cited above (R3 territories, R3 eastern, R3 commonwealth) escalated this in the amend loop. Pass 1 Q-P1-02 settled the tie-break order over four candidates (recency-only, alphabetical-only, embedding-model-only, composite).

## Decision

1. **Chunk-metadata fields** (additive to `chunk-metadata.schema.json`, T173):
   - `agency`: enum `NSW-RFS | FRNSW | DFES-WA | QFES | SAMFS | TAS-FS | NTPFES | ACT-FR | NEMA | DEFENCE | …` (extensible).
   - `agency_role`: enum `urban-fire | rural-fire | ses | combined | police | health | other`.
   - `authority_level`: enum `state-territory | commonwealth | national-institution`.
   - `precedence_rank`: int 1–3 (1 = highest); ACT-Commonwealth coexistence: Commonwealth=1, ACT=2 for national institutions, ACT=1 for the rest of the Territory.
2. **Tie-break order** (Pass 1 Q-P1-02), applied when two chunks share `precedence_rank`:
   1. `corpus_build_sha.generated_at` recency (newer wins);
   2. `licence_mode` (`full-text` > `metadata-only`);
   3. `embedding_model_id` lexicographic (newer wins on equal recency);
   4. `chunk_id` lexicographic (final deterministic backstop).
   The trace `precedence_tiebreak_applied[]` is appended to the audit record per call so SC-011 byte-identical replay still holds.
3. **COMDISPLAN interlock** — when `national_emergency_active=true` is declared (FR-RAG-COMP-04, T207), retrieval boosts Commonwealth COMDISPLAN doctrine for the declared hazard type + impacted jurisdictions to `precedence_rank=1` and demotes state-territory chunks to `rank=2`. This is *re-ranking*, not a carve-out — chunks still retrieve, only the order changes, so audit and chunk-replay remain stable.
4. **Feature flag** — `feature.authority_precedence_ranking.enabled` (Reversible class per A12 flag taxonomy); when disabled, ranking falls back to corpus-build-sha recency only and the UI hides precedence badges. The chunk-metadata fields themselves are Locked-on so disablement does not corrupt downstream replays.
5. **Audit emission** — every retrieval response carries the resolved `precedence_rank`, the COMDISPLAN flag, and the `precedence_tiebreak_applied[]` trace as new audit-record fields (covered by F-A5 / T156–T165).

## Rationale

- **Why two fields per axis (`agency` + `agency_role`, `authority_level` + `precedence_rank`)?** Agency identity is operational ("which doctrine voice am I quoting?"); role lets the UI surface the right badge ("Rural Fire" vs "Urban Fire"); authority level is the legal characterisation; rank is the resolved comparator. Collapsing any of these conflates concerns and makes future agency additions (e.g. an Indigenous Ranger Authority) require schema migrations.
- **Why this tie-break order?** Recency first matches the operator mental model ("the latest doctrine wins"); licence mode second prevents metadata-only stubs from outranking full-text content of equal recency; embedding-model lexicographic ordering breaks ties between a Saturday-night ingest of model A and a Sunday-morning ingest of model B that share `generated_at`; `chunk_id` is the deterministic backstop that guarantees a total order.
- **Why a Reversible flag, not Locked-on?** Operators have asked for the ability to silence COMDISPLAN re-ranking during exercises that simulate degraded federal coordination. Constitution VI is silent on Commonwealth precedence; Pass 2 Q-P2-08 explicitly classed this as Reversible.
- **Why store `precedence_tiebreak_applied[]`?** Without the trace, two replays of the same query against an identical corpus could diverge if the tie-break sees floats with the same printed precision but different IEEE-754 bits. Recording the trace makes replay auditable in the strict spec-014 sense.

## Consequences

**Positive**
- Operational personas get unambiguous agency-disambiguated retrieval; SC-013 (≥ 95 % agency-disambiguation accuracy) is achievable.
- ACT national-institution operators get Commonwealth-first answers; SC-015 (≥ 95 % Commonwealth-first for national institutions in ACT) is achievable.
- COMDISPLAN re-ranking is a single config flip plus a flag, not a retrieval-pipeline rewrite.

**Negative / mitigations**
- Five new chunk-metadata fields → ingest pipeline must populate them; mitigated by the F-A1 ingest-side ranker (T173) and a shipped migration tool (T174) that backfills from the existing `jurisdiction` field plus a hand-curated CSV.
- Audit-record growth ~ 200 bytes/call. Acceptable: at 5 RPS sustained that is ~ 250 MB/year, well under the Cosmos retention budget.
- Operator confusion if a state/territory chunk is intentionally demoted under COMDISPLAN. Mitigated by the recommendation-card showing a "Commonwealth precedence (COMDISPLAN active)" badge whenever rank=1 was achieved via the interlock.

## Cross-references

- Clusters A1 + A3 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-02 in spec.md Session 4.
- Schema additions in `contracts/chunk-metadata.schema.json`.
- Tasks T173–T192; audit emission in F-A5 (T156–T165).
- Plan phases F-A1 + F-A3 in `specs/036-foundry-rag-grounding/plan.md`.
- ADR 16 (blue-green atomicity) covers the rebuild flip when these fields are added.
