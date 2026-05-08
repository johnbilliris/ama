# Research / Decision Log — Spec 036 Foundry RAG Grounding

**Branch**: `036-foundry-rag-grounding` | **Date**: 2026-05-08 | **Phase**: 0 (pre-design)
**Inputs**: [`spec.md`](./spec.md) (Pass-1 + Pass-2 clarifications complete — no remaining `[NEEDS CLARIFICATION]`); R2 persona memos (`technical-architecture.md`, `technical-delivery.md`, `technical-quality.md`); existing patterns from specs 014 / 024 / 029 / 030 / 032 / 033.

> **Reading guide**: every decision below resolves either an explicit "Open Architecture Question" raised in a persona memo or a residual planning ambiguity surfaced by the cross-memo synthesis. Decisions marked **[BOUND]** are locked by spec 036 itself (Pass-1 / Pass-2 clarifications) and re-stated here only as the design anchor; **[OPEN→DECIDED]** decisions are the planning-stage choices made by this document. No `NEEDS CLARIFICATION` markers remain after this file.

---

## R-01 — Foundry SDK + AAD scope **[BOUND, restated for the design anchor]**

**Decision**: Use **`azure-ai-inference`** (`ChatCompletionsClient` + `EmbeddingsClient`) with `DefaultAzureCredential` and AAD scope **`https://cognitiveservices.azure.com/.default`**. Read endpoint from `AZURE_AI_PROJECT_ENDPOINT`; read deployment map from `AZURE_AI_PROJECT_DEPLOYMENTS` (CSV `modelId@version=deploymentName`).

**Rationale**: Bound by spec 036 FR-RAG-FM-01 + FR-RAG-FM-05 + Assumption A4 (resolved 2026-05-08 Pass-1). Mirrors `apps/eval-runner/src/ama_eval/foundry_client.py:39–80` exactly so all three migration anchors share one well-tested env-var contract; the existing `_AOAI_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"` constant in `apps/agents/maf_runtime/chat_client.py:21` is preserved across the migration. No `api_key=` kwarg in any production path (FR-RAG-FM-05).

**Alternatives considered**: (a) `azure-ai-projects` SDK — richer but heavier surface; eval-runner already settled on `azure-ai-inference` and the foundry-client pattern is reused here verbatim; (b) raw REST against the Foundry endpoint — defeats the seam pattern and forfeits SDK retry/auth; (c) keep `openai` SDK pointed at the Foundry-OpenAI-compatibility endpoint — fails FR-RAG-FM-04 lint and re-introduces the very import we're banning. **All rejected.**

**Owner**: AI/ML Engineer (per Architecture-memo top-1) + Software Developer (per Delivery-memo top-1).

---

## R-02 — Embedding model + vector dimensions **[BOUND]**

**Decision**: **`text-embedding-3-large` @ 3072 dimensions** as the v1 default for the corpus index; each AI Search index hosts exactly one `embedding_model_id`.

**Rationale**: Bound by FR-RAG-IDX-02 + Assumption A8 (resolved 2026-05-08 Pass-1). The higher-fidelity dimension is justified by life-safety content density per Constitution §I and matches the AI/ML Engineer persona-memo recommendation (Architecture-memo §AI/ML Engineer §Embedding model binding: "Storage footprint ~375 MB per 100K docs; retrieval latency +15–20% vs. 1536 dims but higher semantic precision justifies trade-off for emergency protocols").

**Alternatives considered**: `text-embedding-3-small @ 1536 dims` (cheaper, faster, but persona-memo flags as inadequate for life-safety doctrine density); `text-embedding-3-large @ 1536 dims` (truncated dimension — retains the model but loses the precision benefit; not aligned with AI/ML memo). **Both rejected.**

**Owner**: AI/ML Engineer.

---

## R-03 — Single index with jurisdiction filter, NOT per-jurisdiction proliferation **[BOUND]**

**Decision**: One `corpus-v{N}` index per `embedding_model_id` cohort, not one index per jurisdiction. `jurisdiction` is a filter field with values `{act, nsw, nt, qld, sa, tas, vic, wa, national, aidr}`. Jurisdiction-scoped retrieval unions own + `national` + `aidr` (e.g. NSW agent query → `jurisdiction in ('nsw','national','aidr')`).

