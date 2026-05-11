# Contract — Corpus Ingest Pipeline (FR-RAG-IDX-01..08)

**Spec**: 036-foundry-rag-grounding
**Status**: DRAFT (spec.md frozen; this contract is the binding reference for `/speckit.tasks`)
**Owner module**: `apps/ingest-runner` (NEW Container Apps Job — see plan.md §Project Structure & R-08)
**Trigger**: `azd postprovision` (FR-RAG-IDX-05) + manual backfill + scheduled drift check.

This contract defines the **idempotent corpus → AI Search ingest pipeline** that:

- ingests the **whole** `docs/corpus/` tree (FR-RAG-IDX-01),
- honours per-source licence modes (FR-RAG-IDX-02),
- carries provenance metadata on every chunk (FR-RAG-IDX-03),
- is hashed-keyed idempotent and blue-green-rebuild aware on embedding-model changes (FR-RAG-IDX-04, R-05),
- produces a single jurisdiction-faceted index (FR-RAG-IDX-08),
- lints licence inventory in CI (FR-RAG-IDX-07).

It is **NEW infrastructure** (no existing equivalent in `apps/ingestion`, which is for live signals — verified during planning). REUSE: `infra/modules/ai-search.bicep` (additive params), `apps/eval-runner/foundry_client.py` (pattern), spec 032 carve-out registry.

---

## 1. Inputs

| Input | Source | Notes |
|---|---|---|
| Corpus tree | `docs/corpus/**` snapshot at `corpus_build_sha` | 155 `source.json` files across 10 jurisdiction roots; estimated ~10k chunks at first ingest |
| Embedding deployment | `AZURE_AI_PROJECT_DEPLOYMENTS` env CSV — selects the `text-embedding-3-large@<ver>=<deploy>` row | FR-RAG-IDX-02; resolved via `LiveFoundryChatClient` |
| AI Search endpoint + alias | `AZURE_SEARCH_ENDPOINT` + `AZURE_SEARCH_INDEX_ALIAS=corpus` | Alias points at the active `corpus-v{N}` |
| Licence inventory | `docs/corpus/INDEXING-LICENCE-INVENTORY.md` | FR-RAG-IDX-07 — lints against `source.json` files |
| Carve-out registry | `infra/parameters/foundry-carveout.yaml` | Embedding deployment row MUST be present |

---

## 2. Outputs

| Output | Sink | Notes |
|---|---|---|
| AI Search index documents | `corpus-v{N}` | One Chunk per page-aligned segment per `mode == "full-text"` source; one metadata doc per `mode == "metadata-only"` source (FR-RAG-IDX-02) |
| Index alias swap | `corpus` alias → `corpus-v{N+1}` | Atomic; only after parity gate (R-05) passes |
| OfflineCacheManifest | `bundles/corpus-v{N}/offline-manifest.json` | Per `contracts/offline-cache-manifest.json`; FR-RAG-LS-02 |
| Service Bus event | `topic.corpus-build-complete` | `{corpus_build_sha, alias_active_index, embedding_model_id, chunk_count, blue_green: bool, parity_gate: PASS\|FAIL}` |
| Ingest report | `azd postprovision` log + Application Insights `FoundryRAGIngest` table | Emits `chunk_size_tokens` histogram (R-04 enforcement) |
| `LICENCE-INVENTORY` lint result | CI step output | Fails build if `source.json` ↔ inventory drift |

---

## 3. Invariants

These are the contract-binding properties; every implementation MUST hold them.

### 3.1 Idempotency (FR-RAG-IDX-04)

For each `CorpusEntry`:

```
if existing_doc.sha256 == source.json.sha256:
    skip  # no re-chunk, no re-embed, no re-index
else:
    re-chunk + re-embed + upsert
```

A repeat invocation with no corpus changes MUST issue **zero** embedding calls and **zero** AI Search write operations (verified by ingest contract test).

### 3.2 Blue-green on embedding-model change (FR-RAG-IDX-04, R-05)

If the resolved `embedding_model_id` differs from the alias-active index's `embedding_model_id` (read from any chunk of the existing index), ingest MUST:

1. Provision a new index `corpus-v{N+1}` via `infra/modules/ai-search-blue-green.bicep` (NEW wrapper).
2. Re-chunk + re-embed the **full** corpus into the new index.
3. Run the **parity gate** (§3.3).
4. On gate PASS: atomically flip the `corpus` alias to `corpus-v{N+1}`.
5. Retain `corpus-v{N}` for **7 days** for rollback.
6. Emit `topic.corpus-build-complete` with `blue_green: true`.

SLA: cold rebuild ≤ 24 h; alias flip < 60 s (FR-RAG-IDX-04). Each `corpus-v{N}` index hosts **exactly one** `embedding_model_id` value (R-05 signal 4).

