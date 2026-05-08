# Data Model — Spec 036 Foundry RAG Grounding

**Branch**: `036-foundry-rag-grounding` | **Date**: 2026-05-08 | **Phase**: 1 (design)
**Inputs**: [`spec.md`](./spec.md) §Key Entities, [`research.md`](./research.md), persona memos.

This file is the canonical entity model for spec 036. Every entity is either **NEW** or **EXTENDED** from a pre-existing spec. JSON-schema mirrors live under [`contracts/`](./contracts/) and `packages/schemas/`. Pydantic v2 models live under `packages/domain/` (extended additively).

---

## Entity catalogue

| Entity | New / Extended | Source of truth | FR anchors |
|---|---|---|---|
| `CorpusEntry` | EXTENDED (read-only consumer) | `docs/corpus/<jurisdiction>/<topic>/source.json` | FR-RAG-IDX-01, -02, -07 |
| `Chunk` | NEW | Azure AI Search index `corpus-v{N}` | FR-RAG-IDX-02, -03, -04 |
| `RetrievalRequest` | NEW | `apps/agents/common/retrieval_client.py` (in-process) | FR-RAG-AG-01 |
| `RetrievalResult` | NEW | `apps/agents/common/retrieval_client.py` (in-process) | FR-RAG-AG-01 |
| `Citation` | NEW (wire format) | [`contracts/citation-envelope.json`](./contracts/citation-envelope.json) | FR-RAG-AG-03, FR-RAG-SIM-02 |
| `AuditRecord` (LLM-call) | EXTENDED | Cosmos DB `audit_records` container + Blob append-only archive | FR-RAG-AG-02, FR-RAG-NS-01..09, FR-RAG-SIM-04, FR-RAG-CV-03 |
| `CarveoutRegistryEntry` | EXTENDED (registry row count grows) | `infra/parameters/foundry-carveout.yaml` (schema unchanged) | FR-RAG-CV-01, -02, -04 |
| `OfflineCacheManifest` | NEW | Field Coordinator-aligned device disk; built by `apps/ingest-runner/src/ama_ingest/offline_bundle.py` | FR-RAG-LS-02 |
| `RagOptoutAdr` | NEW | `docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-*.md` | FR-RAG-NS-01..09 |
| `EquivalenceTestResult` | EXTENDED (reuses spec-033 FR-023 shape) | `apps/eval-runner/` artefacts | FR-RAG-FM-06 |

---

## CorpusEntry (read-only consumer)

A single source's `{handbook.md, source.json, images/}` tuple under `docs/corpus/`. **Spec 036 does not modify the corpus build pipeline (OOS-3)** — the entity is consumed read-only by the ingest pipeline.

