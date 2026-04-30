# ADR-036: Azure AI Search (Standard S1) for AIDR RAG

## Status

Proposed (target: Accepted upon merge of spec-032 Stream-6 task T601/T602).

## Context

Spec 032 FR-AI01 requires retrieval-augmented generation over the AIDR handbook corpus (`docs/aidr/`) so that agent recommendations cite authoritative source material. The rubric flags the absence of grounded RAG (item 9.1) as the gap that limits the AI Integration score.

## Decision

Provision an **Azure AI Search Standard S1** index in **Australia East** (production) and **Basic** in dev/staging, with the following design:

| Setting | Value |
|---|---|
| Region | Australia East (paired: Australia Southeast for read-only failover) |
| SKU | Standard S1 (prod) / Basic (dev/staging) |
| Replicas / Partitions | 1 / 1 (≤ 25 GB index headroom) |
| Public network access | **Disabled** — Private Endpoint only |
| Index name | `aidr-handbooks` |
| Index profile | Hybrid (BM25 + vector) |
| Vector field dimension | 1536 |
| Embedding model | Azure OpenAI `text-embedding-3-large` (AU East deployment) |
| Chunking | 800 tokens with 200-overlap |
| Metadata fields | `handbook_id`, `chapter`, `page`, `version`, `language` |
| Cost autoscale alert | At 70% of S1 search-units per hour |

### Indexing scope (gated)

- Only handbooks with **explicit licence approval** in `docs/aidr/LICENCE-INVENTORY.md` are full-indexed.
- Handbooks pending approval default to **metadata-only** mode (titles + chapter summaries only).
- The AIDR handbook collection is referenced by the constitution as the framework basis (`AIDR Handbook Collection Reference` table); the per-handbook inventory captures redistribution rights and per-handbook indexing approval signed off by Compliance Auditor + Solution Architect.

### Retrieval contract

- `RagService.search(query, top_k=5)` returns `RagCitation[]` (see `data-model.md` E-02).
- Each citation MUST include `handbook_id`, `chunk_id`, `score`, and a `quote` ≤ 500 chars.
- Recommendation cards display the citation list and a "view source" deep-link.

## Consequences

### Positive

- First-party Azure service; AVM module exists; AU residency satisfied.
- Hybrid retrieval (BM25 + vector) consistently outperforms pure vector for Emergency-Management terminology (e.g. "Watch and Act" matches keywords + semantics).
- Citation contract makes provenance visible to operators (NN-1 + NN-4 supportive).

### Negative / accepted

- Standard S1 baseline cost (~AU$ 250/mo) added to monthly run-rate. Justified by the rubric uplift; tracked in the cost-report template (FR-D03).
- Vector dim 1536 doubles index size vs BERT-class 768; Standard S1 still has ample headroom.

### Alternatives considered

- **Cosmos DB Vector index** — preview in AU East at decision time; rejected for prod readiness.
- **Azure OpenAI on-your-data** — black-box retrieval; doesn't expose chunk-level citations needed for rubric item 9.1; rejected.
- **Self-hosted FAISS or Qdrant on Container Apps** — operationally heavy; non-Azure-native; rejected.

## Compliance

- **NN-2 (Data sovereignty)**: AU East with no cross-region replication; index data is plain handbook text (publicly published) but is hosted inside the AU tenant.
- **NN-4 (Interoperability)**: index schema published in `data-model.md` and `contracts/`; `RagService` exposed via OpenAPI.
- **NN-5 (Graceful degradation)**: when AI Search is unavailable, agents fall back to template-only output (no recommendation grounding), with a degraded-mode header. Re-grounded once AI Search recovers.

## References

- Azure AI Search SLA + pricing: <https://azure.microsoft.com/en-us/pricing/details/search/>
- Spec 032 FR-AI01.
- AIDR Handbook Collection: see Constitution `AIDR Handbook Collection Reference` table.

---
*Author: AI/ML Engineer + Solution Architect personas via spec-032 Stream-0. Date: 2026-04-30.*
