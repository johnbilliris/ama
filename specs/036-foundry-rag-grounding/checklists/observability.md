# Observability Checklist: Microsoft Foundry-Based RAG Grounding

**Purpose**: Validate that FR-RAG-OBS-01..03 (retrieval metrics, ingest metrics, p95 latency alerting) are specified with the OTel-to-App-Insights bridge as the single emission transport, the retrieval-only-vs-end-to-end SLO split, and the precise emission point in `RetrievalService.retrieve()` so a Solution Architect + Principal Engineer can verify the observability plan before planning.
**Created**: 2026-05-09 (post R3 amend loop Sessions 3 + 4 + 5)
**Feature**: [spec.md](../spec.md)
**Cluster**: A11 (Observability) + Pass 1 Q-P1-06 (retrieval-only SLO) + Pass 2 Q-P2-05 (OTel-bridge emission point)
**Companion checklists**:
- [test-coverage-windows.md](./test-coverage-windows.md) — Per-session metric tags (FR-RAG-TEST-02 cross-ref)
- [migration.md](./migration.md) — End-to-end SC-012 chat-turn latency (cross-ref)
- [compliance.md](./compliance.md) — Blue-green replay (FR-RAG-IDX-04/04a cross-ref for `correlation_id`)

> **Scope of this file**: The three observability FRs added by R3 Cluster A11: **OBS-01 retrieval client metrics** (`retrieval_latency_ms`, `retrieval_chunk_count`, `retrieval_error_rate`; OTel transport; `RetrievalService.retrieve()` emission point), **OBS-02 ingest pipeline metrics** (`ingest_duration_seconds`, `chunks_processed`, `embedding_calls`, `ingest_errors`; Grafana dashboard `foundry-rag-ingest.json`), **OBS-03 retrieval-only p95 alert** (≤ 500ms threshold; explicitly NOT end-to-end; SC-012 governs end-to-end separately).

> **Item numbering**: Continues from `test-coverage-windows.md` (CHK270+).

## OTel Instrumentation Transport

> **Authority**: FR-RAG-OBS-01 + Pass 2 Q-P2-05; spec 014 FR-016 (OTel pipeline assumption); existing `apps/agents/common/lifecycle/heartbeat.py` + `apps/agents/common/resilience/pybreaker_adapter.py` precedents.

- [ ] CHK270 Is the **OTel-to-App-Insights bridge** cited as the canonical transport in FR-RAG-OBS-01 itself (not only in Pass 2 Q-P2-05 narrative)? [Clarity, Spec §FR-RAG-OBS-01]
- [ ] CHK271 Is the prohibition on **direct Application-Insights SDK calls in production paths** stated as an enforceable contract (lint, CI assertion, code-review hook) — not as guidance? [Acceptance Criteria, Spec §FR-RAG-OBS-01]
- [ ] CHK272 Are the precedent files (`apps/agents/common/lifecycle/heartbeat.py`, `apps/agents/common/resilience/pybreaker_adapter.py`) cited as proof the OTel-only convention is already in force in the codebase? [Traceability, Spec §FR-RAG-OBS-01]
- [ ] CHK273 Is the spec-014 FR-016 OTel-pipeline assumption ("can accept additional metrics without architectural changes") cited so a future contributor cannot redesign the transport? [Traceability, Spec §FR-RAG-OBS-01 vs `specs/014-azure-openai-integration/spec.md`]

## Retrieval Metric Emission Point

> **Authority**: FR-RAG-OBS-01 + FR-RAG-AG-01 shared retrieval client; `apps/agents/common/retrieval_service.py`.

- [ ] CHK274 Are the three retrieval metrics (`retrieval_latency_ms` histogram, `retrieval_chunk_count` histogram, `retrieval_error_rate` counter) each specified with type, percentiles (p50/p95/p99 for histograms), and unit? [Completeness, Spec §FR-RAG-OBS-01]
- [ ] CHK275 Are the metric tags (`agent_name`, `jurisdiction`, `hazard_type`) consistent with the `RetrievalRequest` Key Entity's field set? [Consistency, Spec §FR-RAG-OBS-01 vs §Key Entities]
- [ ] CHK276 Is the emission point (`RetrievalService.retrieve()` AI-Search-round-trip span) tied to the **single shared client** (`apps/agents/common/retrieval_service.py`) so all five grounded agents AND the Simulation Controller emit identically without duplication? [Coverage, Spec §FR-RAG-OBS-01 vs §FR-RAG-AG-01 / §FR-RAG-SIM-01]