**Fields** (from `source.json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `jurisdiction` | enum | yes | `act \| nsw \| nt \| qld \| sa \| tas \| vic \| wa \| national \| aidr` (FR-RAG-IDX-08) |
| `topic` | string | yes | URL-safe slug (e.g. `evacuation-planning`) |
| `mode` | enum | yes | `full-text \| metadata-only \| excluded` (FR-RAG-IDX-02) |
| `sha256` | string | yes | SHA-256 of `handbook.md` rendered output (idempotency key) |
| `retrieved_at` | datetime | yes | ISO-8601 UTC |
| `publisher` | string | yes | E.g. `AIDR`, `NSW RFS`, `Bureau of Meteorology` |
| `edition` | string | optional | E.g. `2023 edition`, `v2` |
| `licence` | string | yes | SPDX-style identifier or named publisher licence |
| `etag` | string | optional | For polite conditional GET on re-fetch (`docs/corpus/README.md`) |
| `last_modified` | datetime | optional | Source-side `Last-Modified` header echo |

**Validation rules**:
- `mode` MUST be one of the three values; CI lint blocks any other value (FR-RAG-IDX-02).
- `mode == "excluded"` → entry MUST NOT be referenced from any agent prompt template (FR-RAG-IDX-02 + Edge Case "Excluded source crept into a prompt template").
- Every entry referenced by `INDEXING-LICENCE-INVENTORY.md` (FR-RAG-IDX-07) MUST have a matching `source.json` and vice versa; CI lint enforces.

**Lifecycle**: write-controlled by the corpus build pipeline at `scripts/disaster_corpus/`; read-controlled by the ingest pipeline (this spec) and by the manifest builder (already present).

---

## Chunk (NEW)

A retrieval unit produced from a `mode == "full-text"` `handbook.md`. Persisted as a document in the Azure AI Search `corpus-v{N}` index.

**Fields**:

| Field | Type | Required | Index attributes | Notes |
|---|---|---|---|---|
| `chunk_id` | string | yes | key | UUID-v5 of `(corpus_entry_id, page, chunk_offset_in_page)` for stable identity across re-runs |
| `corpus_entry_id` | string | yes | filterable | `<jurisdiction>/<topic>` |
| `jurisdiction` | enum | yes | filterable, facetable | values per CorpusEntry.jurisdiction |
| `topic` | string | yes | filterable, facetable | |
| `page` | int | yes | filterable, sortable | 1-indexed |
| `text` | string | conditional | searchable (BM25) | present iff `licence_mode == "full-text"`; OMITTED for `metadata-only` (R-11) |
| `tokens` | int | yes |  | post-tokeniser count; ≤ 1024 (R-04) |
| `embedding` | float[3072] | conditional | vector(3072) | present iff `licence_mode == "full-text"`; OMITTED for `metadata-only` |
| `embedding_model_id` | string | yes | filterable | E.g. `text-embedding-3-large` (R-02); exactly one value per index (R-05 signal 4) |
| `corpus_build_sha` | string | yes | filterable | The `corpus_build_sha` active at ingest time |
| `sha256_of_chunk` | string | yes | retrievable | SHA-256 of `text` (or of `(jurisdiction, topic, page, summary)` for `metadata-only`) |
| `licence_mode` | enum | yes | filterable | `full-text \| metadata-only` (`excluded` chunks are never persisted) |
| `source_url` | string | yes | retrievable | Original publisher URL |
| `rendered_url` | string | yes | retrievable | `/docs/corpus/<jurisdiction>/<topic>/handbook.md#page-N` |
| `summary` | string | conditional | searchable, retrievable | present iff `licence_mode == "metadata-only"` (no body, just publisher-supplied summary) |
| `cross_page` | bool | optional | filterable | `true` iff this chunk overlaps a page boundary (R-04) |

**Index schema constraints**:
- Exactly one distinct value of `embedding_model_id` per `corpus-v{N}` index (R-05 signal 4; ingest lint enforces).
- `vector` field configured at 3072 dimensions, HNSW algorithm with default `m=4, efConstruction=400, efSearch=500` (research will tune post-launch per AI/ML memo).
- Filterable fields: `corpus_entry_id`, `jurisdiction`, `topic`, `page`, `embedding_model_id`, `corpus_build_sha`, `licence_mode`, `cross_page`.
- Semantic ranker enabled (`semanticSearch: 'standard'` in `infra/modules/ai-search.bicep`).

**Validation rules**:
- `tokens ≤ 1024` (R-04); ingest emits a `chunk_size_tokens` histogram and CI fails if any chunk > 1024.
- `licence_mode == "full-text"` → `text` AND `embedding` MUST be present.
- `licence_mode == "metadata-only"` → `text` AND `embedding` MUST be absent; `summary` MUST be present.
- `embedding_model_id` value MUST equal the index-level invariant; ingest fails on mismatch.

**State transitions**: Chunks are immutable. A change in `corpus_entry_id.sha256` triggers re-chunking only of that entry (FR-RAG-IDX-04 idempotency). A change in `embedding_model_id` triggers a full blue-green rebuild (R-05).

---

## RetrievalRequest (NEW)

Emitted by every grounded agent and by the simulation Controller.

```json
{
  "agent_name": "RiskAssessmentAgent",
  "jurisdictions": ["nsw"],
  "hazard_type": "bushfire",
  "query_text": "What is the AIIMS span-of-control for a Level 2 bushfire?",
  "top_k": 5,
  "classification_max": "OFFICIAL",
  "tenant_id": "agency-nsw-rfs",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Validation rules**:
- `jurisdictions` MUST be a non-empty subset of `{act, nsw, nt, qld, sa, tas, vic, wa, national, aidr}`.
- The retrieval client MUST union `jurisdictions ∪ {national, aidr}` server-side (FR-RAG-AG-04, R-03, US7).
- `classification_max` MUST be `OFFICIAL` for all spec-036 paths; any path that would carry above-OFFICIAL content opts out per FR-RAG-NS-07.
- `top_k` defaults to 5; per-agent override permitted via constructor; max 20.

---

## RetrievalResult (NEW)

```json
{
  "chunks": [{ /* Chunk projection — see Citation envelope */ }],
  "retrieval_latency_ms": 187,
  "embedding_model_id": "text-embedding-3-large",
  "corpus_build_sha": "f9c3a8...",
  "classification_filter_applied": false,
  "cache_hit": false,
  "alias_active_index": "corpus-v2"
}
```

**Validation rules**:
- `chunks[]` is empty if no relevant content (US3 acceptance scenario 3); the agent / sim controller must NOT fabricate a citation when chunks are empty (FR-RAG-AG-05, FR-RAG-SIM-03).
- `embedding_model_id` and `corpus_build_sha` MUST be propagated to the AuditRecord on the next inference call.

---

## Citation (NEW — wire format)

Used by both recommendation cards (FR-RAG-AG-03) and simulation SSE `citation` events (FR-RAG-SIM-02). Canonical schema: [`contracts/citation-envelope.json`](./contracts/citation-envelope.json).

```json
{
  "jurisdiction": "nsw",
  "topic": "evacuation-planning",
  "page": 47,
  "source_url": "https://example.gov.au/handbooks/...",
  "rendered_url": "/docs/corpus/nsw/evacuation-planning/handbook.md#page-47",
  "sha256_of_chunk": "f9c3...",
  "licence_mode": "full-text",
  "confidence": 0.84,
  "snippet": "When the area is deemed safe, ..."
}
```

**Validation rules** (R-11):
- `snippet` is **conditionally present** iff `licence_mode == "full-text"`; **omitted** for `metadata-only`.
- `licence_mode == "excluded"` MUST never appear in a Citation (server-side filter at retrieval).
- `confidence ∈ [0.0, 1.0]` computed per R-16 (min of embedding similarity, semantic coherence, licence-mode safety gate).
- `sha256_of_chunk` MUST match a chunk in the issuing call's `RetrievalResult.chunks[]`; otherwise the citation is hallucinated (FR-RAG-AG-05) → suppressed and `hallucinated_citation` audit event emitted.

---

## AuditRecord (LLM-call) (EXTENDED)

The pre-existing `audit_records` Cosmos container is extended additively. Each LLM call emits exactly one record. Append-only Blob archive (existing 7-year immutability policy from spec 030).

**Fields** (additive on top of the existing audit shape — the bold rows are NEW for spec 036):

| Field | Type | Required | Notes |
|---|---|---|---|
| `call_id` | string | yes | UUID; primary key |
| `timestamp_utc` | datetime | yes | |
| `agent_name` | string | yes | Or `SimulationController` for sim |
| `chat_turn_index` | int | optional | Set for sim chat turns; null otherwise |
| **`call_kind`** | enum | yes | `inference \| embedding` (R-13) |
| **`prompt_sha`** | string | conditional | required iff `call_kind == "inference"` |
| **`model_id`** | string | yes | E.g. `gpt-4o-mini` |
| **`model_version`** | string | yes | |
| **`deployment_alias`** | string | yes | The Foundry deployment name resolved from the env-var map |
| **`embedding_model_id`** | string | conditional | required iff `call_kind == "embedding"` OR if `rag_used == true` |
| **`corpus_build_sha`** | string | conditional | required iff `rag_used == true` |
| **`retrieved_chunks[]`** | array | conditional | required iff `rag_used == true`; each element: `{chunk_id, sha256_of_chunk, jurisdiction, topic, page, licence_mode, confidence}` |
| **`citations[]`** | array | conditional | required iff `rag_used == true`; rendered Citation envelopes |
| **`rag_used`** | bool | yes | `false` for FR-RAG-NS-01..09 paths and for `call_kind == "embedding"` |
| **`rag_optout_reason`** | string | conditional | required iff `rag_used == false` AND `call_kind == "inference"`; values: enum from FR-RAG-NS-01..09 |
| **`adr_pointer`** | string | conditional | required iff `rag_used == false`; e.g. `docs/decisions/036-foundry-rag-grounding/01-rag-optout-dependency-notifier.md` |
| **`gateway_decision`** | enum | yes | `allow \| deny \| redact` (FR-RAG-CV-03); `deny` records `gateway_deny_reason` |
| **`gateway_deny_reason`** | string | conditional | required iff `gateway_decision == "deny"` |
| **`hallucinated_citation_count`** | int | yes | 0 for non-grounded paths; ≥ 0 for grounded |
| `output_tokens` | int | yes | |
| `output_text_hash` | string | yes | SHA-256 of model output text |
| `operator_actions[]` | array | optional | Downstream operator decisions (approval, edit, dismiss) |
| `tenant_id` | string | yes | Tenant isolation |
| `correlation_id` | string | yes | Tracing correlation |

**Invariants**:
- `rag_used == true` → `retrieved_chunks[]` non-empty AND `corpus_build_sha` present AND `embedding_model_id` present.
- `rag_used == false` → `rag_optout_reason` non-empty AND `adr_pointer` non-empty AND `retrieved_chunks[]` empty.
- `call_kind == "embedding"` → `prompt_sha` absent AND `retrieved_chunks[]` empty AND `rag_used == false`.
- Every `citation.sha256_of_chunk` MUST appear in `retrieved_chunks[].sha256_of_chunk`; mismatches increment `hallucinated_citation_count` and emit a separate `hallucinated_citation` event.

**Storage**:
- **Hot tier**: Cosmos DB `audit_records` container (existing AU East), 90-day TTL.
- **Cold tier**: Append-only Blob `audit-archive/<yyyy>/<mm>/<dd>/...` (existing 7-year immutability policy from spec 030 reused).
- **Telemetry mirror**: Application Insights custom table `FoundryRAGAudit` (per Compliance memo §74) with KQL-friendly field projection.

**Replay invariant** (SC-011): `(corpus_build_sha, prompt_sha, model_version, retrieved_chunks[].sha256_of_chunk)` together permit byte-identical retrieval-input reconstruction ≥ 95% of the time across a one-month replay window.

---

## CarveoutRegistryEntry (EXTENDED — schema unchanged, row count grows)

Source of truth: `infra/parameters/foundry-carveout.yaml`. Schema: `infra/parameters/foundry-carveout.schema.json` (unchanged — re-stated here for the planning anchor).

```yaml
deployments:
  - model_name: gpt-4o-mini                 # FR-RAG-CV-01
    region: australiaeast                   # AU-default; non-AU only with §NN-2 carve-out
    purpose: production                     # production | shadow | evaluation | research
    business_justification: "Spec 036 FR-RAG-FM-01 — production inference for all agents and simulation chat (NN-2 §3 carve-out scope)."
    approver_identities:                    # minItems: 2
      - johnbilliris
      - <security-engineer-handle>
    review_date: 2027-05-08                 # ≤ 12 months from CD apply
    data_minimisation_required: true        # const: true (schema-enforced)
    classification_filter_required: true    # const: true (schema-enforced)
```

**Validation rules** (schema):
- `approver_identities.minItems == 2`.
- `data_minimisation_required` const `true`.
- `classification_filter_required` const `true`.
- `purpose` enum: `production | shadow | evaluation | research`.
- `review_date` ≤ 12 months from CD apply (FR-RAG-CV-01); `scripts/verify-carveout.ps1` enforces (FR-RAG-CV-02).

**Spec-036 additions** (rows, not schema): one row per Foundry inference deployment for each MAF Agent + the Simulation Controller (typically 1–2 deployments — `gpt-4o-mini` for drafting, `gpt-4o` for reasoning) + one row per non-AU carve-out (only as registry-permitted).

---

## OfflineCacheManifest (NEW)

Built by `apps/ingest-runner/src/ama_ingest/offline_bundle.py`; consumed by `apps/agents/common/offline_cache.py`. Bundle ≤ 500 MB per device (FR-RAG-LS-02).

```json
{
  "version": 1,
  "generated_at": "2026-05-08T11:00:00Z",
  "corpus_build_sha": "f9c3a8...",
  "ttl_days": 14,
  "stale_warning_days": 11,
  "embedding_model_id": "text-embedding-3-large",
  "entries": [
    {
      "chunk_id": "...",
      "jurisdiction": "nt",
      "topic": "cyclone-doctrine",
      "page": 12,
      "sha256_of_chunk": "..."
      // text + embedding inlined in a sibling .bin file referenced by chunk_id
    }
  ],
  "size_bytes_total": 487654321,
  "signatures": {
    "cosign_keyless": "MEYCIQDx...",            // Sigstore + GitHub OIDC (spec 032 FR-AI09)
    "age_detached": "-----BEGIN AGE ENCRYPTED FILE-----\n..." // age-encrypted detached signature for OIDC-less verify
  }
}
```

**Validation rules**:
- `size_bytes_total ≤ 500 × 1024 × 1024` (FR-RAG-LS-02 hard cap).
- `ttl_days == 14`; `stale_warning_days == 11` (R-07 — fixed defaults; per-deployment override only via the audit-logged feature flag described in R-07).
- Both signatures MUST be present; signature verification fails closed (R-07).
- `embedding_model_id` MUST match the chunks' `embedding_model_id`.

**Bundle composition**:
- Manifest JSON (≤ 1 MB).
- Per-chunk binary blob with `text` + `embedding` (lazy-loaded by `chunk_id`).
- The selection of chunks for the bundle is governed by `apps/ingest-runner/src/ama_ingest/offline_bundle.py` and follows the Field Coordinator persona memo's prioritisation: AIDR doctrine + national + each jurisdiction's most-cited handbooks (hazard thresholds, AIIMS span-of-control, evacuation centre setup checklists, sector boundaries).

**Lifecycle**:
- Built post-ingest on every `corpus_build_sha` change.
- Distributed to devices via secure enrollment channel (existing per spec 029 device-enrollment mechanism).
- Loaded by `offline_cache.py` on agent start; signature verification on every load.
- Evicted at day 14 (hard); UI badge surfaces from day 11 (R-07).
- On reconnect, queued offline audit entries are reconciled with original timestamps preserved (FR-RAG-LS-02; SC-009 ≤ 60s SLA).

---

## RagOptoutAdr (NEW)

A markdown ADR under `docs/decisions/036-foundry-rag-grounding/` for each of the nine FR-RAG-NS-01..09 carve-outs. **Required structure** (verified by `tests/contract/test_rag_optout_lint.py`):

```markdown
# ADR <NN> — RAG Opt-Out: <Carve-Out Name>

**FR**: FR-RAG-NS-<NN>
**Persona memo citation**: <file:line>
**Approver**: <name + role>
**Date**: 2026-05-08
**Status**: Accepted

## Context
<Why is RAG inappropriate for this path?>

## Decision
<Explicit statement that RAG is NOT invoked here.>

## Audit-log shape
<What `rag_optout_reason` value is recorded? What `adr_pointer` value points back here?>

## Code-comment marker
<Exact `# RAG-OPTOUT [FR-RAG-NS-<NN>]: <reason>` text used at the call site.>

## Consequences
<What does this opt-out preclude (e.g., post-hoc grounding)? What does it preserve (determinism, latency, hallucination-free output)?>
```

**Files** (one per FR; spec 036 requires all nine):

1. `01-rag-optout-dependency-notifier.md` (FR-RAG-NS-01)
2. `02-rag-optout-bom-live.md` (FR-RAG-NS-02)
3. `03-rag-optout-ga-live.md` (FR-RAG-NS-03)
4. `04-rag-optout-planning-collection.md` (FR-RAG-NS-04)
5. `05-rag-optout-logistics-transactional.md` (FR-RAG-NS-05)
6. `06-rag-optout-scenario-execution.md` (FR-RAG-NS-06)
7. `07-rag-optout-classified.md` (FR-RAG-NS-07)
8. `08-rag-optout-ci-lint.md` (FR-RAG-NS-08 — meta-ADR for the lint mechanism itself)
9. `09-rag-optout-observer-auditor.md` (FR-RAG-NS-09)

---

## EquivalenceTestResult (EXTENDED — reuses spec-033 FR-023 shape)

Emitted by `apps/eval-runner/` per agent during canary cutover (FR-RAG-FM-06). Spec 036 extends the shape with citation-fidelity fields (R-10, Phase E3):

```json
{
  "agent_name": "RiskAssessmentAgent",
  "golden_qa_fixture_id": "036-risk-v3",
  "corpus_build_sha": "f9c3a8...",
  "embedding_model_id": "text-embedding-3-large",
  "decision_equivalence_pct": 0.96,            // ≥ 0.95 to flip per spec-033 FR-023
  "schema_equivalence_pct": 1.00,              // == 1.00 to flip per spec-033 FR-023
  "citation_fidelity_pct": 0.78,               // ≥ 0.70 (spec-036 R-10 extension)
  "verbatim_source_match_pct": 0.92,           // ≥ 0.90 (spec-036 Quality-memo R2 extension)
  "hallucinated_citation_count": 0,
  "passed": true                               // AND of all four thresholds
}
```

**Validation rules**:
- All four thresholds MUST pass for `passed == true`; any one failing blocks the canary flip (FR-RAG-FM-06).
- `golden_qa_fixture_id` MUST be keyed by `(corpus_build_sha, embedding_model_id)` so re-runs are reproducible (Quality-memo §test data §E2E).

---

## Relationships (entity-relationship summary)

```text
CorpusEntry (1) ─── ingests into ──▶ Chunk (N)
Chunk (N)   ─── filtered by ───────▶ RetrievalResult.chunks[]
RetrievalRequest (1) ─── produces ─▶ RetrievalResult (1)
RetrievalResult (1) ─── projects to ▶ Citation (N)
Citation (N) ───── attached to ────▶ AuditRecord.citations[]
RetrievalResult (1) ─── recorded in ▶ AuditRecord.retrieved_chunks[]
AuditRecord (1) ──── one per ──────▶ inference call OR embedding call
RagOptoutAdr (1) ──── pointed to by ▶ AuditRecord.adr_pointer (where rag_used == false)
CarveoutRegistryEntry (1) ─── gates ▶ Foundry deployment via CD
OfflineCacheManifest (1) ─── caches ▶ Chunk (M ⊂ N) for Field Coordinator
EquivalenceTestResult (1) ─── gates ▶ per-agent Foundry canary flip (FR-RAG-FM-06)
```

---

## Schema-mirror locations

| Entity | JSON schema | Pydantic v2 |
|---|---|---|
| Citation | [`contracts/citation-envelope.json`](./contracts/citation-envelope.json) | `packages/domain/src/ama_domain/citation.py` |
| AuditRecord | [`contracts/audit-record-llm-call.json`](./contracts/audit-record-llm-call.json) | `packages/domain/src/ama_domain/audit_record.py` (extended) |
| OfflineCacheManifest | [`contracts/offline-cache-manifest.json`](./contracts/offline-cache-manifest.json) | `packages/domain/src/ama_domain/offline_cache.py` (NEW) |
| RetrievalRequest / RetrievalResult | inlined in [`contracts/retrieval-service.md`](./contracts/retrieval-service.md) | `packages/domain/src/ama_domain/retrieval.py` (NEW) |
| CarveoutRegistryEntry | `infra/parameters/foundry-carveout.schema.json` (existing) | n/a (YAML-only registry) |

---

## Validation matrix (entity × FR)

| Entity | Validated by | FR coverage |
|---|---|---|
| CorpusEntry | `tests/integration/test_corpus_entry_validation.py` (NEW) + `INDEXING-LICENCE-INVENTORY.md` lint | FR-RAG-IDX-01, -02, -07 |
| Chunk | `tests/integration/test_chunk_index_invariants.py` (NEW) + ingest pre-flight lint | FR-RAG-IDX-02, -03, -04 |
| RetrievalRequest/Result | `tests/contract/test_retrieval_service.py` (NEW) | FR-RAG-AG-01, -04 |
| Citation | `tests/contract/test_citation_envelope.py` (NEW) | FR-RAG-AG-03, FR-RAG-SIM-02 |
| AuditRecord | `tests/contract/test_audit_record_shape.py` (NEW) | FR-RAG-AG-02, FR-RAG-NS-*, FR-RAG-SIM-04 |
| OfflineCacheManifest | `tests/integration/test_offline_cache.py` (NEW) | FR-RAG-LS-02 |
| RagOptoutAdr | `tests/contract/test_rag_optout_lint.py` (NEW) | FR-RAG-NS-01..09 |
| CarveoutRegistryEntry | `scripts/verify-carveout.ps1` (extended) + `tests/integration/test_carveout_enforcement.py` (NEW) | FR-RAG-CV-01..04 |
| EquivalenceTestResult | `apps/eval-runner` extended + canary flip CI gate | FR-RAG-FM-06 |

---

*End of data-model.md — see [`contracts/`](./contracts/) for the wire shapes.*