**Rationale**: Bound by FR-RAG-IDX-08 + Pass-1 clarification. Preserves the FR-AI06 single-index economics (one Standard S1 SKU footprint) while the cross-jurisdiction union resolves User Story 7 disambiguation deterministically. Sector-eastern + southern-western + territory persona memos converge on filter-driven disambiguation, not index proliferation.

**Owner**: Solution Architect (per Architecture-memo §Solution Architect).

---

## R-04 — Chunking strategy **[OPEN→DECIDED]**

**Decision**: Chunker uses **H2 page-boundary primary split + 1024-token cap + 10% sliding overlap**, with **atomic preservation of code blocks and tables** (never split mid-table) and **cross-page reference de-normalisation** (a single sentence that spans two `## Page N` headings is duplicated into both chunks with overlap metadata `cross_page=true`).

**Rationale**: Resolves the open question raised in Architecture-memo §Principal Engineer ("What is the formal definition of 'page-aligned Markdown' chunking? Max size? Overlap? Cross-page refs?") and AI/ML-Engineer §Open ("Should chunking strategy differ by document type?"). The corpus README guarantees one `## Page N` heading per page (`docs/corpus/README.md`), so the H2 split is structurally accurate. 1024-token cap stays well under the `text-embedding-3-large` 8191 input limit and avoids silent truncation (Quality-memo R10). 10% overlap is the mid-point of the 5–20% range cited in standard RAG practice — large enough to absorb cross-page Q→A splits, small enough to keep storage growth bounded.

**Alternatives considered**:
- **800-token chunks, 0% overlap** — cheaper but loses semantic cohesion across page boundaries (cited Q→A often spans the very last sentence of page N and the first paragraph of page N+1).
- **2048-token chunks, 20% overlap** — fewer chunks but breaches the AI/ML-Engineer-memo guidance that life-safety doctrine should keep chunks tight enough that the embedder doesn't average across topics.
- **Per-document-type chunking (e.g. tables → row-level)** — adds parser complexity for marginal benefit; deferred to a follow-on iteration if telemetry shows table-heavy doctrine retrieval-quality lag.

**Validation gate**: Ingest emits a `chunk_size_tokens` histogram; ≥ 99.5% of chunks must be ≤ 1024 tokens; truncation rate must be 0 (we cap before embed, not at the embedder). Telemetry alert on regression.

**Owner**: AI/ML Engineer + Data Engineer (per Delivery-memo §Data Engineer).

---

## R-05 — Parity gate for blue-green alias flip **[OPEN→DECIDED]**

**Decision**: The blue-green alias flips from `corpus-v{N}` → `corpus-v{N+1}` only when **all four** parity-gate signals pass:

1. **Ingest count match** — `count(corpus-v{N+1}.documents)` is within ±1% of the reference snapshot of `corpus-v{N}` plus the documented delta from the change.
2. **100-chunk sampling parity** — random 100-chunk sample (stratified across all 10 jurisdiction roots) returns the same top-3 retrieval results between v{N} and v{N+1} for ≥ 95% of sample queries. Stratification: 8 chunks per state/territory + 8 from `national` + 12 from `aidr` (= 100, weighted toward AIDR doctrine density).
3. **Retrieval-quality delta < 5%** — golden-Q&A regression suite (extends spec 032 / spec 033 fixtures) returns decision-equivalence ≥ 95% AND citation-fidelity ≥ 0.7 on v{N+1}.
4. **Homogeneity invariant** — `count(distinct embedding_model_id) in corpus-v{N+1} == 1`.

If any signal fails → alias does not flip; SRE pages on-call; remediation per SRE-memo runbook 2 (manual rebuild). If signal 4 fails → automatic rollback (data-corruption signal per Architecture-memo R1 + Quality-memo R1).

**Rationale**: Resolves Solution-Architect open question ("which signals MUST pass for parity gate") and Quality-memo §Open ("sampling strategy for parity gate validation? Assume 100-chunk sample across jurisdictions?"). Four signals ensure that count, ranking, decision quality, and homogeneity are all proven before traffic shifts. The 95% sampling-parity threshold and the < 5% retrieval-quality delta come from the persona-memo synthesis. Cold-rebuild SLA ≤ 24h and alias flip < 60s are bound by FR-RAG-IDX-04.