## Retrieval-vs-Inference Span Separation

> **Authority**: Pass 1 Q-P1-06 (retrieval-only vs end-to-end SLO split); SC-012 (end-to-end ≤30% chat-turn latency).

- [ ] CHK277 Is the separation between the **AI-Search-round-trip span** and the **Foundry-inference span** explicit, with each emitting distinct metrics (`retrieval_latency_ms` vs `foundry_inference_latency_ms`)? [Clarity, Spec §FR-RAG-OBS-01]
- [ ] CHK278 Is the shared `correlation_id` requirement specified so traces can be stitched across the two spans (and across blue-green index versions per FR-RAG-IDX-04a)? [Coverage, Spec §FR-RAG-OBS-01 vs §FR-RAG-IDX-04a]
- [ ] CHK279 Is the retrieval-only SLO (FR-RAG-OBS-03 — 500ms p95 retrieval-only) clearly disambiguated from the end-to-end SC-012 (≤30% chat-turn latency increase), with **separate Application Insights metrics** for each so degradation can be diagnosed to the correct subsystem? [Consistency, Spec §FR-RAG-OBS-03 vs §SC-012]

## Ingest Metrics + Dashboard

> **Authority**: FR-RAG-OBS-02 + R3 Cluster A11; Grafana dashboard deliverable.

- [ ] CHK280 Are the four ingest metrics (`ingest_duration_seconds` gauge, `chunks_processed` counter, `embedding_calls` counter, `ingest_errors` counter) each typed and consistent with the existing ingest pipeline at `scripts/disaster_corpus/`? [Completeness, Spec §FR-RAG-OBS-02 vs §A1]
- [ ] CHK281 Is the Grafana dashboard `foundry-rag-ingest.json` named as a deliverable artefact with a clear ownership / location / dashboard panel set? [Traceability, Spec §FR-RAG-OBS-02]
- [ ] CHK282 Are ingest-error categorisation requirements specified (error class buckets, retry-vs-fail signals, alerting thresholds for sustained ingest_errors > N)? [Gap, Spec §FR-RAG-OBS-02]

## p95 Latency Alert (Retrieval-only SLO vs SC-012 End-to-End)

> **Authority**: FR-RAG-OBS-03 + Pass 1 Q-P1-06; Solution Architect persona memo (300ms target / 500ms enforced).

- [ ] CHK283 Is the **500ms p95** threshold and "5 minutes" alert window measurable (which percentile aggregation, which sliding window, which datapoint cardinality)? [Measurability, Spec §FR-RAG-OBS-03]
- [ ] CHK284 Is the "**target 300ms / enforced 500ms**" gap explained (Solution Architect target vs alert-fatigue threshold) so future tightening is anticipated and not surprising? [Clarity, Spec §FR-RAG-OBS-03]

## Notes

- **Item count (this file)**: 15 items across 5 sections (CHK270–CHK284).
- **Cross-references**: Items in this file frequently cite FR-RAG-OBS-01..03, FR-RAG-AG-01 (shared retrieval client), FR-RAG-SIM-01 (simulation controller), FR-RAG-IDX-04a (`correlation_id` blue-green stitching), SC-012 (end-to-end chat-turn baseline), `apps/agents/common/retrieval_service.py`, `apps/agents/common/lifecycle/heartbeat.py`, `apps/agents/common/resilience/pybreaker_adapter.py`, spec 014 FR-016 OTel pipeline, and Pass 1 Q-P1-06 / Pass 2 Q-P2-05.
- **Why this file is separate**: Observability is the **single most under-specified surface** in pre-amend specs (it is easy for an FR to say "emit a metric" without specifying transport / emission point / tag set / SLO scope). Splitting it out gives a Solution Architect a focused scope to clear in one pass.
