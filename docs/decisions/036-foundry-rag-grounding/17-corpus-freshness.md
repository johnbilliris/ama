# ADR 17 — Corpus Freshness (Nightly Schedule + 14-Day Staleness Alert)

**FR**: FR-RAG-IDX-05a (scheduled nightly refresh), FR-RAG-FRESH-01 (UI freshness indicator), FR-RAG-FRESH-02 (staleness alert)
**Cluster**: A8 — Corpus Staleness Detection & Surfacing
**Persona memo citation**: `personas-input/r3-technical-quality.md` §F-SRE-01 "Embedding model drift detection automation missing"; `personas-input/r3-operational.md` §"Operators need to see corpus age"
**Approver**: AMA Spec-036 Architecture Review + SRE Engineer
**Date**: 2026-05-08
**Status**: Stub — body authored in `/speckit.implement` (Phase F-A8 task)

## Stub placeholder

> Detailed rationale to land in implement-phase task `T-A8-ADR17` (planned). This stub exists per Assumption **A11** so `[NEEDS ADR]` markers on FR-RAG-IDX-05a, FR-RAG-FRESH-01, and FR-RAG-FRESH-02 resolve to a real path at plan-review time.

## Skeleton (to be filled in `/speckit.implement`)

- **Context** — F-SRE-01 finding: no automated detection of corpus staleness or embedding-model drift; silent degradation discovered only via user escalation. Operators have no UI signal of corpus age; `corpus_build_sha` is opaque hex.
- **Decision — Nightly drift-detection schedule (FR-RAG-IDX-05a)** — Ingest pipeline runs on a schedule of **1 AM AU Eastern** (`cron: "0 14 * * *"` UTC → 0100 AEST / 0000 AEDT). On run: pipeline checks every `source.json.sha256` for drift; if drift detected (any mismatch or new entry added), pipeline re-runs ingest and flips alias if parity gate passes (per ADR-16); if no drift, pipeline logs `no_drift_detected` and exits cheaply.
- **Decision — UI freshness indicator (FR-RAG-FRESH-01)** — Recommendation cards and simulation chat display "Corpus last updated: <timestamp>" derived from `corpus_build_sha` manifest `generated_at`. UI highlights: yellow warning if corpus age >7 days; red alert if >14 days. Implemented in existing `<CitationCard />` and the new `<DegradedModeBadge />` (Phase D4) — no new UI surfaces.
- **Decision — Staleness alert scope (FR-RAG-FRESH-02 / Pass 1 Q-P1-05)** — **Per global corpus index**, NOT per-jurisdiction or per-topic partition. One alert per `corpus_build_sha` age threshold breach. Reasoning: FR-RAG-IDX-08 mandates a single Azure AI Search index; `corpus_build_sha` is monotonic across the whole `scripts/disaster_corpus/manifest.py` build pipeline; per-partition thresholds are out of scope per Assumption A1 + OOS-3.
- **Decision — Alert trigger** — Emit `corpus_stale` alert to on-call + Service Bus when `corpus_build_sha.generated_at` age exceeds 14 days **AND** no ingest job has run in the last 48 hours. The 48-hour grace prevents transient alert noise during in-flight rebuilds.
- **Decision — Disable path** — `feature.corpus_freshness_alert.enabled` (Reversible class per A12); when disabled, alert is suppressed but underlying staleness state still recorded in audit log; flip emits `corpus_freshness_alert_disabled` audit event; reversible mid-incident per spec 029 FR-008.
- **Consequences** — Operators have a 7-day yellow + 14-day red signal in UI; SRE has automated nightly drift detection; FR-SRE-01 finding closed. No per-jurisdiction telemetry complexity.

## Cross-references

- Cluster A8 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-05, Pass 2 Q-P2-08 in `specs/036-foundry-rag-grounding/spec.md` Sessions 4 + 5.
- Schema `specs/036-foundry-rag-grounding/contracts/staleness_alert.schema.json`.
- Existing `infra/modules/ai-search-blue-green.bicep` parity gate.
- Plan phase `F-A8` in `specs/036-foundry-rag-grounding/plan.md`.
