# ADR 17 — Corpus Freshness (Nightly Schedule + 14-Day Staleness Alert)

**FR**: FR-RAG-IDX-05a (scheduled nightly refresh), FR-RAG-FRESH-01 (UI freshness indicator), FR-RAG-FRESH-02 (staleness alert)
**Cluster**: A8 — Corpus Staleness Detection & Surfacing
**Persona memo citation**: `personas-input/r3-technical-quality.md` §F-SRE-01 "Embedding model drift detection automation missing"; `personas-input/r3-operational.md` §"Operators need to see corpus age"
**Approver**: AMA Spec-036 Architecture Review + SRE Engineer
**Date**: 2026-05-08
**Status**: Accepted — body authored 2026-05-15 (Phase F-A8)

## Context

The R3 amend loop surfaced a quality finding (F-SRE-01) that the Phase D ingest pipeline had no automated detection of corpus staleness or embedding-model drift; silent degradation could only be detected via user escalation. The R3 operational memo separately noted that operators wanted a visible "how fresh is this answer?" signal — `corpus_build_sha` was opaque hex and operators wanted a date.

Pass 1 Q-P1-05 settled the alert scope as per-global-index (not per-jurisdiction, not per-topic) consistent with FR-RAG-IDX-08's single-index decision and OOS-3.

## Decision

1. **Nightly drift-detection schedule (FR-RAG-IDX-05a)** — the ingest pipeline runs on a fixed cron of **0100 AEST / 0000 AEDT**, which evaluates as `0 14 * * *` UTC. On each run:
   - The pipeline checks every `source.json.sha256` for drift.
   - On drift (mismatch or new entry), it re-runs ingest and flips the alias only if the parity gate passes (per ADR 16).
   - On no drift, it logs `no_drift_detected` and exits cheaply (no AI Search write, no embedding spend).
2. **UI freshness indicator (FR-RAG-FRESH-01)** — recommendation cards and simulation chat display "Corpus last updated: \<timestamp\>" derived from the manifest `generated_at`. The UI highlights:
   - **green** for age ≤ 7 days,
   - **yellow** for 7 < age ≤ 14 days,
   - **red** for > 14 days.
   This is rendered by the new `<CorpusFreshnessIndicator />` component (T214) and is consumed by `<RecommendationCard />` and `<DegradedModeBadge />` — no new UI surfaces.
3. **Staleness alert scope (FR-RAG-FRESH-02; Pass 1 Q-P1-05)** — **per global corpus index**, NOT per-jurisdiction. One alert per `corpus_build_sha` age-threshold breach. This is consistent with FR-RAG-IDX-08 (single shared index) and avoids the "alert storm" failure mode of per-partition thresholds.
4. **Alert trigger** — emit a `corpus_stale` alert to on-call + Service Bus when **both**:
   - `corpus_build_sha.generated_at` age exceeds 14 days, **and**
   - no ingest job has run in the last 48 hours.
   The 48-hour grace prevents alert noise during long rebuilds.
5. **Reversible flag** — `feature.corpus_freshness_alert.enabled` (Reversible per A12). When disabled, the alert is suppressed but the underlying staleness assessment is still written to the audit log so post-incident review can reconstruct the timeline. The flag flip itself emits a `corpus_freshness_alert_disabled` audit event (and is reversible mid-incident per Spec 029 FR-008).

## Rationale

- **Why 0100 AEST?** Aligns with the broader AMA "nightly maintenance" window already used by the recovery-catalogue and sample-data refresh jobs; minimises operator-side surprises and overlaps with the existing on-call rotation. The `corpus-ingest.yml` cron was migrated from `0 18 * * *` UTC to `0 14 * * *` UTC during F-A8 (T213).
- **Why a 14-day red threshold?** Australian disaster-doctrine handbooks publish quarterly cycles, but the in-between hot-fix bulletins (BoM advisories, NEMA memoranda) flow on a 1–2 week cadence. Past 14 days, the corpus is increasingly likely to omit a recent advisory; the dual-condition (age > 14 AND no ingest in 48 h) prevents flicker.
- **Why per-global-index, not per-jurisdiction?** Single-index economics (FR-RAG-IDX-08); per-partition thresholds would multiply alerts without adding signal — drift in one jurisdiction is operationally a corpus-wide concern.
- **Why Reversible, not Locked-on?** Operators must be able to silence the alert during planned maintenance windows that exceed 48 h (e.g. a month-long licence-clearance pause). Reversible matches Pass 2 Q-P2-08.
- **Why colour bands at 7 / 14, not 14 / 28?** The yellow band is a "soft warning" that lets PIO/IC step in early; the red band is the alert trigger. This matches the Operator-Auditor preference expressed in the R3 memo.

## Consequences

**Positive**
- Operators have an immediately legible 7-day yellow / 14-day red signal in the citation surface.
- SRE has automated nightly drift detection — the F-SRE-01 finding closes.
- No per-jurisdiction telemetry complexity; one alert per corpus per breach.
- Replay path unchanged: `corpus_build_sha` remains the canonical replay key; the UI just renders its `generated_at` more legibly.

**Negative / mitigations**
- A long planned outage of the ingest pipeline (> 48 h) trips the red band even when there is no real staleness. Mitigated by the Reversible flag — operators can suspend the alert with audit visibility.
- The colour bands assume Australian English LTR layouts; right-to-left and high-contrast modes may need bespoke palettes. Tracked under the F-A12 accessibility baseline.
- Operators may interpret "yellow" as "ignore me until red". Mitigated by the runbook (`docs/runbooks/036-foundry-rag-corpus-stale.md`) which explicitly lists the four causes of staleness.

## Cross-references

- Cluster A8 in `specs/036-foundry-rag-grounding/spec.md` Session 3.
- Pass 1 Q-P1-05, Pass 2 Q-P2-08 in spec.md Sessions 4 + 5.
- Schema `contracts/staleness_alert.schema.json`.
- Existing `infra/modules/ai-search-blue-green.bicep` parity gate; orchestrator `apps/api/app/services/corpus_freshness.py`.
- Tasks T212–T217.
- Runbook `docs/runbooks/036-foundry-rag-corpus-stale.md`.
- Plan phase F-A8 in `specs/036-foundry-rag-grounding/plan.md`.