**Alternatives considered**:
- **Single-signal gate (decision-equivalence only)** — what spec-033 FR-023 already does for cutover; insufficient here because index-rebuild has data-corruption failure modes (R1) that decision-equivalence won't catch.
- **Manual sign-off only** — fails the FR-RAG-IDX-05 "no manual steps" mandate for `azd up`.

**Owner**: Data Engineer + AI/ML Engineer + SRE (multi-owner because the gate sits across ingest + retrieval + ops).

---

## R-06 — Hybrid retrieval (BM25 + vector) with RRF **[OPEN→DECIDED]**

**Decision**: Default retrieval is **hybrid** — Azure AI Search semantic ranker over BM25 lexical results fused with the vector results via **Reciprocal Rank Fusion (RRF)**. Default weights: **vector 0.7, lexical 0.3** (life-safety precision > recall). Default `top_k = 5`; per-agent override permitted via constructor injection. Per-agent retrieval cache keyed by `(query_hash, jurisdictions, embedding_model_id)` with 5-minute TTL — cache key includes `embedding_model_id` so old/new indices during alias flip don't cross-pollute (API-Architect-memo §Caching strategy).

**Rationale**: Resolves AI/ML-Engineer open ("top-k & hybrid retrieval — RRF reasonable?") + API-Architect open ("retrieval-service cache shared or isolated?"). Vector-only loses against acronym-heavy doctrine (e.g. "FRNSW", "NTES", "SES-NSW") where lexical match is required for jurisdictional disambiguation; lexical-only loses against semantic queries ("what shelter options exist for cyclone-affected aged-care residents?"). RRF fuses both rankings without tuning a fragile linear combination of scores from incompatible scales. Cache is per-agent (not shared) to keep audit-per-agent cleaner — cross-agent cache shares would muddy the per-agent canary metrics during cutover.

**Alternatives considered**:
- **Vector-only** — fails lexical/acronym tests (see jurisdiction disambiguation suite, SC-010).
- **Lexical-only (BM25)** — fails semantic queries; loses the embedding investment.
- **Linear-combination fusion (e.g. `0.7·norm(vec) + 0.3·norm(lex)`)** — requires score normalisation across non-comparable scales; brittle.
- **Shared cross-agent retrieval cache** — better hit rate but pollutes per-agent canary audit and complicates licence-mode + tenant filtering.

**Validation gate**: Post-Phase-C the curated 50-query persona-driven test set (SC-010) must show 0 silent jurisdiction conflations across hybrid retrieval. RRF weights become a feature-flag-tunable parameter post-launch (Architecture-memo §AI/ML Engineer "Post-launch A/B test").

**Owner**: AI/ML Engineer.

---

## R-07 — Offline cache stale-age threshold + retry policy **[OPEN→DECIDED]**

**Decision**:
- **Hard TTL**: 14 days (bound by FR-RAG-LS-02).
- **Warning badge**: surfaced in UI from day 11 onward (`<DegradedModeBadge stale-age="11d / 14d max" />`).
- **Stale-eviction behaviour**: at day 14, cache is **evicted** (not silently re-served); offline queries fail-closed with "cache TTL exceeded — reconnect required" rather than fail-open (Field Coordinator must KNOW grounding is unavailable rather than silently consume stale doctrine).
- **Field-deployment override**: feature-flag-controlled 30-day extended TTL is permitted for declared field deployments (e.g. Far North NT cyclone season pre-position); the override is itself audit-logged with operator + reason + expiry, and the UI banner becomes red instead of yellow.
- **Signature-validation behaviour**: **fail-closed** — if either cosign or age-encrypted detached signature fails, cache is rejected and the agent operates in template-only fallback (per spec-014 chain). Audit logs `offline_cache_signature_invalid` event.

**Rationale**: Resolves three open questions in one shot: Architecture-memo §Principal Engineer "Should offline cache signature verification fail-open or fail-closed?", Quality-memo R3 "Offline cache TTL sync lag during disaster response", and Quality-memo §Open "Field Coordinator offline >14 days behaviour". Constitution §I (no silencing, no ungrounded life-safety decision) drives the fail-closed signature default; Constitution §IV (auditability) drives the audit-logged override mechanism. The 11-day warning gives Field Coordinators a 3-day recovery window before hard eviction.

