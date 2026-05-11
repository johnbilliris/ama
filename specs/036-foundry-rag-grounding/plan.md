# Implementation Plan: Microsoft Foundry-Based RAG Grounding for All Agents and Simulation Chat

**Branch**: `036-foundry-rag-grounding` | **Date**: 2026-05-08 | **Spec**: [`spec.md`](./spec.md)
**Input**: Feature specification from `specs/036-foundry-rag-grounding/spec.md`
**Status**: Draft (Phase 0 + Phase 1 complete; **Phase F R3 amend-loop appended 2026-05-08**; ready for `/speckit.tasks`)

---

## Summary

Spec 036 broadens the AIDR-only RAG path landed by spec [032](../032-rubric-improvements/spec.md) (FR-AI01..FR-AI10) to the **whole** `docs/corpus/` tree (national + every state/territory + Commonwealth + agency operational doctrine + hazard-specialty material) and **migrates** the production model plane from Azure OpenAI to Microsoft Foundry across the three remaining call sites. Five decision-making agents (Monitoring, Risk Assessment, Evacuation, Resource Allocation, Communication) plus the Simulation Controller chat (spec [024](../024-simulation-control-chat/spec.md)) acquire a shared retrieval client invoked before every prompt-bearing inference call; citations are emitted on every recommendation card and SSE turn; nine non-grounded paths (Dependency Notifier + 8 NS carve-outs) are explicitly opted out via `# RAG-OPTOUT [FR-RAG-NS-NN]` comments and matching ADRs. Every Foundry deployment is gated through the existing carve-out registry at `infra/parameters/foundry-carveout.yaml` (spec 032 FR-AI03a) per Constitution §NN-2 Amendment 1.2.0; data-plane resources stay in Australia East / Australia Southeast.

The technical approach reuses every existing seam — `infra/modules/ai-search.bicep`, `infra/bicep/modules/eval/foundry-deployments.bicep`, `infra/parameters/foundry-carveout.{yaml,schema.json}`, `scripts/verify-carveout.ps1`, the `apps/eval-runner/src/ama_eval/foundry_client.py` test-seam pattern, the spec-029 progressive-delivery feature flag, and the spec-033 FR-023 equivalence gate — and adds three first-party deltas: (1) a shared `RetrievalService` port behind a constructor-injectable Foundry chat-client seam (FR-RAG-FM-07), (2) blue-green AI Search index lifecycle wrapped around the existing module (FR-RAG-IDX-04), and (3) an idempotent corpus-ingest container job (`apps/ingest-runner`) wired into `azd postprovision` (FR-RAG-IDX-05). No new Azure service families are introduced.

---

## Technical Context

**Language/Version**: Python 3.13 (apps/api, apps/agents, apps/eval-runner, apps/ingestion, new apps/ingest-runner) on FastAPI + Pydantic v2; TypeScript 5.8 / React 19 / Next.js 16.2 (apps/web) for citation-card rendering; uv-managed virtualenvs.
**Primary Dependencies**: `azure-ai-inference` (NEW — Foundry inference SDK; replaces `openai.AzureOpenAI` at the three migration anchors), `azure-identity` (existing — `DefaultAzureCredential`, scope `https://cognitiveservices.azure.com/.default`), `azure-search-documents` (existing per spec 032 — vector + hybrid query), `azure-storage-blob` (existing — corpus snapshot + audit archive), `tenacity` (existing — retry on 429/503), `cosign` (existing — spec 032 FR-AI09 keyless signing), `age` CLI (NEW — additional offline-cache detached signature per FR-RAG-LS-02). MAF stays on `agent_framework_openai.OpenAIChatClient` factory signature but rewires its credential plumbing to Foundry (`apps/agents/maf_runtime/chat_client.py`).
**Storage**: Azure AI Search Standard S1 (AU East, Private-Endpoint-only — extends `infra/modules/ai-search.bicep`); Cosmos DB SQL API (existing AU East containers — `audit_records` extended with `retrieved_chunks[]`, `corpus_build_sha`, `embedding_model_id`, `rag_used`, `rag_optout_reason`); Azure Blob Storage (existing AU East — append-only `corpus-snapshots/` container holding the immutable `corpus_build_sha`-tagged tarball read by ingest, plus `offline-cache-bundles/` for Field Coordinator manifests). Microsoft Foundry inference endpoint deployed under the §NN-2 carve-out, AU-region first; non-AU deployments only via registry entry.
**Testing**: pytest with `pytest-asyncio` + `pytest-cov` (unit / contract / integration; reuses the eval-runner `chat_complete` injection pattern); Playwright (e2e for citation rendering + simulation SSE stream); `ruff check apps tests packages` + `ruff format --check` (existing CI gate at `.github/workflows/ci.yml:47`); `mypy --strict` per spec 032; `bicep lint` + `bicep build` on every infra PR; new `tests/contract/test_rag_optout_lint.py` enforces every `# RAG-OPTOUT [FR-RAG-NS-NN]` carries a matching ADR file.
**Target Platform**: Azure (AU East prod / AU Southeast DR + carve-out-registry-only non-AU Foundry inference) — Container Apps for `apps/agents`, `apps/api`, `apps/ingestion`, and the new `apps/ingest-runner` Container Apps Job; App Service for `apps/web`; AI Search service in dedicated AU East private subnet.
**Project Type**: Multi-app monorepo (web + backend api + agent runtime + ingest job + IaC); pnpm/Turborepo for the Node side, uv for the Python side.
**Performance Goals**: SC-012 caps simulation chat-turn p95 latency growth at ≤30% over the spec-024 baseline; Solution-Architect memo target retrieval p95 ≤300ms (memory-budget guideline; not a binding SC); blue-green alias flip <60s; cold rebuild ≤24h; offline cache lookup ≤50ms (local disk); corpus-ingest re-run on unchanged corpus ≤10% of cold-start runtime (SC-005); decision-equivalence ≥95% per spec-033 FR-023 gate before each per-agent canary flip.
**Constraints**: Constitution §I (no agent silencing — spec-014 `_generate_with_fallback` chain remains intact across migration window), §IV (every LLM call audit-logged with full retrieval provenance + corpus-build-SHA), §V/VI-C (warning-composition retrieval surfaces ATSI/CALD/Auslan corpus entries), §NN-2 (data residency AU + carve-out for Foundry model-hosting endpoints only — every data-plane resource fails CD if non-AU); zero `from openai import AzureOpenAI` / `AsyncAzureOpenAI` / `OpenAIChatClient(... mode="azure_openai" ...)` in production paths after final agent flips (FR-RAG-FM-04 lint binding atomically with legacy-client deletion, per FR-RAG-FM-06).
**Scale/Scope**: 155 `source.json` corpus entries across 10 jurisdiction roots (`act, aidr, national, nsw, nt, qld, sa, tas, vic, wa`); estimated ~10k page-aligned chunks at first ingest (re-evaluate after ingest per FR-RAG-IDX-08 70%-capacity alert); 6 agents + 1 simulation chat = 7 grounded surfaces × ~5 prompt-bearing call sites; 9 RAG-OPTOUT carve-outs (FR-RAG-NS-01..09) requiring matching ADR files; 1 carve-out registry, 1 AI Search service, 1 alias (`corpus-search`) over blue/green index pair (`corpus-v{N}` ↔ `corpus-v{N+1}`).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design. PASS at both gates — no §Complexity Tracking justifications required.*