### 3.3 Parity gate (R-05) — 4 signals

The alias flip is gated on all four signals passing:

| # | Signal | Threshold | Action on fail |
|---|---|---|---|
| 1 | Chunk count delta | new vs old `chunk_count` within ±5% (excluding documents with new `corpus_entry_id.sha256`) | Halt flip; manual review |
| 2 | Embedding cost ratio | new total embedding cost ≤ 1.3× old | Halt flip; cost investigation |
| 3 | Eval-runner equivalence | spec 033 FR-023 ≥ 95% decision-equivalence + 100% schema-equivalence on a fixed regression suite | Halt flip; agent regression |
| 4 | Single-model invariant | new index has exactly 1 distinct `embedding_model_id` | Halt flip; ingest bug |

Failed gates emit `topic.corpus-build-complete` with `parity_gate: FAIL` and a per-signal breakdown; alias is NOT flipped; on-call SRE paged.

### 3.4 Provenance on every chunk (FR-RAG-IDX-03)

Every Chunk doc MUST carry: `jurisdiction, topic, page, sha256_of_chunk, source_url, retrieved_at, licence_mode, corpus_build_sha, embedding_model_id`. Ingest validates this at write time; missing fields fail the build.

### 3.5 Licence-mode partitioning (FR-RAG-IDX-02)

| `source.json.mode` | Behaviour |
|---|---|
| `full-text` | Chunk page-aligned, embed, index body + metadata |
| `metadata-only` | Index title, URL, summary, jurisdiction, topic — do NOT embed body, do NOT store body text |
| `excluded` | Do NOT index at all; skipped before embedding budget is touched |

Lint: an `excluded` chunk surfaced anywhere downstream is a Sev2 incident.

### 3.6 Single index, jurisdiction-faceted (FR-RAG-IDX-08)

Output is **one** index `corpus-v{N}` with `jurisdiction`, `topic`, `licence_mode` filterable fields. Per-jurisdiction proliferation is forbidden. Capacity alert fires at 70% utilisation.

### 3.7 Carve-out registry alignment (FR-RAG-CV-01..02)

Before the first embedding call, ingest MUST verify the resolved embedding deployment's `(model_name, region)` is present in `infra/parameters/foundry-carveout.yaml` with `review_date` ≤ 12 months out (`scripts/verify-carveout.ps1`-extended). Missing row → fail-closed (no embedding calls issued).

---

## 4. CLI surface

```bash
# Local + CI invocation
python -m ama_ingest \
  --corpus-root docs/corpus \
  --search-endpoint $AZURE_SEARCH_ENDPOINT \
  --index-alias corpus \
  --embedding-model text-embedding-3-large@2024-12-15 \
  --corpus-build-sha $CORPUS_BUILD_SHA \
  --mode {full|incremental|dry-run} \
  --offline-bundle-out bundles/corpus-v$N/offline-manifest.json
```

| Mode | Behaviour |
|---|---|
| `full` | Force blue-green rebuild regardless of `embedding_model_id` match. Used for emergency reseed. |
| `incremental` | Default. Skips entries whose `sha256` matches; re-embeds only changed entries. |
| `dry-run` | Plan-only. Prints chunks-to-write, chunks-to-skip, embedding calls projected, cost estimate. |

Exit codes: `0` success, `1` lint fail (licence inventory / carve-out), `2` parity gate fail, `3` AI Search write error, `4` Foundry embedding error, `5` config error.

---

## 5. Chunking strategy (R-04)

| Property | Value | Rationale |
|---|---|---|
| Target chunk size | 1024 tokens (post-tokeniser) | Balance recall vs context-window cost |
| Overlap | 10% (≈100 tokens) | Avoids boundary-clipping at page seams |
| Split heuristic | Page-aligned first; H2 (`##`) split for long pages | Preserves citation page-anchor (FR-RAG-AG-03) |
| Cross-page chunks | `cross_page=true` flag | Surfaces in ingest histogram for tuning |
| Hard ceiling | 1024 tokens — CI fails any chunk above | R-04 |

Tokeniser: `tiktoken cl100k_base` (matches OpenAI/Foundry embedding tokenisation).

---

## 6. Audit (FR-RAG-AG-02 / R-13)

Every embedding call emits an `AuditRecord` with `call_kind="embedding"`, populated `embedding_model_id` and `deployment_alias`, `rag_used=false`, `prompt_sha` absent, `retrieved_chunks=[]`. This is the only path that emits `call_kind="embedding"` audit rows.

Ingest also emits a single ingest-summary record:

```json
{
  "kind": "ingest_summary",
  "corpus_build_sha": "f9c3a8…",
  "started_at": "2026-05-08T10:00:00Z",
  "completed_at": "2026-05-08T13:42:00Z",
  "chunks_written": 9847,
  "chunks_skipped_idempotent": 412,
  "embedding_calls": 9847,
  "embedding_total_cost_usd": 18.94,
  "blue_green": true,
  "parity_gate": "PASS",
  "alias_flipped_to": "corpus-v3",
  "previous_index_retained_until": "2026-05-15T13:42:00Z"
}
```

---

## 7. Failure modes

| Failure | Behaviour | Audit |
|---|---|---|
| `source.json.sha256` mismatch with `handbook.md` content | Hard fail; ingest aborts before embedding | `corpus_integrity_error` |
| Foundry embedding 4xx | Hard fail with deployment + scope details | `foundry_config_error` |
| Foundry embedding 5xx / timeout | Retry 3× with exponential backoff (1s/4s/16s); then hard fail | `foundry_transport_error` |
| AI Search write 5xx | Retry per-batch 3×; surface partial-write report | `search_write_error` |
| Parity gate fail (any signal) | Halt alias flip; previous alias remains active | `parity_gate_failed` |
| Carve-out row missing | Fail-closed before any embedding call | `carveout_missing` |
| Licence inventory drift | Fail at lint step before ingest starts | `licence_inventory_drift` |
| Chunk > 1024 tokens | Fail build (R-04 invariant) | `chunk_size_violation` |

All failure modes are recoverable: ingest can be re-run idempotently after fixing the underlying issue.

---

## 8. CI / CD integration

- **`ci.yml`**: Adds licence-inventory lint (`tools/lint/check_licence_inventory.py`) + chunking dry-run on PR (validates that `source.json` shape changes don't break ingest).
- **`cd.yml`**: After `azd up`, invokes `apps/ingest-runner` Container Apps Job in `incremental` mode (FR-RAG-IDX-05).
- **`corpus-ingest.yml`** (NEW workflow): Scheduled drift check (daily) — runs `dry-run` mode and pages on-call if unexpected drift detected.

---

## 9. Reuse-vs-new (R-08)

| Asset | Decision |
|---|---|
| `apps/ingestion` (live signals) | REUSE for inspiration only — different domain (live BoM/GA feeds). NOT shared code. |
| `infra/modules/ai-search.bicep` | REUSE with additive parameters (`vectorDimensions`, `embeddingDeploymentName`, `jurisdictionValues`, `capacityAlertThresholdPercent`). |
| `infra/modules/ai-search-blue-green.bicep` | NEW wrapper that composes `ai-search.bicep` with alias management + retention. |
| `apps/eval-runner/foundry_client.py` | REUSE pattern (constructor-injectable seam) — replicated in `apps/agents/common/foundry_chat_client.py`. |
| `scripts/verify-carveout.ps1` | EXTEND to verify embedding deployment row before ingest. |
| `scripts/disaster_corpus/*.py` | UNTOUCHED — corpus build pipeline (Assumption A1 in spec). |
| `apps/ingest-runner` | NEW Container Apps Job. |

---

## 10. Mapping to FRs / SCs / data-model

| Surface | FR / SC / Source | Notes |
|---|---|---|
| Whole-tree ingest | FR-RAG-IDX-01 | spec.md L222 |
| Licence-mode partitioning | FR-RAG-IDX-02 | spec.md L223–227 |
| Provenance fields | FR-RAG-IDX-03 | spec.md L228 |
| Idempotency + blue-green | FR-RAG-IDX-04 / R-05 | spec.md L229; research.md R-05 |
| `azd postprovision` + CD trigger | FR-RAG-IDX-05 | spec.md L230 |
| Private-Endpoint AI Search | FR-RAG-IDX-06 | spec.md L231 |
| `INDEXING-LICENCE-INVENTORY.md` lint | FR-RAG-IDX-07 | spec.md L232 |
| Single index, jurisdiction-faceted | FR-RAG-IDX-08 | spec.md L233 |
| Embedding-call audit | FR-RAG-AG-02 / R-13 | data-model.md §AuditRecord |
| Cold rebuild ≤ 24 h | SC (spec 036 §Success Criteria) | spec.md FR-RAG-IDX-04 |
| Alias flip < 60 s | SC | spec.md FR-RAG-IDX-04 |
| Carve-out registry alignment | FR-RAG-CV-01..02 | spec.md L215–216 |
| Embedding model selection | FR-RAG-IDX-02 / R-02 | research.md R-02 (`text-embedding-3-large` 3072 dims) |
| Chunk size cap | R-04 | research.md R-04 |
| Parity gate | R-05 | research.md R-05 |
| Test seam | FR-RAG-FM-07 (ingest reuses `LiveFoundryChatClient`) | spec.md L211 |