**Alternatives considered**:
- **Fail-open on signature invalid** — wins availability but violates §I + §IV (we'd be grounding life-safety decisions on potentially-tampered doctrine).
- **No hard eviction, only warning** — wins continuity but allows silent staleness; rejected by Quality-memo R3.
- **Per-jurisdiction TTL** — added governance complexity for marginal benefit; the override mechanism handles edge cases.

**Owner**: Security Engineer (signature behaviour) + SRE (telemetry + alerting) + Field Coordinator persona owner (operational override semantics).

---

## R-08 — `apps/ingest-runner` as a new Container Apps Job (reuse vs new analysis) **[OPEN→DECIDED]**

**Decision**: Create a **new** `apps/ingest-runner` Container Apps **Job** (not a Container Apps service, not a script under `scripts/`, not an extension of `apps/ingestion/`).

**Rationale**: The pre-existing `apps/ingestion/` is for **live operational signals** — BoM XML, simulation events, etc. — and uses streaming pipeline shapes (worker, normalisers, pipeline_factory). The corpus ingest is a **batch, idempotent, on-demand job** (FR-RAG-IDX-04, FR-RAG-IDX-05) with a different input shape (`docs/corpus/**` filesystem snapshot), different output (Azure AI Search index + signed manifest), and different invocation cadence (`azd postprovision` + GitHub Actions on `docs/corpus/**` push). Folding it into `apps/ingestion/` would muddy the live/batch distinction. A bare `scripts/ingest_corpus.py` is rejected because (a) it must run in Azure under managed identity for Foundry embedding calls, (b) it consumes the same `azure-ai-inference` + `azure-search-documents` deps as `apps/agents` and shares the seam contract, (c) it must emit an audit `ingest_complete` event to Service Bus on success — none of which are script-shaped.

**Alternatives considered**:
- **Extend `apps/ingestion/`** — pollutes the live-signal codebase with batch concerns; failed `apps/ingest-runner` builds shouldn't break BoM ingestion.
- **Bare script under `scripts/disaster_corpus/`** — violates OOS-3 (we agreed not to modify the corpus build pipeline) and fails the managed-identity / dep-sharing tests above.
- **Build into `apps/eval-runner`** — tempting because it already has the Foundry client, but eval-runner has its own provisioner lifecycle (per-run resources) and the corpus is not a per-run resource.

**Owner**: Infrastructure / DevOps.

---

## R-09 — Per-agent Foundry quota governance **[OPEN→DECIDED]**

**Decision**: Each MAF Agent + the Simulation Controller declares a **soft per-agent token-per-minute budget** in `infra/parameters/foundry-quota.yaml` (NEW). The Foundry seam (`LLMClient` + MAF `chat_client` factory + simulation `controller_service`) reads its agent's budget at startup and exposes a `budget_used_pct` gauge; circuit breaker (`apps/agents/common/circuit_breaker.py` already exists) opens at 90% and forces template-fallback when at 100%. SRE alert at 70% triggers a quota-rebalance review.

**Rationale**: Resolves Architecture-memo R2 + Architecture-memo §AzPrinArch §Open ("How should quota be allocated per agent during concurrent canary migrations?") + Delivery-memo R2. During per-agent canary cutover (Phase C8), concurrent legacy + Foundry calls multiply token spend; without a per-agent budget the SES-style "everyone bursts at once" failure mode silences the platform (Constitution §I violation). The 90%/100% thresholds match the existing circuit-breaker semantics.

**Alternatives considered**:
- **Single platform-wide Foundry budget** — easier to manage but lets one agent starve others during canary; rejected.
- **No budget, rely on Foundry throttling** — Foundry returns 429 which gets retried; under canary load this cascades into multi-second p95 spikes that break SC-012.

**Owner**: Security Engineer + DevOps.

---

## R-10 — Hallucinated-citation confidence-downgrade threshold **[OPEN→DECIDED]**

**Decision**: Initial threshold is **`hallucinated_citation_count >= 1` per call → confidence downgrade by 1 band** (e.g. 0.85 → 0.65; band boundaries `[0.0, 0.6, 0.8, 1.0]` matching UX-memo §UX Designer §Citation rendering). The threshold is configurable per agent via `infra/parameters/citation-confidence.yaml`. Default is intentionally strict (one hallucination → downgrade) because a hallucinated citation in a life-safety context is an immediate Constitution §I + §IV failure.

**Rationale**: Resolves API-Architect-memo R1 + Software-Developer §Open ("Should hallucinated-citation confidence threshold be configurable per jurisdiction or uniform?") + spec FR-RAG-AG-05 ("above a configurable threshold"). Per-agent (not per-jurisdiction) configurability matches the canary cutover unit (we tune per agent during canary, not per jurisdiction); per-jurisdiction tuning is deferred to a follow-on iteration once telemetry is available.

**Alternatives considered**:
- **Threshold ≥ 3** — too permissive; first or second hallucination already breaches §I.
- **Per-jurisdiction threshold** — adds governance complexity for unproven benefit; defer.

**Owner**: Principal Engineer + Compliance Auditor.

---

## R-11 — Citation envelope shape (wire format for cards + SSE) **[OPEN→DECIDED]**

**Decision**: One canonical Citation envelope used by both recommendation cards (FR-RAG-AG-03) and simulation SSE events (FR-RAG-SIM-02):

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
  "snippet": "When the area is deemed safe, ..."     // omitted entirely if licence_mode == "metadata-only"
}
```

`snippet` is **conditionally present**: present iff `licence_mode == "full-text"`; **omitted** (not nulled, not masked) for `metadata-only` so that the wire format itself enforces redistribution rights. `licence_mode == "excluded"` chunks NEVER appear (filtered server-side at retrieval).

**Rationale**: Resolves API-Architect-memo §Open ("How should licence-mode filtering interact with the retrieval contract? snippet omitted or masked?") + UX-memo §Open ("How should licence-mode 'Excluded' citations be surfaced?"). Conditional presence is the strongest enforcement (parsers can't accidentally render a body that isn't there). Excluded sources must NEVER reach the wire — enforced at retrieval, not the envelope.

**Alternatives considered**:
- **Snippet always present, masked for metadata-only** — risk of accidental render; weaker enforcement.
- **Two separate envelope shapes per licence mode** — doubles the schema surface; client code branches awkwardly.

**Owner**: API Architect + Compliance Auditor.

---

## R-12 — Per-agent canary sequencing order **[OPEN→DECIDED]**

**Decision**: Canary flips proceed in this order (one per sprint or one per chaos-game-day cycle, never two concurrently):

1. **Monitoring** (lowest blast radius — primarily live BoM signals; RAG path is doctrinal-reasoning only)
2. **Risk Assessment** (high-leverage for the equivalence test because spec 032 already validated this surface for AIDR RAG)
3. **Evacuation** (life-safety primary; tested last among "decision agents" before Communication so any regression is caught before a public-facing surface)
4. **Resource Allocation** (deterministic provisioning core; equivalence test most stable here)
5. **Communication** (public-facing — second-to-last so the prior four agents have stabilised before any draft warning carries Foundry-grounded text)
6. **Simulation Controller** (last — composes all the prior agents' patterns; flipping after the operational fleet ensures rehearsal env always trails prod by one sprint until the final flip)

The Dependency Notifier never flips — it opts out per FR-RAG-NS-01.

**Rationale**: Resolves Quality-memo §Open ("Per-agent canary sequencing order?") + SRE-memo §Open ("Lower-risk agents get early cutover?"). The order is risk-ordered (low blast radius first) AND validation-ordered (Risk Assessment second because spec-032's golden Q&A is densest there, giving the highest-confidence equivalence-gate signal early). Communication penultimate keeps the public-facing surface protected by the most-validated upstream agents.

**Alternatives considered**:
- **Atomic flip (all six at once)** — rejected by FR-RAG-FM-06 (per-agent canary mandated).
- **Reverse order (Communication first)** — exposes the public-facing surface earliest and amplifies blast radius; rejected.

**Owner**: Software Developer + QA + SRE.

---

## R-13 — Audit log retention for embedding-call provenance **[OPEN→DECIDED]**

**Decision**: Embedding calls (corpus ingest) **DO** emit an audit record to the `FoundryRAGAudit` table — a separate sub-shape (`call_kind: "embedding"`) from inference calls (`call_kind: "inference"`). Embedding records carry `corpus_build_sha`, `embedding_model_id`, `chunk_count`, `embedded_token_count`, but NOT `prompt_sha` or `retrieved_chunks[]` (not applicable). Retention is the same 7-year append-only Blob archive (existing spec 030 immutability policy reused).

**Rationale**: Resolves Compliance-Auditor §Open ("Constitution §IV applies to every LLM call — does it apply to embedding requests?"). Constitution §IV says *every agent action, recommendation, and decision* — embedding calls themselves are not decisions, but the audit record is needed to prove (a) which embedding model was used to build a given index version, (b) when that index was built, (c) by which identity. Without it, post-hoc replay of a recommendation can't independently verify the corpus-side provenance.

**Alternatives considered**:
- **No audit on embedding calls** — fails reconstructibility (we'd have to trust the index manifest blindly).
- **Embedding audit in a separate retention class (e.g. 1 year)** — adds governance complexity for marginal cost saving.

**Owner**: Compliance Auditor + Data Engineer.

---

## R-14 — UX choices: collapsible citation panel + degraded-mode banner unification **[OPEN→DECIDED]**

**Decision**:
- **Risk Manager UI**: Citation cards rendered as a **collapsible accordion** below each recommendation; **default collapsed** for compact view; expanding the accordion shows up to 5 citations sorted by `confidence` descending; ARIA per Accessibility memo §45–69 (`role="button"`, `aria-expanded`, `aria-controls`).
- **Simulation chat panel**: Inline citation markers (`[1]`, `[2]`, ...) within the response text; **right-edge collapsible panel** shows the full `<CitationCard />`s in real-time as SSE events arrive; SSE events stream the same Citation envelope (R-11). Mobile: panel stacks below the response.
- **Degraded-mode banner**: **single unified banner** (not three concurrent badges) communicating root cause + recommended action — e.g. "Offline mode active — corpus 11d old, expires in 3d. Reconnect to refresh." Yellow for stale-cache + offline-cache active; red for retrieval-unavailable + cache evicted.
- **Confidence badges**: traffic-light colour coding (green ≥ 0.8, yellow 0.6–0.8, red < 0.6) **PLUS** an icon (✓ / ⚠ / ✗) so the signal is not colour-only (WCAG 2.2 AA, colour-blind safe).

**Rationale**: Resolves UX-memo §Open ("Should confidence badges include tooltip?", "How should excluded citations be surfaced?", "Should sim citation panel auto-expand?") + Architecture-memo §UX Designer R2 ("If stale + offline + alert all display, user may misunderstand severity"). Unified banner avoids the "three concurrent indicators" failure mode UX-R2. Default-collapsed cards prevent the citation panel from dominating the recommendation surface (UX-R1). Confidence-tooltip is deferred (UX complexity vs benefit unproven).

**Alternatives considered**:
- **Default-expanded citation cards** — overwhelms operator UI when top_k=5; rejected.
- **Three separate badges (stale + offline + retrieval-unavailable)** — UX-R2 failure mode.
- **Colour-only confidence indicator** — WCAG fail.

**Owner**: UX Designer + Accessibility Tester.

---

## R-15 — Reuse vs new for blue-green Bicep helper **[OPEN→DECIDED]**

**Decision**: **Add** `infra/modules/ai-search-blue-green.bicep` as a **wrapper** around the existing `infra/modules/ai-search.bicep` (do NOT modify the existing module beyond additive parameters). The wrapper:
- Provisions paired indices `corpus-v{N}` and (when rebuilding) `corpus-v{N+1}` as separate AI Search index resources within the existing search service.
- Manages an alias (`corpus-search`) using the AI Search alias REST API via a deployment script resource.
- Exposes `currentIndexName` and `previousIndexName` outputs so the ingest-runner job knows which index to write to.

The existing `ai-search.bicep` gains additive parameters `vectorDimensions` (default 3072), `embeddingDeploymentName` (string), `jurisdictionValues` (array), `capacityAlertThresholdPercent` (default 70). No removals.

**Rationale**: AVM-first policy + module-reuse default (per Architecture-memo §Azure Principal Architect §AVM Module Choices). Wrapping avoids breaking existing spec 032 callers of `ai-search.bicep`. Alias management via REST is the only path until the AVM module exposes alias as a first-class child resource.

**Alternatives considered**:
- **Modify `ai-search.bicep` in-place to add alias logic** — breaks spec 032's existing module contract; rejected.
- **Create a parallel AI Search service per index version** — doubles the SKU footprint; defeats the single-service economics (FR-AI06 inheritance).
- **Use a dedicated Azure Functions app to manage alias** — adds an unnecessary service; the deployment-script Bicep pattern is the right shape.

**Owner**: Azure Principal Architect + Infrastructure / DevOps.

---

## R-16 — Citation confidence model **[OPEN→DECIDED]**

**Decision**: `confidence ∈ [0.0, 1.0]` is computed as the **minimum** of three sub-scores:

1. **Embedding similarity** — cosine similarity between the query embedding and the chunk embedding (raw AI Search relevance score normalised to [0,1]).
2. **Semantic coherence with query** — Foundry-side rerank score from the AI Search semantic ranker.
3. **Licence-mode safety gate** — `1.0` for `full-text`, `0.7` for `metadata-only` (the operator should treat metadata-only-cited claims with caution because the body wasn't grounded), `N/A` for `excluded` (never returned).

Min-fusion (not weighted average) so a low score on any dimension caps confidence — life-safety bias toward conservatism.

**Rationale**: Resolves AI/ML-Engineer §Confidence scoring reuse + AI/ML-Engineer §Open ("Should confidence account for corpus age?"). Min-fusion prevents the "high-similarity, low-coherence" pathological case from being averaged into a misleading mid-score. Corpus age is **not** included in v1 because (a) the corpus has its own currency hooks (`source.json.retrieved_at`, `last_modified`) which the operator can inspect, (b) age-as-confidence-input couples the model to corpus-update cadence in ways that hide the underlying signals.

**Alternatives considered**:
- **Weighted average** — averages out the pathological cases; rejected for life-safety reasons.
- **Include corpus age** — defer; tooling already surfaces age via `source.json` inspection.

**Owner**: AI/ML Engineer.

---

## Summary — what's resolved here vs deferred to `tasks.md`

| Decision | Status |
|---|---|
| R-01 Foundry SDK + AAD scope | **[BOUND]** by spec |
| R-02 Embedding model + dims | **[BOUND]** by spec |
| R-03 Single index + jurisdiction filter | **[BOUND]** by spec |
| R-04 Chunking strategy | **[OPEN→DECIDED]** here |
| R-05 Parity gate signals | **[OPEN→DECIDED]** here |
| R-06 Hybrid retrieval + RRF + cache | **[OPEN→DECIDED]** here |
| R-07 Offline cache stale-age + sig fail-closed | **[OPEN→DECIDED]** here |
| R-08 ingest-runner as new Container Apps Job | **[OPEN→DECIDED]** here |
| R-09 Per-agent quota budget | **[OPEN→DECIDED]** here |
| R-10 Hallucinated-citation downgrade threshold | **[OPEN→DECIDED]** here |
| R-11 Citation envelope wire shape | **[OPEN→DECIDED]** here |
| R-12 Canary sequencing order | **[OPEN→DECIDED]** here |
| R-13 Embedding-call audit shape | **[OPEN→DECIDED]** here |
| R-14 UX choices (cards + banner + a11y) | **[OPEN→DECIDED]** here |
| R-15 Bicep wrapper for blue-green | **[OPEN→DECIDED]** here |
| R-16 Confidence model | **[OPEN→DECIDED]** here |

**Deferred to `tasks.md`** (planning-stage decisions that don't change the design but are too granular for this file):
- Specific golden Q&A fixture set per agent (Phase E3) — count, jurisdiction balance, source diversity.
- RRF weight A/B test plan (Architecture-memo §AI/ML Engineer post-launch) — when to run, success metric.
- Specific telemetry alert thresholds for `embedding_model_version_active` mismatch (Quality-memo runbook).
- Specific KQL queries for monthly compliance audit (Compliance-memo audit query templates).

**Status: ready for Phase 1 design.** No `NEEDS CLARIFICATION` remain; all open architecture questions from the three persona memos are either decided here or explicitly scoped to `tasks.md`.