| Principle / Section | Gate | Spec 036 binding | Status |
|---|---|---|---|
| **§I — Primacy of Life** | Every life-safety decision MUST cite authoritative source; agents MUST NOT silently degrade to ungrounded heuristics. | FR-RAG-AG-01..03 (citation on every recommendation), FR-RAG-AG-05 (no fabricated citations), FR-RAG-FM-06 (`_generate_with_fallback` chain intact across migration), FR-RAG-LS-01 (RAG never replaces human approval). | **PASS** — every prompt-bearing call site retrieves before inference; canary flag never silences an agent. |
| **§IV — Transparency & Auditability** | Every agent action logged with full provenance and rationale; reproducible from audit. | FR-RAG-AG-02 (`retrieved_chunks[]`, `corpus_build_sha`, `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `embedding_model_id` on every record), FR-RAG-NS-01..09 (`rag_used=false` + `rag_optout_reason` on opt-out paths), FR-RAG-AG-05 (`hallucinated_citation` audit event), FR-RAG-NS-08/09 (CI lint blocks new opt-outs without ADR), SC-011 (sampled byte-identical replay ≥95%). | **PASS** — append-only audit shape extended (see [`data-model.md`](./data-model.md)). |
| **§V — Warning & Public Information** | Public-facing warnings MUST follow AWS + ten warning principles; ATSI/CALD/Auslan/Easy-Read accessible. | FR-RAG-AG-06 (Communication agent retrieves ATSI/CALD/Auslan/Easy-Read corpus entries before drafting), FR-RAG-LS-03 (LLM-grounded draft + human-approved final both in audit), US8 acceptance scenarios. | **PASS** — Communication agent path adds licence-mode-aware retrieval before composition. |
| **§VI-C — Vulnerable Populations** | Priority for ATSI, CALD, disability, children, elderly, tourists, institutional care. | FR-RAG-AG-06, US2 acceptance scenario 2 (vulnerable-population reference cites Constitution VI-C and relevant ATSI/CALD entry). | **PASS** — same retrieval surface as §V. |
| **§NN-1 — Human-in-the-loop** | No agent may take irreversible real-world action without explicit human authorisation. | FR-RAG-LS-01 (RAG provides context + options; humans retain veto), FR-RAG-LS-03 (Quality Gates preserved), spec-024 PublicationService egress controls preserved unchanged. | **PASS** — spec changes the *grounding* of recommendations, not the *authority* to act. |
| **§NN-2 — Data Sovereignty (+ Foundry carve-out, Amendment 1.2.0)** | Every data-persisting service in AU; Foundry model-hosting endpoint may be non-AU only via registry. | FR-RAG-CV-01..04 (registry gate, CD enforcement, model-gateway data-minimisation, no non-AU data plane), FR-RAG-FM-05 (AAD scope `https://cognitiveservices.azure.com/.default`; no `api_key=`), FR-RAG-IDX-06 (AI Search Private-Endpoint-only AU East, no cross-region replication). Schema enforcement at `infra/parameters/foundry-carveout.schema.json` (`data_minimisation_required: const true`, `classification_filter_required: const true`, `approver_identities` minItems: 2). | **PASS** — registry pre-existed (spec 032); spec 036 only populates and tightens. |
| **§NN-3 — Privacy by design** | Australian Privacy Act 1988 + state/territory legislation. | FR-RAG-CV-03 (PII redaction + PSPF detection at the model gateway; deny + audit on filter failure), audit log records `gateway_decision`. | **PASS** — model gateway pattern reused from spec 032 / spec 029. |
| **§NN-4 — Interoperability** | CAP, EDXL, GeoJSON, OpenAPI standards-based APIs. | Citation envelope (Citation entity) carries `{jurisdiction, topic, page, source_url, sha256_of_chunk}`; OpenAPI for `/v1/retrieve` (see [`contracts/retrieval-service.md`](./contracts/retrieval-service.md)). | **PASS** — citation schema is JSON, retrieval contract is OpenAPI. |
| **§NN-5 — Graceful degradation** | Continue at reduced capability if any single agent/service/region unavailable. | FR-RAG-LS-02 (offline corpus cache, 14d TTL, dual-signed), spec-014 fallback chain intact (FR-RAG-FM-06), edge-case bullets (Foundry quota → carve-out routing with data-minimisation; AI Search 503 → offline cache; cache stale → "cache stale" badge; agent without LLM endpoint → fail-closed per spec 014/033). | **PASS** — offline cache + template fallback + circuit-breaker reuse from spec 029/032. |
| **§Quality Gates** | Lint + unit + integration before merge; What-If for infra; human review of public outputs; lessons capture. | FR-RAG-NS-08 (RAG-OPTOUT lint), FR-RAG-FM-04 (no-OpenAI lint), `bicep what-if` already gated in `.github/workflows/ci.yml`, FR-RAG-LS-03 (human approval preserved), spec-029/032/033 lessons hooks reused. | **PASS** — additive lint steps only. |

**Pre-Phase-0 verdict**: PASS. **Post-Phase-1 re-check**: PASS (no design choice in [`research.md`](./research.md) or [`contracts/`](./contracts/) introduces a new constitutional risk; the blue-green index pattern, the constructor-injected seam, and the carve-out-registry tightening all extend pre-existing patterns). The §Complexity Tracking table is intentionally empty.

---

## Project Structure

### Documentation (this feature)

```text
specs/036-foundry-rag-grounding/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output — research / decision log
├── data-model.md        # Phase 1 output — corpus index, citation envelope, audit shape, registry, opt-out
├── quickstart.md        # Phase 1 output — local-dev wiring + azd up
├── contracts/           # Phase 1 output
│   ├── retrieval-service.md       # FR-RAG-AG-01 RetrievalService port + OpenAPI
│   ├── foundry-chat-client.md     # FR-RAG-FM-07 constructor-injectable seam (Python protocol)
│   ├── ingest-pipeline.md         # FR-RAG-IDX-01..05 idempotent ingest contract
│   ├── citation-envelope.json     # FR-RAG-AG-03 + FR-RAG-SIM-02 wire format
│   ├── audit-record-llm-call.json # FR-RAG-AG-02 + FR-RAG-NS-* audit shape
│   └── offline-cache-manifest.json # FR-RAG-LS-02 dual-signed manifest shape
├── checklists/          # (pre-existing) requirements.md, migration.md, compliance.md
└── tasks.md             # Phase 2 output (/speckit.tasks command — NOT created by /speckit.plan)
```

### Source Code (repository root)

This feature **extends** the existing tree; only the entries marked `[NEW]` are introduced. All others are touched in-place. **No new top-level directories** outside the existing `apps/`, `packages/`, `infra/`, `scripts/`, `tests/`, `docs/decisions/`.

```text
apps/
├── agents/
│   ├── common/
│   │   ├── llm_client.py              # MIGRATE FR-RAG-FM-01: AzureOpenAI → Azure AI Inference; add chat_complete seam
│   │   ├── llm_config.py              # EXTEND: add AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_PROJECT_DEPLOYMENTS
│   │   ├── retrieval_client.py        # [NEW] FR-RAG-AG-01 shared RetrievalService client (jurisdiction union, top-k, hybrid)
│   │   ├── citation_filter.py         # [NEW] FR-RAG-AG-05 hallucinated-citation suppression
│   │   ├── offline_cache.py           # [NEW] FR-RAG-LS-02 dual-signature load + stale-age telemetry
│   │   └── audit.py                   # EXTEND: retrieved_chunks[], corpus_build_sha, embedding_model_id, rag_used/_reason
│   └── maf_runtime/
│       ├── chat_client.py             # MIGRATE FR-RAG-FM-02: factory rewires to Foundry; preserve OpenAIChatClient signature
│       └── agents/_factory.py         # WIRE: inject retrieval_client + chat_complete seam into Agent constructors
├── api/
│   └── app/services/simulation/
│       ├── controller_service.py      # MIGRATE FR-RAG-FM-03: AsyncAzureOpenAI → Foundry async; emit `citation` SSE events
│       ├── controller_prompt.md       # UNCHANGED (OOS-6)
│       └── citation_sse.py            # [NEW] FR-RAG-SIM-02 SSE event marshalling
├── eval-runner/
│   └── src/ama_eval/foundry_client.py # REFERENCE — pattern source for the seam; not modified
├── ingestion/                         # UNCHANGED — existing ingestion (BoM XML, simulation, etc.) is for live signals
└── ingest-runner/                     # [NEW] Container Apps Job for corpus ingest (FR-RAG-IDX-01..05)
    ├── pyproject.toml
    ├── src/ama_ingest/
    │   ├── __main__.py                # `python -m ama_ingest` entrypoint (azd postprovision + GitHub Actions)
    │   ├── chunker.py                 # H2 page-boundary + 1024-token cap + 10% overlap (research.md decision R-04)
    │   ├── embedder.py                # text-embedding-3-large @ 3072 dims via Foundry (Azure AI Inference)
    │   ├── indexer.py                 # blue-green write to corpus-v{N+1}; alias flip helper
    │   ├── licence_filter.py          # full-text | metadata-only | excluded gating per source.json (FR-RAG-IDX-02)
    │   ├── manifest.py                # corpus_build_sha + signature emission (cosign + age)
    │   ├── parity_gate.py             # alias-flip pre-flight: ingest-count match + sampling parity + retrieval-quality delta < 5%
    │   └── offline_bundle.py          # FR-RAG-LS-02 ≤500 MB cache bundle + dual signature
    └── tests/
        ├── unit/                      # licence_filter, chunker, parity_gate
        └── integration/               # against staging AI Search

infra/
├── main.bicep                         # WIRE: new ai-search-blue-green helper output; pass embeddingDeploymentName
├── modules/
│   ├── ai-search.bicep                # EXTEND: parameters for jurisdictionValues, vectorDimensions, capacity alert
│   ├── ai-search-blue-green.bicep     # [NEW] alias create / swap / rollback (wraps the existing module)
│   └── azure-openai.bicep             # KEEP for legacy fallback during canary; tagged for deprecation in final FM-04 PR
├── bicep/modules/eval/
│   └── foundry-deployments.bicep      # REUSE — referenced by both eval-runner and the new prod Foundry deployments
├── parameters/
│   ├── foundry-carveout.yaml          # POPULATE FR-RAG-CV-01: prod inference deployments + non-AU exceptions
│   └── foundry-carveout.schema.json   # UNCHANGED (spec 032 schema)
└── policy/rego/
    └── foundry_carveout.rego          # [NEW] OPA policy referenced by carveout YAML header (currently missing on disk per scan)

scripts/
├── verify-carveout.ps1                # EXTEND FR-RAG-CV-02: also fail on review_date expiry + missing approver IDs
├── seed_ingest.py                     # [NEW] azd postprovision hook — invokes ingest-runner job; sets CORPUS_BUILD_SHA on revisions
└── disaster_corpus/                   # UNCHANGED (OOS-3)

packages/
├── domain/                            # EXTEND: Citation, RetrievalRequest, RetrievalResult, AuditRecord pydantic models
├── schemas/                           # EXTEND: JSON-schema mirrors of citation-envelope + audit-record + offline-cache-manifest
└── ui/                                # EXTEND: <CitationCard /> + <DegradedModeBadge /> components (WCAG 2.2 AA)

tests/
├── contract/
│   ├── test_retrieval_service.py      # [NEW] FR-RAG-AG-01 contract
│   ├── test_foundry_chat_client.py    # [NEW] FR-RAG-FM-07 constructor seam
│   ├── test_citation_envelope.py      # [NEW] FR-RAG-AG-03 + FR-RAG-SIM-02 schema
│   ├── test_audit_record_shape.py     # [NEW] FR-RAG-AG-02 fields + opt-out shape
│   ├── test_rag_optout_lint.py        # [NEW] FR-RAG-NS-08/09 enforcement (`# RAG-OPTOUT [FR-RAG-NS-NN]` ↔ ADR file)
│   └── test_no_openai_imports.py      # [NEW] FR-RAG-FM-04 lint (binding atomically with legacy-client deletion PR)
├── integration/
│   ├── test_blue_green_alias_flip.py  # [NEW] FR-RAG-IDX-04 alias swap + 7-day rollback retention
│   ├── test_idempotent_ingest.py      # [NEW] FR-RAG-IDX-04 unchanged corpus → 0 re-embed
│   ├── test_offline_cache.py          # [NEW] FR-RAG-LS-02 dual-signature + 14-day TTL
│   ├── test_carveout_enforcement.py   # [NEW] FR-RAG-CV-01..04 CD gate
│   └── test_data_minimisation_gateway.py # [NEW] FR-RAG-CV-03 PII / PSPF deny + audit
├── e2e/
│   ├── citation_rendering.spec.ts     # [NEW] Playwright — Risk Manager + Simulation citation cards
│   └── degraded_mode_badge.spec.ts    # [NEW] Playwright — stale corpus + offline cache UI states
└── eval/                              # REUSE eval-runner — extend golden Q&A with per-agent fixtures (spec 032 pattern)

docs/
├── corpus/                            # UNCHANGED (OOS-3, OOS-4)
├── corpus/INDEXING-LICENCE-INVENTORY.md  # [NEW] FR-RAG-IDX-07 machine-checked inventory
└── decisions/036-foundry-rag-grounding/  # [NEW] 9 ADRs for FR-RAG-NS-01..09 carve-outs
    ├── 01-rag-optout-dependency-notifier.md
    ├── 02-rag-optout-bom-live.md
    ├── 03-rag-optout-ga-live.md
    ├── 04-rag-optout-planning-collection.md
    ├── 05-rag-optout-logistics-transactional.md
    ├── 06-rag-optout-scenario-execution.md
    ├── 07-rag-optout-classified.md
    ├── 08-rag-optout-ci-lint.md       # ADR for the CI-lint mechanism itself (FR-RAG-NS-08)
    └── 09-rag-optout-observer-auditor.md

.github/
├── workflows/
│   ├── ci.yml                         # EXTEND: ruff (existing), no-openai-imports, RAG-OPTOUT lint, bicep what-if, carveout review_date check
│   ├── cd.yml                         # EXTEND: scripts/verify-carveout.ps1 ALWAYS runs before plan apply; fail on AU-residency violation
│   ├── corpus-ingest.yml              # [NEW] triggered by docs/corpus/** push → invokes apps/ingest-runner job → emits corpus_build_sha artefact
│   └── foundry-carveout-review.yml    # EXISTING — extended with review_date alerting at T-30 / T-7 / T-0
└── agents/copilot-instructions.md     # UPDATED by `update-agent-context.ps1 -AgentType copilot` (spec 036 entry appended)
```

**Structure Decision**: Multi-app monorepo, single new Container Apps Job (`apps/ingest-runner`). The ingest pipeline is a **new app** (not a script under `scripts/`) because it (a) runs on a schedule + on `azd postprovision` + on `docs/corpus/**` push, (b) needs Foundry workload identity for embedding calls, (c) needs the same `azure-search-documents` and `azure-ai-inference` deps as `apps/agents`, and (d) emits an audit event to Service Bus on completion — all of which are Container-Apps-Job-shaped, not one-shot-script-shaped. **No** new shared packages under `packages/` — Citation / RetrievalRequest / AuditRecord live in the existing `packages/domain` pydantic-v2 layer (extended additively). Reuse vs new is recorded in [`research.md` R-08](./research.md).

---

## Goals & Milestones

| # | Goal | Acceptance | Anchored by |
|---|---|---|---|
| **G1** | Foundry inference plane replaces Azure OpenAI at all three call sites with managed identity, no API keys, and a constructor-injectable seam. | `grep -r "from openai" apps/` → 0 in production paths after final agent flip; `tests/contract/test_no_openai_imports.py` passes; FR-023 equivalence ≥ 95% per agent. | FR-RAG-FM-01..07, SC-002 |
| **G2** | Carve-out registry binds CD: every Foundry deployment present, approvers signed, `review_date` ≤ 12 months out; no production data plane outside AU. | `scripts/verify-carveout.ps1` blocks plan apply on violation; `tests/integration/test_carveout_enforcement.py` proves CD failure on synthetic gap. | FR-RAG-CV-01..04, SC-003, SC-004 |
| **G3** | Whole `docs/corpus/` indexed with licence-mode honoured; ingest idempotent; embedding-model rebuild blue-green with parity gate. | First ingest publishes `corpus-v1`; re-run yields 0 re-embed (SC-005); model swap rebuilds `corpus-v2` and flips alias < 60s; old retained 7d. | FR-RAG-IDX-01..08, SC-005, SC-006 |
| **G4** | Five decision agents + Simulation chat retrieve before every prompt-bearing call, attach citations, and audit full provenance; no fabricated citations. | 100% recommendation citation on grounded paths (SC-001); 0 hallucinated citations across 200-prompt jailbreak suite (SC-007); audit byte-replay ≥ 95% (SC-011); SSE `citation` events present for grounded sim turns. | FR-RAG-AG-01..06, FR-RAG-SIM-01..06, SC-001, SC-007, SC-011 |
| **G5** | Nine RAG-OPTOUT carve-outs documented + lint-enforced; degraded-mode + offline-cache work for Field Coordinator-aligned paths. | All nine ADRs landed; lint blocks new opt-outs without ADR (SC-008); offline answers fully cached + reconciled within 60s on reconnect (SC-009); jurisdiction disambiguation passes 50-query test set (SC-010). | FR-RAG-NS-01..09, FR-RAG-LS-02, FR-RAG-AG-04, SC-008, SC-009, SC-010 |
| **G6** | Per-agent canary cutover behind spec-029 flag with spec-033 FR-023 gate; spec-014 `_generate_with_fallback` chain intact across the migration window; FR-RAG-FM-04 lint binds atomically with legacy-client deletion. | All six agents flip without silencing; rollback playbook executed at least once in staging game-day. | FR-RAG-FM-06, Constitution §I |

### Milestones (sequenced, not concurrent — see Phasing)

- **M1 (Sprint 1–2)**: Foundry seam + RetrievalService port + carve-out CD enforcement. *G1 partial, G2 complete.*
- **M2 (Sprint 2–3)**: Ingest-runner job, blue-green alias, `corpus-v1` first publish, INDEXING-LICENCE-INVENTORY.md. *G3 complete.*
- **M3 (Sprint 3–4)**: Per-agent canary flips for Monitoring → Risk Assessment → Evacuation → Resource Allocation → Communication; Simulation chat grounding + SSE; RAG-OPTOUT lint. *G1 complete, G4 partial, G5 partial.*
- **M4 (Sprint 4–5)**: Field Coordinator offline cache, jurisdiction disambiguation suite, hallucinated-citation suppression hardening, all nine ADRs landed. *G4 complete, G5 complete.*
- **M5 (Sprint 5)**: Final Foundry agent flips, legacy `azure-openai.bicep` removal PR + `tests/contract/test_no_openai_imports.py` binding, monthly chaos game-day cadence live. *G6 complete.*

---

## Phasing

Phasing maps the seven FR families against the six goals and the persona-memo "top 10" task scaffolds.

### Phase A — Foundry seam + carve-out enforcement (M1)
*Anchored by Architecture-memo top-1, Delivery-memo top-1/2/3/6, Quality-memo top-7/8.*

1. **A1 — `LLMClient` migration with seam (FR-RAG-FM-01, -05, -07)**: Replace `openai.AzureOpenAI` import in `apps/agents/common/llm_client.py` with `azure.ai.inference.ChatCompletionsClient`. Constructor accepts `chat_complete: Callable[..., FoundryResponse] | None = None`. Default constructs the live client using `DefaultAzureCredential` + scope `https://cognitiveservices.azure.com/.default`. Unit tests inject `FakeFoundryClient` (see [`contracts/foundry-chat-client.md`](./contracts/foundry-chat-client.md)). **Spec-014 `_generate_with_fallback` chain preserved** (FR-RAG-FM-06).
2. **A2 — MAF chat-client factory rewire (FR-RAG-FM-02)**: `apps/agents/maf_runtime/chat_client.py` keeps the `build_azure_openai_chat_client` signature (no caller changes) but builds the Foundry-backed client. Same seam.
3. **A3 — Simulation controller migration (FR-RAG-FM-03)**: Replace `from openai import AsyncAzureOpenAI` in `apps/api/app/services/simulation/controller_service.py` (line 368) with the Foundry async client. Inject the same seam. Preserve `controller_prompt.md` (OOS-6).
4. **A4 — Carve-out CD gate (FR-RAG-CV-01..04)**: Extend `scripts/verify-carveout.ps1` to (i) validate every `Microsoft.CognitiveServices/accounts/deployments@*` resource in the Bicep `what-if` plan against `infra/parameters/foundry-carveout.yaml`, (ii) fail on `review_date` ≤ today, (iii) fail on missing or placeholder `approver_identities`, (iv) fail on any non-AU data-plane resource (`azurermhost != australiaeast|australiasoutheast`). Wire into `.github/workflows/cd.yml`. Materialise the missing `infra/policy/rego/foundry_carveout.rego` file referenced by the YAML header.
5. **A5 — Model gateway data minimisation (FR-RAG-CV-03)**: PII redaction (`presidio-analyzer` already in repo per spec 030), PSPF-marking detection regex, sensitive-operational-content filter — gateway invoked before any non-AU Foundry call; deny → audit `gateway.deny.reason`. Wire into the seam.

### Phase B — Corpus ingest + blue-green index (M2)
*Anchored by Architecture-memo top-2/8, Delivery-memo top-4/5/8, Quality-memo top-2/10.*

6. **B1 — `apps/ingest-runner` Container Apps Job (FR-RAG-IDX-01, -05)**: New `pyproject.toml`, `src/ama_ingest/` modules per Project Structure, Dockerfile, Bicep wiring as a Container Apps Job. Invoked by `azd postprovision` + by GitHub Actions `corpus-ingest.yml` on `docs/corpus/**` push.
7. **B2 — Chunking + embedding (FR-RAG-IDX-02)**: H2 page-boundary split + 1024-token cap + 10% sliding overlap (decision [R-04](./research.md)). Embed via Foundry-hosted `text-embedding-3-large` @ 3072 dims (FR-RAG-IDX-02). Skip-on-SHA-match for idempotency.
8. **B3 — Licence-mode filter (FR-RAG-IDX-02)**: `full-text` → body+embed; `metadata-only` → title+URL+summary, no body, no body embeddings; `excluded` → no doc emitted; deploy-time warning if any agent prompt template references an `excluded` source.
9. **B4 — Single index with jurisdiction/topic/licence_mode filters (FR-RAG-IDX-08)**: Single `corpus-v{N}` index; `jurisdiction` value-list `{act,nsw,nt,qld,sa,tas,vic,wa,national,aidr}`; jurisdiction-scoped retrieval unions `own + national + aidr` (FR-RAG-AG-04, US7). Capacity alert at 70% (FR-RAG-IDX-08).
10. **B5 — Blue-green alias + parity gate (FR-RAG-IDX-04)**: New Bicep helper `infra/modules/ai-search-blue-green.bicep` wraps the existing module. Embedding-model swap → fresh `corpus-v{N+1}` build; alias flip after parity gate (decision [R-05](./research.md): ingest-count match + 100-chunk sampling parity ≥ 95% + retrieval-quality delta < 5%); previous index retained 7 days; alias flip < 60s; cold rebuild ≤ 24h.
11. **B6 — INDEXING-LICENCE-INVENTORY.md (FR-RAG-IDX-07)**: Machine-checked inventory file mirrors spec 032's AIDR LICENCE-INVENTORY.md pattern; CI fails if any `source.json` carries a licence not in the inventory.

### Phase C — Shared retrieval + per-agent grounding + simulation grounding (M3)
*Anchored by Architecture-memo top-3/4/5/9, Delivery-memo top-2/3/9, Quality-memo top-1/5/6.*

12. **C1 — `RetrievalService` shared client (FR-RAG-AG-01)**: `apps/agents/common/retrieval_client.py` exposes `retrieve(request: RetrievalRequest) -> RetrievalResult`. See [`contracts/retrieval-service.md`](./contracts/retrieval-service.md). Hybrid search (BM25 + vector) with RRF (decision [R-06](./research.md), default vector 0.7 / lexical 0.3). Top-k default 5 (configurable per agent). Per-agent quota governance (decision [R-09](./research.md)).
13. **C2 — Audit-record extension (FR-RAG-AG-02)**: Extend `audit_records` Cosmos container with `retrieved_chunks[]`, `corpus_build_sha`, `embedding_model_id`, `prompt_sha`, `model_id`, `model_version`, `deployment_alias`, `rag_used`, `rag_optout_reason`, `gateway_decision`, `hallucinated_citation_count`. See [`data-model.md`](./data-model.md) §AuditRecord. Append-only Blob archive (existing 7-year immutability policy from spec 030 reused).
14. **C3 — Citation envelope on every recommendation (FR-RAG-AG-03)**: Citation pydantic model + JSON schema ([`contracts/citation-envelope.json`](./contracts/citation-envelope.json)); rendered into recommendation cards by `<CitationCard />` (`packages/ui/`); links to rendered Markdown page + original PDF URL.
15. **C4 — Jurisdiction disambiguation (FR-RAG-AG-04, US7)**: Retrieval contract enforces own-jurisdiction ∪ national ∪ aidr; retrieval payload always carries `jurisdiction` so FRNSW/RFS, SES NSW/VIC/QLD/NTES, DFES-WA-as-single-agency are never silently conflated. Curated 50-query test set (SC-010) under `tests/integration/test_jurisdiction_disambiguation.py` (recommended in tasks).
16. **C5 — Hallucinated-citation suppression (FR-RAG-AG-05)**: `apps/agents/common/citation_filter.py` validates every emitted citation against the live `retrieved_chunks[]` set; mismatched citation → suppress in card, log `hallucinated_citation` event, downgrade confidence above configurable threshold (planning default 1; revisited per agent in tasks — decision [R-10](./research.md)).
17. **C6 — Communication-agent ATSI/CALD/Auslan retrieval (FR-RAG-AG-06, US8)**: Retrieval surfaces ATSI / CALD / Auslan / Easy-Read / TIS-National corpus entries to Communication agent before warning composition; gates draft for human approval (FR-RAG-LS-01, FR-RAG-LS-03).
18. **C7 — Simulation chat grounding + SSE citation (FR-RAG-SIM-01..06)**: Simulation Controller invokes the same RetrievalService before each chat-turn inference; SSE stream emits `citation` events ([`contracts/citation-envelope.json`](./contracts/citation-envelope.json)); audit per FR-RAG-SIM-04 mirrors AG-02; scripted-scenario timeline path opts out (FR-RAG-NS-06).
19. **C8 — Per-agent canary flips (FR-RAG-FM-06)**: Spec-029 feature flag `foundry_rag_enabled_agents` flips per-agent in order Monitoring → Risk Assessment → Evacuation → Resource Allocation → Communication (Simulation flips last). Each flip gated by spec-033 FR-023 equivalence (≥ 95% decision-equivalence + 100% schema-equivalence) on the per-agent golden Q&A. Spec-014 `_generate_with_fallback` chain intact throughout.

### Phase D — RAG-OPTOUT carve-outs + offline cache + multi-jurisdiction QA (M4)
*Anchored by Quality-memo top-3/4/9, Delivery-memo top-7, Architecture-memo top-4/5.*

20. **D1 — Nine RAG-OPTOUT ADRs (FR-RAG-NS-01..09)**: Author all nine `docs/decisions/036-foundry-rag-grounding/<NN>-rag-optout-*.md` files following the format named in [Project Structure](#project-structure). Each ADR cites the persona memo, names the approver, and points back to the FR.
21. **D2 — RAG-OPTOUT lint (FR-RAG-NS-08)**: `tests/contract/test_rag_optout_lint.py` walks every Python module under `apps/agents/` and `apps/api/app/services/`, finds `# RAG-OPTOUT [FR-RAG-NS-NN]` markers, asserts each marker has a matching ADR file, and asserts every non-grounded production call site carries the marker (pattern: any `chat_complete` / `LLMClient.generate_response` call NOT preceded by a retrieval call within the same function body needs the marker OR is whitelisted).
22. **D3 — Offline cache + dual signature (FR-RAG-LS-02)**: `apps/agents/common/offline_cache.py` builds and verifies a ≤500 MB per-device bundle; cosign keyless (Sigstore + GitHub OIDC) signs the manifest at build time per spec 032 FR-AI09; age-encrypted detached signature on the bundle for OIDC-less verification; 14-day TTL; audit-logged refresh on next online sync; queued offline audit entries reconciled within 60s with original timestamps preserved (SC-009).
23. **D4 — Stale-corpus + degraded-mode UI (FR-RAG-LS-02 + UX-memo top-6)**: `<DegradedModeBadge />` surfaces stale-cache age + offline-cache active + retrieval-unavailable banner; WCAG 2.2 AA conformance; jurisdiction labels expanded for screen readers (Accessibility memo).
24. **D5 — Multi-jurisdiction disambiguation suite (SC-010)**: Curated 50-query persona-driven test set covering NSW–VIC border (RFS vs CFA-VIC; FRNSW vs FRV), NT–QLD cyclone crossing (NTES vs SES-QLD), ACT–NSW handoff (ACT RFS vs NSW RFS, AFP-ACT vs NSW Police), DFES-WA single-agency boundary cases.

### Phase E — Final cutover + chaos game-day cadence (M5)
*Anchored by Quality-memo top-9/10, SRE-memo top-5, Delivery-memo top-10.*

25. **E1 — Final agent flip + atomic legacy-client deletion (FR-RAG-FM-04)**: PR that flips the last agent ALSO (a) deletes `apps/agents/common/llm_client.py` Azure-OpenAI import path, (b) introduces `tests/contract/test_no_openai_imports.py` as a binding lint, (c) removes `infra/modules/azure-openai.bicep` (or marks it `legacy/` per spec 032 deprecation pattern), (d) collapses `_generate_with_fallback` to its template-only branch (Foundry-side regression now downgrades to template, never to Azure-OpenAI). FR-RAG-FM-04 lint binds atomically per FR-RAG-FM-06.
26. **E2 — Monthly + quarterly + post-incident game-day cadence (Quality-memo top-9 / SRE-memo runbooks)**: Monthly: blue-green alias flip under load + offline cache fallback (Game-Day 1 + 2). Quarterly: multi-agent canary sequencing + cascading failure (Game-Day 3). Post-incident: replay within 48h. Playbook lives in `docs/runbooks/036-foundry-rag-gameday.md`.
27. **E3 — Eval harness extension (Quality-memo top-6 + Architecture-memo top-1)**: Reuse `apps/eval-runner/src/ama_eval/` to generate per-agent golden Q&A fixtures keyed by `(corpus_build_sha, embedding_model_id)`; canary gate query is `decision-equivalence ≥ 95% AND schema-equivalence == 100% AND citation-fidelity ≥ 0.7 AND verbatim-source-match` (extends spec-033 FR-023 with spec-036 citation checks per Quality-memo risk #2).

---

## Risk Register

Consolidated from the three persona memos' "top 5 risks" sections (15 raw entries → 13 deduplicated; embedding-version drift and per-agent canary sequencing each appeared in two memos and are merged with cross-memo mitigations). Severity uses Likelihood × Impact heat (L/M/H × L/M/H/Critical). Owner names the persona who carries the mitigation, not a real person — to be assigned in `tasks.md`.

| # | Risk | L × I | Mitigation | Anchored by | Owner |
|---|---|---|---|---|---|
| **R1** | **Embedding-model version drift across blue-green index** — mid-build mixed `embedding_model_id` chunks corrupt semantic ranking silently. | M × H | Schema enforces exactly-one `embedding_model_id` per index; ingest lint validates homogeneity; alias flip blocked unless parity gate passes (R-05); 7-day rollback retention (FR-RAG-IDX-04); SRE alert on `embedding_model_version_active` mismatch. | Arch-memo R1, Delivery-memo R1, Quality-memo R1 | AI/ML Engineer + Data Engineer |
| **R2** | **Foundry quota exhaustion in AU East during concurrent canary** — per-agent flips + spec-033 equivalence test + spec-029 FF can spike token/sec beyond AU quota and silence agents. | M × Critical | Sequenced per-agent rollout (one agent per sprint per Phase C8); explicit per-agent quota governance (R-09); spec-014 fallback chain intact across the window (FR-RAG-FM-06); circuit breaker on retrieval; carve-out registry permits non-AU inference under data-minimisation gateway (FR-RAG-CV-03); SRE runbook 1 (Foundry outage). | Arch-memo R1, Delivery-memo R2, SRE-memo Cap.Plan | Security Engineer + DevOps |
| **R3** | **Citation hallucination undetected by equivalence gate** — gate measures decision-equivalence but not citation fidelity; LLM cites a chunk not in `retrieved_chunks[]`. | M × Critical | Hallucinated-citation suppression filter at emission (FR-RAG-AG-05, Phase C5); audit `hallucinated_citation_count`; canary gate extended to citation-fidelity ≥ 0.7 + verbatim-source-match (Phase E3); Observer-Auditor spot-check; CI-lint forbids citation emission without backing chunk. | API-arch-memo R1, Delivery-memo R3, Quality-memo R2 | Principal Engineer + Software Developer |
| **R4** | **Offline-cache integrity failure** — tampered manifest passes single-signature; Field Coordinator acts on stale/corrupted doctrine. | L × H | Dual signature: cosign keyless (Sigstore + GitHub OIDC) at build + age-encrypted detached signature on bundle (FR-RAG-LS-02); cache load fails closed if either check fails; audit-logged refresh on next online sync; key rotation runbook (SRE memo runbook 5). | Delivery-memo R4 | Security Engineer |
| **R5** | **Agent silencing during cutover** — legacy Azure-OpenAI client deleted before equivalence gate passes on all agents → operator unaware. | M × Critical | spec-014 fallback chain intact across migration; spec-029 FF per-agent canary; spec-033 equivalence gate BLOCKS flip until ≥ 95%; FR-RAG-FM-04 lint binds atomically with legacy-client deletion (FR-RAG-FM-06, Phase E1); template-fallback path tested in chaos Game-Day 2. | Delivery-memo R5, Constitution §I | Software Developer + QA |
| **R6** | **Offline cache stale-age threshold under-defined** — ≤500 MB cap and 14-day TTL set, but no per-jurisdiction stale-age policy; Field Coordinator deploys outdated corpus during long deployment. | M × H | Threshold defined as 14 days hard TTL + 11-day "warning" badge in UI (decision [R-07](./research.md)); telemetry `offline_cache_ttl_days_remaining` gauge alerted at <3 days; pre-deploy 30-day extended TTL via feature-flag override for declared field deployments. | Quality-memo R3 | SRE + Field Coordinator persona owner |
| **R7** | **Alias flip cutover timeout under load** — < 60s SLA can race against in-flight queries → 504s. | M × M | Pre-cutover query drain (wait for in-flight) per SRE memo runbook 2; monitor alias switch latency; rollback if > 120s; client-side exponential backoff with jitter on retrieval transient 404 (Architecture-memo R3). | Quality-memo R4, Architecture-memo R3 | SRE + Data Engineer |
| **R8** | **Compliance audit-trail incompleteness** — bug in wrapped client / exception handling drops `rag_used` field. | M × M | Contract test for audit-log presence on every call (Phase D2); lint on Foundry call site verifies audit-logging wrapper applied; monthly KQL query counts missing entries by agent (Compliance memo); Application Insights `FoundryRAGAudit` custom table. | Quality-memo R5 | Compliance Auditor + SRE |
| **R9** | **Constructor-injected seam leakage into production** — fake callable left in production via merge error → fake citations. | L × Critical | Type-check seam (real callable type vs fake stub type via `Protocol`); ≥ 95% unit-test coverage on seam paths; CI lint forbids `FakeFoundryClient` import outside `tests/`. | Principal-eng-memo R1 | Principal Engineer + QA |
| **R10** | **Chunking strategy emergence** — page-aligned cells > 2000 tokens silently truncated by embedder → vector fidelity loss. | M × M | Decision [R-04](./research.md): H2 page-boundary + 1024-token cap + 10% overlap + atomic table/code-block preservation; ingest telemetry histogram of chunk size + truncation rate; alert on > 0.5% truncation. | Principal-eng-memo R2 | AI/ML Engineer |
| **R11** | **Backward-compatibility debt during the migration window** — two chat-loop implementations diverge silently. | M × M | Automated parity tests (same input → same output for both paths) on every PR while both clients live; bi-weekly review of FF status; final E1 PR atomically removes the legacy path. | Principal-eng-memo R3 | Software Developer |
| **R12** | **Carve-out registry drift** — `excluded`-licence-mode chunk leaks into query response despite filter. | L × H | Three-layer enforcement: ingest-time exclusion (FR-RAG-IDX-02), retrieval-time `licence_mode` filter, response-time citation-envelope validator; KQL audit `count where licence_mode not in (full,metadata,excluded)` monthly; SRE runbook 4 (registry drift). | Compliance memo §License-Mode | Compliance Auditor + Data Engineer |
| **R13** | **Citation rendering accessibility regression** — confidence badges low-contrast; collapsible panel missing ARIA → WCAG 2.2 AA failure. | M × M | Accessibility-tester memo contracts on `<CitationCard />` (Phase D4); mandatory accessibility audit pre-GA (WAVE + screen-reader); jurisdiction labels expanded for SR ("New South Wales" not "NSW") per Accessibility memo §51–54. | Architecture UX-memo R4, Accessibility memo §45–69 | Accessibility Tester + UX Designer |

**Risk-register count: 13.**

---

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified.**

The Constitution Check above is PASS at both the pre-Phase-0 and post-Phase-1 gates. **No complexity-tracking entries are required.** Every design choice in [`research.md`](./research.md) and [`contracts/`](./contracts/) is either (a) a direct extension of a pre-existing spec-032 / spec-024 / spec-029 / spec-033 pattern, or (b) the lighter-weight option among the alternatives evaluated (e.g., single index with filter fields, not per-jurisdiction proliferation; constructor-injectable seam, not SDK monkey-patching; new Container Apps **Job** for ingest, not a new Container Apps service or new top-level package).

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| *(none)* | — | — |

---

## Cross-references

- **Spec**: [`spec.md`](./spec.md) (68 FRs, 10 USs, 19 SCs, 8 OOS, 12 assumptions; Pass-1 + Pass-2 + R3 amend-loop Pass-1 + R3 amend-loop Pass-2 clarifications complete).
- **Checklists**: [`checklists/requirements.md`](./checklists/requirements.md), [`checklists/migration.md`](./checklists/migration.md), [`checklists/compliance.md`](./checklists/compliance.md).
- **Phase 0 research**: [`research.md`](./research.md).
- **Phase 1 design**: [`data-model.md`](./data-model.md), [`contracts/`](./contracts/), [`quickstart.md`](./quickstart.md).
- **Constitution**: [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) — Principle I, IV, V, VI-C, NN-1, NN-2 (Amendment 1.2.0), Quality Gates.
- **Predecessor specs**: [014 Azure OpenAI Integration](../014-azure-openai-integration/spec.md) (migrated), [024 Simulation Control & Chat Orchestration](../024-simulation-control-chat/spec.md) (extended), [029 Progressive Delivery Pipeline](../029-progressive-delivery-pipeline/spec.md) (FF mechanism reused), [030 LLM Eval Framework](../030-llm-eval-framework/spec.md) (eval-runner pattern referenced), [032 Rubric Improvements](../032-rubric-improvements/spec.md) (FR-AI03a registry + FR-AI06 PE + FR-AI09 cosign reused), [033 MAF Adoption](../033-maf-adoption/spec.md) (FR-023 equivalence + FR-012b cutover gate referenced).
- **Persona memos** (R2 technical, primary planning input): `personas-input/technical-architecture.md`, `personas-input/technical-delivery.md`, `personas-input/technical-quality.md`. R1 sector + operational memos consulted: `personas-input/operational.md`, `personas-input/sectors-{commonwealth,crosssector,eastern,southern-western,territories}.md`.
- **Existing infrastructure reused** (no replacement, only additive deltas): `infra/modules/ai-search.bicep`, `infra/bicep/modules/eval/foundry-deployments.bicep`, `infra/parameters/foundry-carveout.{yaml,schema.json}`, `apps/eval-runner/src/ama_eval/foundry_client.py`, `scripts/verify-carveout.ps1`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/foundry-carveout-review.yml`.

---

*End of original plan.md sections (Phases A–E + R1–R13). The R3 amend-loop appendix begins below.*

---

## Phase F — R3 Amend Loop Implementation (post-A–E)

> **Provenance**: Round 3 persona review (Sessions 3–5 in `spec.md`) surfaced 12 amendment clusters (A1–A12) addressing 34 of 89 individual findings raised by 85 personas across 9 R3 memos (`personas-input/r3-*.md`). The amend loop added **25 new FRs** (FR-RAG-CA-01..05, FR-RAG-COMP-01..04, FR-RAG-COORD-01..02, FR-RAG-TEST-01..04, FR-RAG-OBS-01..03, FR-RAG-UI-01, FR-RAG-IDX-04a/05a/09, FR-RAG-FRESH-01/02, FR-RAG-NS-09) and extended FR-RAG-AG-02/-04, FR-RAG-LS-02, FR-RAG-CV-01. Two clarify passes (Sessions 4 + 5) added 16 Q&A resolutions. Final spec counts: **68 FRs, 10 USs, 19 SCs, 8 OOS, 12 Assumptions, 5 Clarification sessions**. Phase F is the planning view of those amendments; it lands **after** the existing Phases A–E (i.e., relative to `tasks.md`, F-A* tasks come AFTER T142–T150, NOT before — see [§Updated phase ordering](#phase-f-ordering-vs-existing-tasks-t142-t150) below). It does not re-do prior work; it appends new sub-phases mapped to clusters A1–A12.

### F-A1 — Agency disambiguation (Cluster A1)
*Anchored by R3 sectors-eastern, southern-western, territories memos (multi-agency jurisdiction reality); Pass 1 Q-P1-02 tie-break order.*

- **F-A1.1** — Add chunk-metadata fields `agency` (e.g., `NSW-RFS`, `FRNSW`, `DFES-WA`, `SAMFS`) and `agency_role` (`urban-fire | rural-fire | ses | combined | police | ambulance | marine-rescue | national-security | other`) to the AI Search index; required on every `corpus-v{N+1}` document. Schema authority: `contracts/chunk-metadata.schema.json`.
- **F-A1.2** — Extend `apps/ingest-runner/src/ama_ingest/chunker.py` to emit `agency` + `agency_role` from `source.json` per-entry metadata; ingest-time lint fails the build if any chunk lacks both.
- **F-A1.3** — Wire FR-RAG-AG-04 disambiguation into `apps/agents/common/retrieval_client.py` so urban-fire and rural-fire queries within the same jurisdiction never collide.
- **F-A1.4** — Migration: blue-green rebuild ONLY (no in-place chunk mutation per Pass 2 Q-P2-01 + Assumption A10) — legacy `corpus-v{N}` is retained 7 days post-flip per FR-RAG-IDX-04 + ADR-16.
- **F-A1.5** — SC-013 acceptance: ≥95% on agency-disambiguation subset of `tests/fixtures/golden-set-v1.json` (entries tagged `agency_disambiguation`, ≥20 entries).

### F-A2 — Cultural Authority Registry & Gating (Cluster A2)
*Anchored by Constitution VI-C non-negotiable; ADR-12; sectors-territories memo Indigenous-liaison emphasis.*

- **F-A2.1** — Provision Cosmos DB container `culturalAuthorityRegistry` in Australia East (NN-2 + FR-RAG-CV-04) via `infra/modules/cosmos-cultural-authority.bicep` (NEW). Schema authority: `contracts/cultural-authority-registry.schema.json`.
- **F-A2.2** — Container is provisioned **empty**; population is HUMAN-IN-LOOP per FR-RAG-CA-05 (NEMA + AFAC + ≥3 Indigenous community representatives sign-off). SC-014 verifies sign-offs at CD time.
- **F-A2.3** — Implement `apps/agents/common/cultural_authority_registry.py` (NEW) — Cosmos client + signature verifier (cosign keyless OR age-encrypted detached, mirroring FR-RAG-LS-02 dual-sig pattern).
- **F-A2.4** — Implement the **post-retrieval, in-process gate** inside `apps/agents/common/retrieval_service.py` (the FR-RAG-AG-01 entry point, between AI Search round-trip and Foundry inference) per Pass 2 Q-P2-02. Gate suppresses Sacred Site / Indigenous protocol chunks unless operator consent is verified; emits `cultural_authority_registry_unavailable` audit event on registry-unreachable per Pass 1 Q-P1-01 (fail-closed for protected chunks; non-protected chunks remain retrievable so the agent does not silence — Constitution Principle I).
- **F-A2.5** — Add chunk fields `cultural_classification` (`public | indigenous-language | sacred-site | land-governance`) and `cultural_authority_required` (bool) — see `contracts/chunk-metadata.schema.json`.
- **F-A2.6** — Feature flag `feature.cultural_authority_gate.enabled` is **Locked-on in prod** (A12 class taxonomy) — disabling permitted only for `environment=test` chaos runs and OPA-blocked at flag-flip time per Constitution VI-C.
- **F-A2.7** — Corpus body authoring (Indigenous-language translations, Sacred Site protocols, ALT/APY consent gates) is **HUMAN-IN-LOOP** per FR-RAG-CA-01..03 + Assumption A9 + OOS-8; tracked in `tasks.md` but performed outside this AI workflow.

### F-A3 — Authority Precedence Ranking (Cluster A3)
*Anchored by ADR-13; sectors-territories memo (ACT national-institution precedence); sectors-commonwealth memo (COMDISPLAN activation); Pass 1 Q-P1-02 tie-break order.*

- **F-A3.1** — Add chunk fields `authority_level` (`state-territory | commonwealth | national-institution`) and `precedence_rank` (int 1=highest, 3=lowest) — schema in `contracts/chunk-metadata.schema.json`.
- **F-A3.2** — Extend `apps/agents/common/retrieval_client.py` ranking pass: when retrieval surfaces conflicting guidance from multiple authority levels (e.g., ACT ESA + Commonwealth NEMA), the recommendation card MUST present both with precedence indicators and a conflict-resolution note directing operators to escalate to IC + NEMA liaison (FR-RAG-AC-01).
- **F-A3.3** — Implement deterministic tie-break order per Pass 1 Q-P1-02 — sequence: (1) recency (`corpus_build_sha.generated_at`), (2) `licence_mode` (`full-text` > `metadata-only`), (3) `embedding_model_id` lexicographic, (4) `chunk_id` lexicographic. Trace recorded as `precedence_tiebreak_applied[]` in audit.
- **F-A3.4** — Wire FR-RAG-COMP-04 COMDISPLAN activation: when `national_emergency_active` flag is set, retrieval ranking elevates `authority_level=commonwealth` chunks to `precedence_rank=1` for the duration of the activation.
- **F-A3.5** — Feature flag `feature.authority_precedence_ranking.enabled` (Reversible class) — disable falls back to recency-only ranking; emits `authority_precedence_ranking_disabled` audit event.
- **F-A3.6** — SC-015 acceptance: Commonwealth doctrine first in ≥95% of national-institution queries (Parliament House, Defence estates, embassies) when `jurisdiction == act`.

### F-A4 — OPA Carve-Out Bug Fix (Cluster A4)
*Anchored by R3 architecture memo F-ARCH-05 BLOCKER finding; Pass 2 Q-P2-03 sequencing.*

- **F-A4.1** — **PLAN-ONLY DELIVERABLE** (per user's "NOT to implement here" directive): document the rego change at `infra/policy/rego/foundry_carveout.rego`. The rule at line 29 currently reads `count(deployment.approver_identities) < 2 ...` which is correct for dev/staging but violates FR-RAG-CV-01 prod 3-approver requirement. Plan: introduce an `input.environment` discriminator so:
  - `environment == "prod"` → `count(deployment.approver_identities) < 3` is a deny
  - `environment in {"dev", "staging"}` → `< 2` is a deny (existing behaviour preserved)
- **F-A4.2** — Sequencing per Pass 2 Q-P2-03: rego tightening MUST be coupled with the amend-loop merge in the **same PR** (no bifurcated rollout window — splitting it across two PRs would create a window where prod could deploy a 2-approver carve-out, the very gap FR-RAG-CV-01 closes).
- **F-A4.3** — Contract test at `tests/contract/test_foundry_carveout.py` (NEW, sibling of existing `tests/contract/test_carveout_registry_entry.py`):
  - 2-approver dev payload → empty `deny_foundry_carveout` set, exit 0.
  - 2-approver prod payload → non-empty deny set, exit 1.
  - 3-approver prod payload → empty deny set, exit 0.
- **F-A4.4** — Spec-036 amend-loop schema mirror at `contracts/foundry-cv.schema.json` documents the registry-root `min_approvers_prod` (default 3) + `min_approvers_dev` (default 2) and per-row `environment` enum, kept in sync with `infra/parameters/foundry-carveout.schema.json`.
- **F-A4.5** — SC-016 acceptance covers all three contract-test cases.

### F-A5 — Audit Schema Extension & Field-Coordinator Offline Boundaries (Cluster A5)
*Anchored by ADR-14; Constitution Principle IV; FR-RAG-LS-02 offline autonomy.*

- **F-A5.1** — Extend Cosmos DB `audit_records` container schema (additive, nullable per Pass 2 Q-P2-01 + A10) with: `operator_override_rationale`, `approval_workflow_state` (enum `pending|approved|rejected`), `approval_authority`, `downgrade_justification`, `retrieval_index_name`, `field_coordinator_offline_decision`, `conflict_group_id`, `precedence_tiebreak_applied[]`. Schema authority: `contracts/audit-record-llm-call.json` (extended in this amend-loop).
- **F-A5.2** — Migration runs via the **existing** `infra/scripts/migrate-audit-record-036.ps1` script (Phase D2 task **T082**, "additive fields only; preserve existing rows"); no migration window required because Cosmos tolerates missing fields on legacy rows. The script gains a Phase F entry point that adds the 8 new fields.
- **F-A5.3** — Wire `apps/agents/common/audit.py` to emit the new fields on every applicable record: `operator_override_rationale` whenever an operator modifies/rejects a recommendation; `approval_workflow_state` on every public-warning event; `retrieval_index_name` on every `rag_used == true` record (concrete AI-Search index name, NOT the alias — per ADR-16); `field_coordinator_offline_decision` on Field-Coordinator offline path.
- **F-A5.4** — Extend FR-RAG-LS-02 Field-Coordinator offline boundaries: MAY make resource-allocation, safety-escalation, and evacuation-centre setup decisions offline using cached doctrine; MUST NOT issue public warnings, request mutual aid across jurisdictions, or escalate to state/national level offline (requires IC approval on reconnect). On reconnect, queued decisions audit-emit `approval_workflow_state: "pending"` and are flagged for IC review before they become operational.
- **F-A5.5** — SC-017 acceptance: `operator_override_rationale` present in 100% of override events; `approval_workflow_state` present in 100% of public-warning events.

### F-A6 — Federal Compliance (Cluster A6)
*Anchored by ADR-15; sectors-commonwealth memo NEMA / AGD / AFP federal alignment; OOS-8 / Assumption A9 HUMAN-IN-LOOP gates.*

- **F-A6.1** — Author `docs/compliance/ISM-2024-mapping.md` (NEW) referencing ISM-0468 (TLS 1.2+ for Foundry + AI Search), ISM-1552 (audit-log cryptographic integrity via cosign + detached sigs).
- **F-A6.2** — Implement Privacy Act 1988 APP 1/3/5/6/11 surfaces: SAR (Subject Access Request) workflow at `GET /api/audit/sar?subject=...`; PII anonymisation hook in `apps/agents/common/audit.py` before write; existing 7-year retention from spec 030 reused.
- **F-A6.3** — Implement PSPF audit export: `GET /api/audit/export?format=pspf&start=...&end=...` returns CSV with mandated columns: `Timestamp, User, Action, Resource, Outcome, Justification`. The existing audit shape (post-F-A5 extensions) covers every column without further schema change.
- **F-A6.4** — Wire FR-RAG-COMP-04 COMDISPLAN ranking interlock (already covered by F-A3.4).
- **F-A6.5** — **HUMAN-IN-LOOP gates** per Assumption A9: the codebase scaffolds the implementation but federal sign-off (NEMA, AGD, AFP, AIATSIS) is performed outside this AI workflow. Tasks for sign-off acquisition are tracked in `tasks.md` but their completion is external.
- **F-A6.6** — SC-018 acceptance: `docs/compliance/ISM-2024-mapping.md` exists, references the two ISM controls, and the PSPF export endpoint returns valid PSPF-format CSV.

### F-A7 — Blue-Green Audit Replay Consistency (Cluster A7)
*Anchored by ADR-16; R3 architecture memo F-ARCH-02 + F-ARCH-03 findings; Pass 1 Q-P1-04 rollback SLO timer; spec 029 FR-008 5-min pattern.*

- **F-A7.1** — Implement FR-RAG-IDX-04a in-flight atomicity: `apps/agents/common/retrieval_client.py` resolves the alias `corpus-search` to a concrete index name at query start (e.g. `corpus-v3`) and pins that name for the entire query lifecycle. SSE multi-turn sessions pin once at session start; no alias re-resolution mid-query.
- **F-A7.2** — Wire `retrieval_index_name` into every `RetrievalResult` and propagate to `AuditRecord.retrieval_index_name` (covered by F-A5.3 audit-emission wiring).
- **F-A7.3** — Implement FR-RAG-IDX-09 5-minute rollback SLO: timer starts at emission of the `index_rollback` Service Bus event (parity-gate failure detection). "Rollback complete" = (a) alias resolves to old index for all new queries after the SLO deadline, AND (b) rollback record `{old_index_name, new_index_name, parity_gate_failure_reason, release_manager_id, completed_at}` appended to audit store.
- **F-A7.4** — Rollback is **manual** (Release Manager approval required) per Pass 2 Q-P2-08 Manual operator action class; on-call paged via existing alert pipeline.
- **F-A7.5** — Previous index retained 7 days post-flip per FR-RAG-IDX-04 (Bicep TTL tag; enforced by `infra/scripts/cleanup-stale-indices.ps1`).
- **F-A7.6** — SC-019 acceptance: concurrent retrieval queries spanning blue-green flip return consistent index name in audit log; rollback completes ≤5 min.

### F-A8 — Corpus Freshness (Cluster A8)
*Anchored by ADR-17; R3 quality memo F-SRE-01 finding; Pass 1 Q-P1-05 alert scope.*

- **F-A8.1** — Implement FR-RAG-IDX-05a nightly drift-detection schedule: `.github/workflows/corpus-ingest.yml` cron at `"0 14 * * *"` UTC (= 0100 AEST / 0000 AEDT). On run: pipeline checks every `source.json.sha256` for drift; if drift → re-run ingest + alias flip per ADR-16; if no drift → log `no_drift_detected` and exit cheaply.
- **F-A8.2** — Implement FR-RAG-FRESH-01 UI freshness indicator in `<CitationCard />` and the Simulation chat surface: "Corpus last updated: <timestamp>" derived from `corpus_build_sha` manifest `generated_at`. Yellow if age >7 days; red if >14 days.
- **F-A8.3** — Implement FR-RAG-FRESH-02 staleness alert at the **global corpus index** scope (Pass 1 Q-P1-05; NOT per-jurisdiction): emit `corpus_stale` to on-call + Service Bus when `corpus_build_sha.generated_at` age >14 days AND no ingest in last 48h. Schema authority: `contracts/staleness_alert.schema.json`.
- **F-A8.4** — Feature flag `feature.corpus_freshness_alert.enabled` (Reversible class) — disable suppresses the alert but records underlying state in audit log.
- **F-A8.5** — Author runbook `docs/runbooks/036-foundry-rag-corpus-stale.md` covering the four common stale causes (corpus repo stalled / ingest pipeline failing / cron misconfigured / parity gate blocking).

### F-A9 — Multi-Agent Conflict Detection (Cluster A9)
*Anchored by ADR-18; Pass 1 Q-P1-03 escalation chain; Pass 2 Q-P2-06 detection mechanics.*

- **F-A9.1** — Provision Cosmos DB container `conflictDetectionLog` in Australia East (NN-2 + FR-RAG-CV-04) via `infra/modules/cosmos-conflict-detection.bicep` (NEW). Schema authority: `contracts/conflict_detection.schema.json`.
- **F-A9.2** — Implement `apps/api/app/services/conflict_detection.py` (NEW) — reactive, post-return, deterministic, rule-based detector running in the recommendation-aggregation layer (NOT inside any individual agent and NOT in real-time streaming, per Pass 2 Q-P2-06). Compares each pair of agent recommendations after both return; pre-emptive divergence detection rejected because it breaks Constitution Principle IV deterministic replay + spec 033 MAF agent-isolation model.
- **F-A9.3** — Implement four conflict classes per ADR-18: **resource** (same `resource_id`, overlapping `(start_time, end_time)`); **spatial** (incompatible recs over overlapping `(geo_bbox, time_window)`); **temporal** (action verbs with mutually exclusive deadlines); **severity** (hazard severity buckets with delta ≥1 AIIMS incident level for the same hazard).
- **F-A9.4** — Wire `conflict_group_id` into AuditRecord (covered by F-A5.1) so trace stitching works without a JOIN.
- **F-A9.5** — Implement AIIMS escalation chain per Pass 1 Q-P1-03: (1) `conflict_detected` event routes first to Ops Officer; (2) 5-min unack timeout → IC; (3) full-AIIMS-unreachable + degraded-connectivity → Field Coordinator queues for IC review on reconnect (Field Coordinator MUST NOT auto-resolve cross-agent conflicts).
- **F-A9.6** — Feature flag `feature.multi_agent_conflict_detection.enabled` (Reversible class) — disable reverts to single-agent behaviour; emits `multi_agent_coordination_disabled` audit event.

### F-A10 — Test Coverage Expansion (Cluster A10)
*Anchored by ADR-19; R3 delivery memo F-DEL-01/F-DEL-08 Windows findings; quality memo F-PERF-02/F-TEST-01 load + cold-start findings; Pass 1 Q-P1-07/-08 + Pass 2 Q-P2-04 fixture canonicalisation.*

- **F-A10.1 — Windows compat (FR-RAG-TEST-01)** — Add Windows runner job to `.github/workflows/ci.yml` mirroring the existing Linux job (per-PR trigger). Add shared `clean_tmp_path` fixture to `tests/conftest.py` (closes F-DEL-01: `gc.collect()` + `time.sleep(0.05)` + retry). Force `PYTHONIOENCODING=utf-8` via env-var (closes F-DEL-08). No new fixture directory; cases live alongside Linux counterparts under `tests/contract/`, `tests/integration/`, `apps/agents/tests/` gated by `@pytest.mark.skipif(sys.platform != "win32")`.
- **F-A10.2 — 50-agent load (FR-RAG-TEST-02)** — Add `RetrievalSession` Locust task class to existing `tests/load/locustfile.py`; harness MUST exercise 50 distinct `agent_session_id` values (per Pass 1 Q-P1-07) sustained at RPS=50 for 60s with p95 retrieval latency ≤500ms. Triggers: scheduled weekly CI + pre-promotion stage of spec-029 progressive-delivery (NOT per-PR — too long). SHOULD-class quality gate.
- **F-A10.3 — Golden set consolidation (FR-RAG-TEST-03)** — Single fixture at `tests/fixtures/golden-set-v1.json` (per Pass 1 Q-P1-08). Each entry: `(agent_name, jurisdictions, hazard_type, query_text, expected_chunk_ids, expected_jurisdiction_filters, tags[])`. The `tags[]` field MUST support `agency_disambiguation` for the SC-013 subset (≥20 of 50 entries). Per-PR trigger.
- **F-A10.4 — Blue-green E2E (FR-RAG-TEST-04)** — New file `tests/e2e/test_blue_green_alias_flip.py`; runs against staging Azure AI Search using ephemeral `corpus-test-*` index names. Asserts: (a) alias flip <60s, (b) post-flip retrieval resolves to new index, (c) previous index accessible 7 days, (d) rollback flips back. Triggers: scheduled nightly (mirrors FR-RAG-IDX-05a 1 AM AU-Eastern cadence) + pre-release stage of spec-029.
- **F-A10.5 — Test-strategy doc** — Author `docs/testing/spec-036-test-strategy.md` documenting the unit/contract/integration/e2e split with `@pytest.mark.unit|integration|contract|e2e` markers (closes F-DEL-07 finding).

### F-A11 — Observability (Cluster A11)
*Anchored by R3 architecture memo F-ARCH-15 OTel + delivery memo F-DEL-06 OTel-in-foundry-seam findings; Pass 2 Q-P2-05 emission transport.*

- **F-A11.1 — FR-RAG-OBS-01 retrieval metrics** — Wrap `RetrievalService.retrieve()` in `apps/agents/common/retrieval_service.py` in a dedicated OTel span emitting `retrieval_latency_ms` (histogram, p50/p95/p99), `retrieval_chunk_count` (histogram), `retrieval_error_rate` (counter). Tags: `agent_name`, `jurisdiction`, `hazard_type`. Transport: **existing OTel-to-App-Insights bridge per spec 014 FR-016** (per Pass 2 Q-P2-05) — direct App-Insights SDK calls forbidden in production paths.
- **F-A11.2 — Foundry inference span** — Wrap the Foundry inference call in a **separate** OTel span emitting `foundry_inference_latency_ms` so retrieval-only (Pass 1 Q-P1-06) and end-to-end (SC-012) SLOs are independently observable. Both spans share the same `correlation_id` for trace stitching (closes F-ARCH-15 + F-DEL-06).
- **F-A11.3 — FR-RAG-OBS-02 ingest metrics** — `apps/ingest-runner/src/ama_ingest/__main__.py` emits `ingest_duration_seconds` (gauge), `chunks_processed` (counter), `embedding_calls` (counter), `ingest_errors` (counter). Author Grafana dashboard `infra/dashboards/foundry-rag-ingest.json`.
- **F-A11.4 — FR-RAG-OBS-03 latency alert** — Alert if **retrieval-only** p95 >500ms for >5 min (degraded performance; not a hard failure). Foundry inference governed independently by SC-012. Both reported as separate App Insights metrics.
- **F-A11.5 — SC dashboard** — Author `infra/bicep/modules/foundry-rag-success-criteria-dashboard.bicep` with Application Insights workbook tiles for SC-001..SC-019 (closes F-QA-03).

### F-A12 — Accessibility (Cluster A12)
*Anchored by R3 delivery memo F-DEL-05 CitationCard accessibility finding; FR-RAG-UI-01 SHOULD-class WCAG 2.2 AA.*

- **F-A12.1 — `<CitationCard />` keyboard accessibility (closes F-DEL-05)** — Wrap collapsible header in `<button>` element with `onClick`, `aria-expanded`, `aria-controls`. Visible focus ring (`focus-visible:ring-2`). Add Testing-Library tests at `tests/web/src/components/citation/citation-card.test.tsx` asserting (1) button in tab order, (2) Enter toggles, (3) Space toggles.
- **F-A12.2 — `aria-label` for citations** — `aria-label="Cite: <jurisdiction>/<topic>/handbook.md#page-N"` on each citation row.
- **F-A12.3 — Screen-reader announcement** — On grounded recommendation render, fire `aria-live="polite"` announcement: "Grounded recommendation with N citations".
- **F-A12.4 — Automated accessibility lint** — Add `jest-axe` (preferred) OR `pa11y` to the existing UI-test pipeline; gate at CI as a SHOULD (warn-only initially). Trigger: per-PR.
- **F-A12.5 — SHOULD scope** — FR-RAG-UI-01 is SHOULD, not MUST; not blocking Step 9 acceptance per persona memo guidance.

### Phase F ordering vs existing tasks T142–T150

Existing `tasks.md` numbers run to **T150** (Phase E close, 2026-05-08). Phase F sub-phases land **after** T150 in the dependency-ordered task graph. Recommended task-numbering convention for Phase F (to be generated by `/speckit.tasks`):

| Sub-phase | Task range (recommended) | Predecessors | Notes |
|---|---|---|---|
| F-A4 (rego bug-fix) | T151–T155 | T150 | **First** in Phase F because it is a single-PR bug-fix coupled with the amend-loop merge per Pass 2 Q-P2-03. |
| F-A1 (agency disambiguation) + F-A3 (precedence ranking) | T156–T170 | T155, T040 (B-phase blue-green wrapper) | Co-scheduled — share the same blue-green rebuild pass. |
| F-A2 (cultural authority) | T171–T180 | T170, T085 (D-phase RAG-OPTOUT lint pattern) | Provision empty container + plumbing only — body authoring + sign-off is HUMAN-IN-LOOP per Assumption A9. |
| F-A5 (audit shape) + F-A7 (blue-green replay) | T181–T192 | T082 (existing audit-migration script), T040 | F-A5.1 audit-shape and F-A7.2 `retrieval_index_name` are co-emitted. |
| F-A6 (federal compliance) | T193–T200 | T180, T192 | HUMAN-IN-LOOP federal sign-off gates F-A6.5; codebase-side scaffolding is in scope. |
| F-A8 (corpus freshness) + F-A10 (test coverage) | T201–T215 | T192 | F-A10.4 blue-green E2E depends on F-A7 atomicity; F-A8.1 nightly schedule depends on existing `corpus-ingest.yml`. |
| F-A9 (conflict detection) | T216–T222 | T192 (audit shape) | `conflict_group_id` written to AuditRecord (F-A5.1) is the trace-stitching anchor. |
| F-A11 (observability) | T223–T230 | T192 | OTel spans wrap pre-existing call sites; ordering matters only relative to F-A5 (so spans can include `retrieval_index_name` attribute). |
| F-A12 (accessibility) | T231–T235 | T223 | Last because UI components consume metrics + audit fields landed earlier. |

**No re-ordering of T001–T150 is required.** All Phase F tasks are appended.

---

## Risk Register Additions (R3 amend-loop)

The original 13-row Risk Register (R1–R13) covers the Phase A–E surface. The amend loop adds 5 new risks (R14–R18) plus refines 2 prior risks (R-update notes added to R7 + R13). Severity uses the same L × I × {L|M|H|Critical} scale.

| # | Risk | L × I | Mitigation | Anchored by | Owner |
|---|---|---|---|---|---|
| **R14** | **Cultural-authority registry partial population at go-live** — registry container provisioned but corpus body authoring (Indigenous-language translations, Sacred Site protocols) HUMAN-IN-LOOP per FR-RAG-CA-01..03 + A9; if go-live happens before sign-off, the gate fail-closes for all protected chunks. | M × H | F-A2.6 OPA-blocked flag-flip enforces Locked-on in prod; FR-RAG-CA-05 + SC-014 governance gate; CD verifies sign-offs at deploy time; Constitution Principle I no-silencing preserved (non-protected chunks still retrievable). | R3 sectors-territories memo + R3 sectors-commonwealth memo §A2; Constitution VI-C; OOS-8 | HUMAN-IN-LOOP NEMA + AFAC + Indigenous community owners |
| **R15** | **Federal compliance attestation slipped past go-live** — Privacy Act + ISM 2024 + PSPF sign-off requires NEMA + AGD + AFP HUMAN-IN-LOOP; mis-sequencing means CD lands the implementation before attestation lands. | M × Critical | F-A6.5 explicit HUMAN-IN-LOOP gate; A9 documented; tasks.md Phase F-A6 carries sign-off acquisition tasks; CD blocking pre-prod release until ISM-2024-mapping.md + PSPF audit endpoint verifications pass. | R3 sectors-commonwealth memo §A6; Constitution NN-3 Privacy Act; A9 | Compliance Auditor + HUMAN-IN-LOOP federal owners |
| **R16** | **Multi-agent conflict false positives** — reactive, rule-based detector may flag legitimate parallel recommendations as conflicts (e.g., Risk Assessment + Monitoring both flag a hazard with severity-delta=1 by design). | M × M | F-A9.6 Reversible flag (one-click disable falls back to single-agent behaviour); ADR-18 four-class taxonomy is deterministic and pre-agreed; SRE runbook + Ops Officer dual-track resolution; SRE F-SRE-02 false-positive characterisation deferred to post-launch metric review. | R3 quality memo F-SRE-02; ADR-18; Pass 1 Q-P1-03 | Software Developer + Ops Officer persona owner |
| **R17** | **OTel-to-App-Insights bridge failure mode under canary load** — per Pass 2 Q-P2-05 the existing OTel pipeline is the binding emission path; if the bridge degrades during the per-agent canary, retrieval + foundry latency become unobservable AND the SC-012 30%-end-to-end gate cannot be diagnosed. | M × M | F-A11.1/.2 dual-span wiring; existing no-op fallback in spec-014 OTel pipeline ensures spans degrade gracefully (no production impact); SRE alert on OTel exporter queue depth >threshold; existing `apps/agents/common/lifecycle/heartbeat.py` + `pybreaker_adapter.py` precedents. | R3 architecture memo F-ARCH-15 + delivery memo F-DEL-06; Pass 2 Q-P2-05 | DevOps + SRE |
| **R18** | **Schema-on-read tolerance leaks legacy nullable fields into ranking pipeline** — Cosmos additive-nullable migration (Pass 2 Q-P2-01) means legacy `AuditRecord` rows have `null` for `retrieval_index_name`, `precedence_tiebreak_applied`, etc.; if ranking or replay code paths assume non-null, replay can fail in production. | L × H | F-A5.1 schema (`audit-record-llm-call.json`) marks every amend-loop field nullable explicitly; type-check seam (Protocol/runtime) accepts None; replay code path tested with legacy + post-migration fixtures (golden-set tagged `legacy_pre_amend`); PR review checklist for null-safety on every amend-loop field consumer. | R3 architecture memo F-ARCH-14; Pass 2 Q-P2-01; A10 | Principal Engineer + Data Engineer |

**R-updates** (deltas to existing risks, NOT replacements):

- **R7 (alias flip cutover timeout)** — gains F-A7.3 explicit 5-minute SLO timer-start condition (Service Bus `index_rollback` event emission per Pass 1 Q-P1-04), F-A7.4 manual-not-automatic Release Manager gate, and Manual operator action class flag taxonomy (Pass 2 Q-P2-08).
- **R13 (citation rendering accessibility regression)** — gains F-A12.1..5 concrete remediation actions for the F-DEL-05 keyboard-focus-trap finding; jest-axe / pa11y CI integration is the binding gate.

---

## Rollback-Class Taxonomy (Pass 2 Q-P2-08)

All amend-loop feature flags follow the **spec-029 progressive-delivery flag pattern** (FR-008 5-minute rollback via flag flip). Flags partition into three reversibility classes:

| Class | FRs | Flag (`feature.*`) | Disable behaviour | Reversibility | Audit emission on flip |
|---|---|---|---|---|---|
| **Locked-on** | FR-RAG-CA-04 (cultural-authority gate); FR-RAG-AG-02 (audit fields once written) | `cultural_authority_gate.enabled` (defaults `true`; flag exists only for `environment=test` chaos runs) | n/a in prod — disabling violates Constitution VI-C and is **policy-blocked by OPA at flag-flip time** (the OPA bug-fix in F-A4 is a prerequisite) | One-way; only re-enable is permitted in prod | `cultural_authority_gate_test_disable_attempt` (denied by OPA) |
| **Reversible (≤5-min flag flip)** | FR-RAG-COORD-01/02 (conflict detection); FR-RAG-AG-04 precedence ranking; FR-RAG-FRESH-02 staleness alert | `multi_agent_conflict_detection.enabled`; `authority_precedence_ranking.enabled`; `corpus_freshness_alert.enabled` | Disabled → agents revert to single-agent behaviour / SHA-recency-only ranking / suppressed alert; underlying state still recorded in audit log; **never silences the agent** (Constitution Principle I) | Reversible mid-incident per spec 029 FR-008 5-min SLO | `<feature>_disabled` audit event with `flag_name`, `old_value`, `new_value`, `actor_id`, `change_reason` |
| **Manual operator action (not flag-driven)** | FR-RAG-IDX-09 alias-flip rollback | n/a — alias re-flip is the rollback mechanism itself | Release Manager re-flips alias to old index; 5-min SLO timer per Pass 1 Q-P1-04 (timer starts at `index_rollback` Service Bus event emission) | Reversible (alias-flip path) | `index_rollback` Service Bus event + audit append `{old_index_name, new_index_name, parity_gate_failure_reason, release_manager_id, completed_at}` |

Every flag flip MUST emit `audit.feature_flag_change` carrying `{flag_name, old_value, new_value, actor_id, change_reason}` (Constitution Principle IV full provenance). **No flag flip MAY silence an agent** (Constitution Principle I) — disabling a coordination flag falls back to single-agent behaviour, never to a no-op.

---

## HUMAN-IN-LOOP Escalation Paths (Pass 2 Q-P2-07)

The amend loop introduces three classes of work that the codebase scaffolds but does NOT autonomously complete. Plan-phase deliverables provide the seam; implement-phase tasks track sign-off acquisition; execution is external.

| Path | What the codebase does | What HUMAN-IN-LOOP owns | Anchored by |
|---|---|---|---|
| **Cultural-authority corpus body** | Indigenous-language corpus structure + signature gating (`culturalAuthorityRegistry` Cosmos container) + retrieval-side fail-closed gate + audit-event surface | Translation authoring (Arrernte, Tiwi, Warlpiri, Pitjantjatjara, Torres Strait Islander) + Sacred Site protocols + ALT/APY consent + AIATSIS Ethics Committee sign-off | FR-RAG-CA-01..05; OOS-8; A9; ADR-12 |
| **Federal compliance attestation** | Privacy Act 1988 APP 1/3/5/6/11 surfaces (privacy policy + SAR endpoint + PII anonymisation hook + 7-yr retention); ISM-2024-mapping.md scaffold; PSPF audit-export endpoint; COMDISPLAN ranking interlock | NEMA + AGD + AFP federal sign-off on the compliance attestations + production go-live authorisation | FR-RAG-COMP-01..04; A9; ADR-15 |
| **Cultural-authority registry population** | Cosmos container provisioned empty + signature-verifier ready | NEMA + AFAC + ≥3 Indigenous community representatives sign-off + initial row population + revocation workflow ownership | FR-RAG-CA-05; SC-014; A9 |

**Plan-phase deferral pattern** (Pass 2 Q-P2-07 + A11):
- `[NEEDS ADR]` markers in spec.md = **`/speckit.specify`-phase** deliverable (already landed).
- ADR stub files at `docs/decisions/036-foundry-rag-grounding/12-...md` through `19-...md` = **`/speckit.plan`-phase** deliverable (landed by this amend-loop run).
- ADR body authoring + HUMAN-IN-LOOP sign-off = **`/speckit.implement`-phase** deliverable (paralleling Phase E ADR-authoring tasks T118–T126).

---

## Tech-stack Additions (R3 amend-loop)

The amend loop adds **3 new dependencies** to the existing stack (no new Azure services). All additions are additive over the Phase A–E baseline.

| Dependency | Purpose | Where landed | Anchored by |
|---|---|---|---|
| `opentelemetry-sdk` + `opentelemetry-instrumentation-azure-search-documents` (Python) + `opentelemetry-exporter-azure-monitor` (Python) | Required by F-A11.1/.2 to wrap `RetrievalService.retrieve()` and the Foundry inference call in dedicated OTel spans exported to Application Insights via the existing OTel-to-App-Insights bridge per spec 014 FR-016. **Direct App Insights SDK calls remain forbidden in production paths.** | `apps/agents/common/retrieval_service.py`, `apps/agents/common/foundry_chat_client.py`, `apps/agents/maf_runtime/middleware/otel_middleware.py` | F-A11; Pass 2 Q-P2-05; F-ARCH-15 + F-DEL-06 R3 findings |
| `jest-axe` (Node, preferred) **OR** `pa11y` (Node, alt) | Required by F-A12.4 to lint WCAG 2.2 AA on `<CitationCard />` + recommendation card in CI. `jest-axe` integrates cleanly with the existing Testing-Library pipeline; `pa11y` is the alternative if jest-axe coverage is insufficient. SHOULD-class gate (warn-only initially). | `apps/web/__tests__/`, `packages/ui/__tests__/` | F-A12; FR-RAG-UI-01; F-DEL-05 R3 finding |
| `psutil` (Python) | Required by F-A10.2 50-agent Locust harness to probe per-process memory + CPU during the 60-second sustained-load test (validates SC-012 + the SHOULD-class p95 ≤500ms gate without false positives from CI-runner contention). | `tests/load/locustfile.py`, `tests/load/test_workflow_capacity.py`, `tests/load/baselines/` | F-A10; FR-RAG-TEST-02; F-PERF-02 R3 finding |

**No new Azure service families.** `culturalAuthorityRegistry` and `conflictDetectionLog` are net-new Cosmos DB **containers** within the existing Cosmos account — same SKU, same region, same private-endpoint envelope. All other amend-loop changes are within the existing Container Apps + AI Search + Foundry envelope.

---

## Cross-cluster dependencies

Several amend-loop clusters share data structures or sequencing constraints. The matrix below documents the dependencies so `/speckit.tasks` orders T151–T235 correctly.

| From cluster | To cluster | Dependency | Why |
|---|---|---|---|
| **A2** (cultural authority) | **A5** (audit shape) | A5 audit field `cultural_authority_check_result` carries the gate decision for replay | Pass 2 Q-P2-02 gate emits its decision into the existing `retrieved_chunks[]` audit shape; needs ADR-14 audit extension landed first |
| **A1+A3** (agency + precedence) | **A5** (audit shape) | A5 audit field `precedence_tiebreak_applied[]` carries the tie-break trace per Pass 1 Q-P1-02 | SC-011 ≥95% byte-identical replay holds even when ranks tie |
| **A4** (rego bug-fix) | **All amend-loop merges** | F-A4.2 sequencing — coupled with amend-loop merge in same PR | Splitting it across PRs creates a window where prod could deploy a 2-approver carve-out (Pass 2 Q-P2-03) |
| **A7** (blue-green atomicity) | **A1+A3** (agency + precedence) | A1+A3 chunk-schema extensions land via blue-green rebuild per Pass 2 Q-P2-01; A7 atomicity protocol must be in place before the rebuild | A1+A3 are required Chunk fields; in-place mutation forbidden per A10 |
| **A5** (audit shape) | **A7** (blue-green replay) | A5 `retrieval_index_name` field is what A7 audit replay pins to | Field added in F-A5.1 → emitted in F-A5.3 → consumed by F-A7.1 retrieval client |
| **A5** (audit shape) | **A9** (conflict detection) | A9 `conflict_group_id` is added to AuditRecord in F-A5.1 | A9 detector emits `conflict_group_id` to the same field for trace stitching |
| **A6** (federal compliance) | **A3** (precedence ranking) | F-A6.4 wires COMDISPLAN activation interlock via the F-A3 precedence-ranking mechanism | Single mechanism, two consumers |
| **A11** (observability) | **A5** + **A7** | OTel spans include `retrieval_index_name` (A5+A7) as a span attribute | Span attribute key matches audit field name |
| **A10.4** (blue-green E2E) | **A7** (in-flight atomicity) | E2E test asserts the F-A7.1 query-pinning protocol holds across alias flips | Test cannot be authored until atomicity protocol is in place |

---

## Updated phase ordering relative to existing Phases A–E

The amend loop does NOT re-order Phases A–E. It appends Phase F as a single block landing **after T150**. Within Phase F, the cluster ordering is documented in [§Phase F ordering vs existing tasks T142–T150](#phase-f-ordering-vs-existing-tasks-t142-t150) above.

**Single-PR coupling constraint** (per Pass 2 Q-P2-03): F-A4 (rego bug-fix) MUST land in the same PR as the broader amend-loop merge — splitting it creates a deployment window where prod could deploy a 2-approver carve-out (the very gap FR-RAG-CV-01 closes). All other Phase F sub-phases MAY land in subsequent PRs in dependency-order.

---

## Cross-references — Phase F appendix

- **Spec amend-loop sessions**: [`spec.md`](./spec.md) Sessions 3–5 (R3 review + Pass 1 + Pass 2; 16 Q&A resolutions; 25 new FRs + 12 amendments).
- **R3 review memos** (planning input): `personas-input/r3-operational.md`, `r3-sectors-{commonwealth,crosssector,eastern,southern-western,territories}.md`, `r3-technical-{architecture,delivery,quality}.md`, `r3-triage.md`.
- **R3 amend-loop ADR stubs** (created by `/speckit.plan`): `docs/decisions/036-foundry-rag-grounding/12-cultural-authority-gating.md` through `19-test-coverage-windows.md` (8 stubs; body authored in `/speckit.implement`).
- **Amend-loop contracts** (created/extended by this run): `contracts/cultural-authority-registry.schema.json`, `contracts/conflict_detection.schema.json`, `contracts/foundry-cv.schema.json`, `contracts/staleness_alert.schema.json`, `contracts/chunk-metadata.schema.json` (all NEW); `contracts/audit-record-llm-call.json` (EXTENDED).
- **Data-model amend-loop additions**: [`data-model.md` §R3 Amend-Loop Additions](./data-model.md#r3-amend-loop-additions).
- **Research amend-loop ADRs**: [`research.md` §R-17..R-24](./research.md).
- **Quickstart amend-loop steps**: [`quickstart.md` §12..§15](./quickstart.md).

*End of Phase F appendix.*
