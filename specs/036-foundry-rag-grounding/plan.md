# Implementation Plan: Microsoft Foundry-Based RAG Grounding for All Agents and Simulation Chat

**Branch**: `036-foundry-rag-grounding` | **Date**: 2026-05-08 | **Spec**: [`spec.md`](./spec.md)
**Input**: Feature specification from `specs/036-foundry-rag-grounding/spec.md`
**Status**: Draft (Phase 0 + Phase 1 complete; ready for `/speckit.tasks`)

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

- **Spec**: [`spec.md`](./spec.md) (43 FRs, 8 USs, 12 SCs, 7 OOS, 8 assumptions; Pass-1 + Pass-2 clarifications complete).
- **Checklists**: [`checklists/requirements.md`](./checklists/requirements.md), [`checklists/migration.md`](./checklists/migration.md), [`checklists/compliance.md`](./checklists/compliance.md).
- **Phase 0 research**: [`research.md`](./research.md).
- **Phase 1 design**: [`data-model.md`](./data-model.md), [`contracts/`](./contracts/), [`quickstart.md`](./quickstart.md).
- **Constitution**: [`.specify/memory/constitution.md`](../../.specify/memory/constitution.md) — Principle I, IV, V, VI-C, NN-1, NN-2 (Amendment 1.2.0), Quality Gates.
- **Predecessor specs**: [014 Azure OpenAI Integration](../014-azure-openai-integration/spec.md) (migrated), [024 Simulation Control & Chat Orchestration](../024-simulation-control-chat/spec.md) (extended), [029 Progressive Delivery Pipeline](../029-progressive-delivery-pipeline/spec.md) (FF mechanism reused), [030 LLM Eval Framework](../030-llm-eval-framework/spec.md) (eval-runner pattern referenced), [032 Rubric Improvements](../032-rubric-improvements/spec.md) (FR-AI03a registry + FR-AI06 PE + FR-AI09 cosign reused), [033 MAF Adoption](../033-maf-adoption/spec.md) (FR-023 equivalence + FR-012b cutover gate referenced).
- **Persona memos** (R2 technical, primary planning input): `personas-input/technical-architecture.md`, `personas-input/technical-delivery.md`, `personas-input/technical-quality.md`. R1 sector + operational memos consulted: `personas-input/operational.md`, `personas-input/sectors-{commonwealth,crosssector,eastern,southern-western,territories}.md`.
- **Existing infrastructure reused** (no replacement, only additive deltas): `infra/modules/ai-search.bicep`, `infra/bicep/modules/eval/foundry-deployments.bicep`, `infra/parameters/foundry-carveout.{yaml,schema.json}`, `apps/eval-runner/src/ama_eval/foundry_client.py`, `scripts/verify-carveout.ps1`, `.github/workflows/ci.yml`, `.github/workflows/cd.yml`, `.github/workflows/foundry-carveout-review.yml`.

---

*End of plan.md — proceed to `/speckit.tasks` for the dependency-ordered task breakdown.*
